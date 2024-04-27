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
from flask import Flask, jsonify, request
from flask_restx import Api, Resource, fields, reqparse
# Torob crawler
import settings as torob_settings, pipelines, middlewares
from pipelines import DatabaseProduct, DatabaseSeller, DatabaseProductSellerDetails
from spiders import TorobSpider
# Log
from twisted.python import log
# Database
import psycopg2

crochet.setup()  # setting up crochet to execute
# CRAWL_RUNNER = CrawlerRunner(get_project_settings())  # initialize CrawlerRunner

# Configur logging
configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})

con = psycopg2.connect(
    host='localhost',
    user='postgres',
    password='docker',
    database='crawler_db'
)

cursor = con.cursor()

# app , api
app = Flask(__name__)
api = Api(app)


# Fetch all products endpoint
def fetch_all_products(page=1, per_page=10):
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
                                  created_on=row[9]
                                  )
        products.append(product)
    return products


# Fetch all sellers
def fetch_all_sellers(page=1, per_page=10, search_name=None):
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


# Fetch all product seller details
def fetch_all_product_seller_details(product_id, page=1, per_page=10):
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


# Request body
crawl_request_body = api.model('CrawlRequest', {
    'url': fields.String(required=True, description='The URL to crawl')
})


class CrawlTorob(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    @api.expect(crawl_request_body)
    def post(self):
        try:
            data = request.get_json()
            base_url = data.get('url')

            if base_url:
                # Start the crawl
                self.crawl_torob_with_crochet(base_url)

                while not self.crawl_complete:
                    print("********************** Crawling1 ... **********************")
                    time.sleep(5)
                    if self.crawl_complete:
                        break

                return 'Crawling operation finished.', 200
            else:
                return 'URL parameter is missing.', 400
        except Exception as e:
            print("An error occurred in crawl endpoint:", e)

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


# Crawl endpoint
api.add_resource(CrawlTorob, "/crawl-torob")

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


# Test api endpoint
@api.route('/test')
class Test(Resource):
    @staticmethod
    def get():
        return {'Test': 'Success'}


# Products endpoint
@api.route("/products")
class Products(Resource):
    @api.expect(product_parser)
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
    def get(self):
        args = product_seller_details_parser.parse_args()
        product_id = args['productId']
        page = args['page']
        per_page = args['per_page']
        product_seller_details = fetch_all_product_seller_details(product_id, page, per_page)
        print("********************** product seller details items count :", len(product_seller_details))
        return jsonify([psd.to_json() for psd in product_seller_details])


if __name__ == '__main__':
    app.run(debug=True)
