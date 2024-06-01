import crochet
import time
import scrapy
import sys
# Scrapy
from scrapy import signals
from scrapy.signalmanager import dispatcher
from scrapy.crawler import Crawler, CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
# Flask
from flask import Flask, jsonify, request, abort, current_app
from flask_restx import Api, Resource, fields, reqparse
# Torob crawler
import settings as torob_settings, pipelines, middlewares
from pipelines import DatabaseProduct, DatabaseSeller, DatabaseProductSellerDetails, StructuredProductDto
from spiders import TorobSpider
# Log
from twisted.python import log
# Database
import psycopg2
# Datetime
from datetime import datetime, timedelta
# SQL Alchemy
from flask_sqlalchemy import SQLAlchemy
# Func tools
from functools import wraps
# JWT
import jwt
# OS
import os

# setting up crochet to execute
crochet.setup()

# Configur logging
configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})

# Searching database connection
con = psycopg2.connect(
    host='postgresDb',
    user='docker',
    password='docker',
    database='crawler_db'
)

# Cursor to execute sql commands
cursor = con.cursor()

# app , api
app = Flask(__name__)
# Flask database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://docker:docker@postgresDb/crawler_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is our little secret'
print("********************** Secret Key :", SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY

# Swagger UI JWT token configuration
authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT authorization using the Bearer scheme. Example: "Bearer {token}"'
    }
}

# Initialize API with authorization configuration
api = Api(app, authorizations=authorizations, security='Bearer Auth')

# Db
db = SQLAlchemy(app)


# User model
class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def save_to_db(self):
        print("********************** Inserting into database ...")
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, user_id):
        return cls.query.filter_by(id=user_id).first()


# Create tables
@app.before_request
def create_tables():
    # The following line will remove this handler, making it
    # only run on the first request
    print("********************** Creating tables ...")
    app.before_request_funcs[None].remove(create_tables)

    db.create_all()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        try:
            if "Authorization" in request.headers:
                token = request.headers["Authorization"].split(" ")[1]
        except Exception as e:
            return {
                "message": "Pass the token correctly",
                "data": None,
                "error": "Use the correct schema (Bearer {token})"
            }, 400
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        try:
            data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = UserModel.find_by_id(data["user_id"])
            if current_user is None:
                return {
                    "message": "Invalid Authentication token!",
                    "data": None,
                    "error": "Unauthorized"
                }, 401
            # If 'active' is a column in UserModel, ensure it is checked properly
            if not getattr(current_user, 'active', True):  # Default to True if 'active' is not defined
                abort(403)
        except Exception as e:
            return {
                "message": "Something went wrong",
                "data": None,
                "error": str(e)
            }, 500

        return f(*args, **kwargs)

    return decorated


# Fetch all products endpoint
def fetch_all_products(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        cursor.execute("SELECT * FROM products ORDER BY created_on DESC LIMIT %s OFFSET %s", (per_page, offset))
        result_products = cursor.fetchall()
        products = []
        for row in result_products:
            product = DatabaseProduct(id=row[0],
                                      image_url=row[1],
                                      name1=row[2],
                                      name2=row[3],
                                      more_info_url=row[4],
                                      price=row[5],
                                      price_text=row[6],
                                      shop_text=row[7],
                                      is_stock=row[8],
                                      created_on=row[11]
                                      )
            products.append(product)
        return products
    except psycopg2.Error as e:
        print(f"Database error occurred: {e}")
        con.rollback()
        return []


# Fetch all sellers
def fetch_all_sellers(page=1, per_page=10, search_name=None):
    try:
        offset = (page - 1) * per_page
        if search_name:
            cursor.execute("SELECT * FROM sellers WHERE name LIKE %s ORDER BY created_on DESC LIMIT %s OFFSET %s",
                           ('%' + search_name + '%', per_page, offset))
        else:
            cursor.execute("SELECT * FROM sellers ORDER BY created_on DESC LIMIT %s OFFSET %s", (per_page, offset))
        result_sellers = cursor.fetchall()
        sellers = []
        for row in result_sellers:
            seller = DatabaseSeller(id=row[0],
                                    name=row[1],
                                    city=row[2],
                                    is_flagged=row[3],
                                    created_on=row[4]
                                    )
            sellers.append(seller)
        return sellers
    except psycopg2.Error as e:
        print(f"Database error occurred: {e}")
        con.rollback()
        return []


# Fetch all product seller details
def fetch_all_product_seller_details(product_id, page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        cursor.execute(
            "SELECT * FROM product_seller_details WHERE product_id = %s ORDER BY created_on DESC LIMIT %s OFFSET %s",
            (product_id, per_page, offset))
        result_product_seller_details = cursor.fetchall()
        product_seller_details_list = []
        for row in result_product_seller_details:
            product_seller_details = DatabaseProductSellerDetails(id=row[0],
                                                                  name1=row[1],
                                                                  name2=row[2],
                                                                  shop_name=row[3],
                                                                  shop_city=row[4],
                                                                  price=row[5],
                                                                  price_text=row[6],
                                                                  last_price_change_date=row[7],
                                                                  page_url=row[8],
                                                                  is_stock=row[9],
                                                                  created_on=row[10],
                                                                  seller_id=row[11],
                                                                  product_id=row[12],
                                                                  )
            product_seller_details_list.append(product_seller_details)
        return product_seller_details_list
    except psycopg2.Error as e:
        print(f"Database error occurred: {e}")
        con.rollback()
        return []


def fetch_structured_products_with_search(page=1, per_page=10, search_name=""):
    try:
        offset = (page - 1) * per_page
        if search_name is not None:
            # Use LIKE operator to perform partial string matching
            search_condition = "AND (P.name1 LIKE %s OR S.name LIKE %s OR S.city LIKE %s)"
            search_values = ('%' + search_name + '%', '%' + search_name + '%', '%' + search_name + '%')
        else:
            search_condition = ""
            search_values = ()
        query = """SELECT P.name1, P.name2, P.category_name,
                         P.brand_name, PSD.price, PSD.price_text,
                         PSD.created_on, PSD.is_stock, PSD.id, S.name, S.city, P.image_url
                         FROM public.product_seller_details PSD
                         INNER JOIN public.products P ON P.id = PSD.product_id
                         INNER JOIN public.sellers S ON S.id = PSD.seller_id
                         WHERE 1=1 {search_condition}
                         ORDER BY PSD.created_on DESC
                         LIMIT %s OFFSET %s""".format(search_condition=search_condition)

        cursor.execute(query, search_values + (per_page, offset))
        result_structured_data = cursor.fetchall()
        structured_products = []

        for row in result_structured_data:
            structured_product = StructuredProductDto(name1=row[0],
                                                      name2=row[1],
                                                      category_name=row[2],
                                                      brand_name=row[3],
                                                      price=row[4],
                                                      price_text=row[5],
                                                      created_on=row[6],
                                                      is_stock=row[7],
                                                      psd_id=row[8],
                                                      seller_name=row[9],
                                                      seller_city=row[10],
                                                      image_url=row[11])
            structured_products.append(structured_product)
        return structured_products
    except psycopg2.Error as e:
        print(f"Database error occurred: {e}")
        con.rollback()
        return []


# Request body
crawl_request_body = api.model('CrawlRequest', {
    'url': fields.String(required=True, description='The URL to crawl')
})


@api.route("/crawl-torob")
class CrawlTorob(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self, base_url):
        try:
            # Initialize the crawler object
            print("********************** crochet ... **********************")
            self.crawler = Crawler(TorobSpider.TorobSpider, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl(url=base_url)
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @api.expect(crawl_request_body)
    @token_required
    def post(self):
        try:
            data = request.get_json()
            base_url = data.get('url')

            if base_url:
                # Start the crawl
                self.crawl_torob_with_crochet(base_url)

                while not self.crawl_complete:
                    print("********************** Crawling ... **********************")
                    time.sleep(5)
                    if self.crawl_complete:
                        break

                return 'Crawling operation finished.', 200
            else:
                return 'URL parameter is missing.', 400
        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


# Define a parser for the product required parameter
product_seller_details_parser = reqparse.RequestParser()
product_seller_details_parser.add_argument('productId', type=str, required=True, help='The ID of the product')
product_seller_details_parser.add_argument('page', type=int, required=False, default=1, help='The page number')
product_seller_details_parser.add_argument('per_page', type=int, required=False, default=10, help='Items per page')

# Define a parser for the product seller details required parameter
product_parser = reqparse.RequestParser()
product_parser.add_argument('page', type=int, required=False, default=1, help='The page number')
product_parser.add_argument('per_page', type=int, required=False, default=10, help='Items per page')

# Define a parser for the product seller details required parameter
seller_parser = reqparse.RequestParser()
seller_parser.add_argument('page', type=int, required=False, default=1, help='The page number')
seller_parser.add_argument('per_page', type=int, required=False, default=10, help='Items per page')
seller_parser.add_argument('search_name', type=str, required=False, help='search name')

# Define a parser for the structured product data required parameter
structured_product_data_parser = reqparse.RequestParser()
structured_product_data_parser.add_argument('page', type=int, required=False, default=1, help='The page number')
structured_product_data_parser.add_argument('per_page', type=int, required=False, default=10, help='Items per page')
structured_product_data_parser.add_argument('search_name', type=str, required=False, help='search name')

# Define a parser for the user required parameter
user_model = api.model('User', {
    'username': fields.String(description='The username', required=True),
    'password': fields.String(description='The password', required=True),
})

user_parser = reqparse.RequestParser()
user_parser.add_argument('user', type=dict, location='json', required=True)


# Test api endpoint
@api.route('/test')
class Test(Resource):
    @staticmethod
    def get():
        return {'Test': 'Success'}


@api.route("/structure_products")
class StructuredProducts(Resource):
    @api.expect(structured_product_data_parser)
    @token_required
    def get(self):
        args = structured_product_data_parser.parse_args()
        page = args['page']
        per_page = args['per_page']
        search_name = args['search_name']
        structured_products = fetch_structured_products_with_search(page, per_page, search_name)
        print("********************** Structured products items count :", len(structured_products))
        return jsonify([sp.to_json() for sp in structured_products])


# Products endpoint
@api.route("/products")
class Products(Resource):
    @api.expect(product_parser)
    @token_required
    def get(self):
        args = product_parser.parse_args()
        page = args['page']
        per_page = args['per_page']
        products = fetch_all_products(page, per_page)
        print("********************** Product items count :", len(products))
        return jsonify([p.to_json() for p in products])


# Sellers endpoint
@api.route("/sellers")
class Sellers(Resource):
    @api.expect(seller_parser)
    @token_required
    def get(self):
        args = seller_parser.parse_args()
        page = args['page']
        per_page = args['per_page']
        search_name = args['search_name']
        sellers = fetch_all_sellers(page, per_page, search_name)
        print("********************** Seller items count :", len(sellers))
        return jsonify([s.to_json() for s in sellers])


# Product seller details endpoint
@api.route("/product_seller_details")
class ProductSellerDetails(Resource):
    @api.expect(product_seller_details_parser)
    @token_required
    def get(self):
        args = product_seller_details_parser.parse_args()
        product_id = args['productId']
        page = args['page']
        per_page = args['per_page']
        product_seller_details = fetch_all_product_seller_details(product_id, page, per_page)
        print("********************** product seller details items count :", len(product_seller_details))
        return jsonify([psd.to_json() for psd in product_seller_details])


@api.route("/user_registration")
class UserRegistration(Resource):
    @api.expect(user_model)
    def post(self):
        # this will automatically parse the JSON body
        data = api.payload
        username = data.get('username')
        password = data.get('password')
        new_user = UserModel(
            username=username,
            password=password
        )
        try:
            if UserModel.find_by_username(data['username']):
                return {'message': 'User {} already exists'.format(data['username'])}, 200
            new_user.save_to_db()
            return {
                'message': 'User {} was created'.format(data['username'])
            }, 200
        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/user_login")
class UserLogin(Resource):
    @api.expect(user_model)
    def post(self):
        try:
            data = api.payload  # this will automatically parse the JSON body
            username = data.get('username')
            password = data.get('password')
            current_user = UserModel.find_by_username(username)
            if not current_user:
                return {'message': 'User {} doesn\'t exist'.format(username)}

            if password == current_user.password:
                try:
                    # token should expire after 24 hrs
                    token = jwt.encode(
                        {"user_id": current_user.id, "exp": datetime.now() + timedelta(hours=24)},
                        app.config["SECRET_KEY"],
                        algorithm="HS256"
                    )
                    return {
                        "message": "Successfully fetched auth token",
                        "data": {"token": token}
                    }
                except Exception as e:
                    return {
                        "error": "Something went wrong",
                        "message": str(e)
                    }, 500
            else:
                return {
                    "message": "Error fetching auth token!, invalid username or password",
                    "data": None,
                    "error": "Unauthorized"
                }, 404
        except Exception as e:
            return {
                "message": "Something went wrong!",
                "error": str(e),
                "data": None
            }, 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
