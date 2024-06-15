# OS
import os
import time
# Concurrent
import concurrent.futures
# Threading
import threading
# Datetime
from datetime import datetime, timedelta
# Func tools
from functools import wraps
# Crochet
import crochet
# JWT
import jwt
# Log
# Database
import psycopg2
# Flask
from flask import Flask, jsonify, request, abort, current_app
from flask_restx import Api, Resource, fields, reqparse
# SQL Alchemy
from flask_sqlalchemy import SQLAlchemy
# Scrapy
from scrapy import signals
from scrapy.crawler import Crawler
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
# Torob crawler
from pipelines import DatabaseProduct, DatabaseSeller, DatabaseProductSellerDetails, StructuredProductDto
from spiders import (TorobSpider_Phone,
                     TorobSpider_Tablet,
                     TorobSpider_Headphone,
                     TorobSpider_Charger,
                     TorobSpider_Cable,
                     TorobSpider_PhoneTabletHolder,
                     TorobSpider_MonoPod,
                     TorobSpider_PowerBank,
                     TorobSpider_SmartWatch,
                     TorobSpider_LaptopNotebook,
                     TorobSpider_Monitor,
                     TorobSpider_AllInOne,
                     TorobSpider_Desktop,
                     TorobSpider_MiniComputer,
                     TorobSpider_CPU,
                     TorobSpider_Motherboard,
                     TorobSpider_GraphicCard,
                     TorobSpider_ComputerRAM,
                     TorobSpider_LaptopRAM,
                     TorobSpider_ServerRAM,
                     TorobSpider_ComputerPower,
                     TorobSpider_ComputerSoundCard,
                     TorobSpider_Keyboard,
                     TorobSpider_Mouse,
                     TorobSpider_MouseAndKeyboard,
                     TorobSpider_ComputerCase,
                     TorobSpider_CaseFan,
                     TorobSpider_Hub,
                     TorobSpider_3DPrinterAndEssentials,
                     TorobSpider_AdslVdsl,
                     TorobSpider_Lte3G4G5G,
                     TorobSpider_FiberOpticModem,
                     TorobSpider_Router,
                     TorobSpider_AccessPoint,
                     TorobSpider_NetworkCard,
                     TorobSpider_Switch,
                     TorobSpider_NetworkCable,
                     TorobSpider_NetworkMemoryAndStorage,
                     TorobSpider_Server,
                     TorobSpider_ExternalHardDrive,
                     TorobSpider_InternalHardDrive,
                     TorobSpider_SSDHardDrive,
                     TorobSpider_ServerHardDrive,
                     TorobSpider_FlashMemory,
                     TorobSpider_MemoryCard,
                     TorobSpider_NetworkAndSecurityCamera,
                     TorobSpider_Recorder)

# setting up crochet to execute
crochet.setup()

# Configur logging
configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})

# Searching database connection
con = psycopg2.connect(
    host='postgresDb',
    user='postgres',
    password='docker',
    database='crawler_db'
)

# Cursor to execute sql commands
cursor = con.cursor()

# app , api
app = Flask(__name__)
# Flask database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:docker@postgresDb/crawler_db'
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


@api.route("/crawl-torob-all")
class CrawlTorobAll(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)
        self.spider_status = {}
        self.spider_counts = {}
        self.lock = threading.Lock()  # Correct use of Lock

    def crawler_result(self, item, response, spider):
        with self.lock:
            self.spider_counts[spider.name] += 1
            print(f"Item scraped by {spider.name}: {self.spider_counts[spider.name]}")

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self, spider_cls):
        try:
            print(f"********************** Starting crawl: {spider_cls.name} **********************")
            crawler = Crawler(spider_cls, get_project_settings())
            with self.lock:
                self.spider_counts[spider_cls.name] = 0
                self.spider_status[spider_cls.name] = False
            crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            crawler.crawl()
        except Exception as e:
            print(f"An error occurred in crawl_torob_with_crochet for {spider_cls.name}: {e}")

    def finished_crawling(self, spider, reason):
        print(f"********************** Finished crawling: {spider.name} **********************")
        with self.lock:
            self.spider_status[spider.name] = True

    @token_required
    def post(self):
        try:
            spiders_to_run = [
                TorobSpider_Phone.TorobSpider_Phone,
                TorobSpider_Tablet.TorobSpider_Tablet,
                TorobSpider_Headphone.TorobSpider_Headphone,
                TorobSpider_Charger.TorobSpider_Charger,
                TorobSpider_Cable.TorobSpider_Cable,
                TorobSpider_PhoneTabletHolder.TorobSpider_PhoneTabletHolder,
                TorobSpider_MonoPod.TorobSpider_MonoPod,
                TorobSpider_PowerBank.TorobSpider_PowerBank,
                TorobSpider_SmartWatch.TorobSpider_SmartWatch,
                TorobSpider_LaptopNotebook.TorobSpider_LaptopNotebook,
                TorobSpider_Monitor.TorobSpider_Monitor,
                TorobSpider_AllInOne.TorobSpider_AllInOne,
                TorobSpider_Desktop.TorobSpider_Desktop,
                TorobSpider_MiniComputer.TorobSpider_MiniComputer,
                TorobSpider_CPU.TorobSpider_CPU,
                TorobSpider_Motherboard.TorobSpider_Motherboard,
                TorobSpider_GraphicCard.TorobSpider_GraphicCard,
                TorobSpider_ComputerRAM.TorobSpider_ComputerRAM,
                TorobSpider_LaptopRAM.TorobSpider_LaptopRAM,
                TorobSpider_ServerRAM.TorobSpider_ServerRAM,
                TorobSpider_ComputerPower.TorobSpider_ComputerPower,
                TorobSpider_ComputerSoundCard.TorobSpider_ComputerSoundCard,
                TorobSpider_Keyboard.TorobSpider_Keyboard,
                TorobSpider_Mouse.TorobSpider_Mouse,
                TorobSpider_MouseAndKeyboard.TorobSpider_MouseAndKeyboard,
                TorobSpider_ComputerCase.TorobSpider_ComputerCase,
                TorobSpider_CaseFan.TorobSpider_CaseFan,
                TorobSpider_Hub.TorobSpider_Hub,
                TorobSpider_3DPrinterAndEssentials.TorobSpider_3DPrinterAndEssentials,
                TorobSpider_AdslVdsl.TorobSpider_AdslVdsl,
                TorobSpider_Lte3G4G5G.TorobSpider_Lte3G4G5G,
                TorobSpider_FiberOpticModem.TorobSpider_FiberOpticModem,
                TorobSpider_Router.TorobSpider_Router,
                TorobSpider_AccessPoint.TorobSpider_AccessPoint,
                TorobSpider_NetworkCard.TorobSpider_NetworkCard,
                TorobSpider_Switch.TorobSpider_Switch,
                TorobSpider_NetworkCable.TorobSpider_NetworkCable,
                TorobSpider_NetworkMemoryAndStorage.TorobSpider_NetworkMemoryAndStorage,
                TorobSpider_Server.TorobSpider_Server,
                TorobSpider_ExternalHardDrive.TorobSpider_ExternalHardDrive,
                TorobSpider_InternalHardDrive.TorobSpider_InternalHardDrive,
                TorobSpider_SSDHardDrive.TorobSpider_SSDHardDrive,
                TorobSpider_ServerHardDrive.TorobSpider_ServerHardDrive,
                TorobSpider_FlashMemory.TorobSpider_FlashMemory,
                TorobSpider_MemoryCard.TorobSpider_MemoryCard,
                TorobSpider_NetworkAndSecurityCamera.TorobSpider_NetworkAndSecurityCamera,
                TorobSpider_Recorder.TorobSpider_Recorder
            ]

            futures = []

            # Start the crawl for each spider in parallel
            for spider_cls in spiders_to_run:
                print(f"Submitting spider: {spider_cls.name}")
                futures.append(self.executor.submit(self.crawl_torob_with_crochet, spider_cls))

            while not all(self.spider_status.get(spider_cls.name, False) for spider_cls in spiders_to_run):
                print("********************** Crawling in progress ... **********************")
                time.sleep(5)

            results = {spider_cls.name: self.spider_counts.get(spider_cls.name, 0) for spider_cls in spiders_to_run}
            return jsonify({'message': 'Crawling operation finished.', 'results': results}), 200

        except Exception as e:
            print(f"An error occurred in post method: {e}")
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-phone")
class CrawlTorob_Phone(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-phone: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Phone.TorobSpider_Phone, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-phone: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-phone: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-phone: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-tablet")
class CrawlTorob_Tablet(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-tablet: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Tablet.TorobSpider_Tablet, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-tablet: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-tablet: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-tablet: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-headphone")
class CrawlTorob_Headphone(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-headphone: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Headphone.TorobSpider_Headphone, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-headphone: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-headphone: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-headphone: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-charger")
class CrawlTorob_Charger(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-charger: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Charger.TorobSpider_Charger, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-charger: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-charger: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-charger: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-cable")
class CrawlTorob_Charger(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-cable: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Cable.TorobSpider_Cable, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-cable: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-cable: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-cable: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-phonetabletholder")
class CrawlTorob_PhoneTabletHolder(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-phonetabletholder: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_PhoneTabletHolder.TorobSpider_PhoneTabletHolder, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-phonetabletholder: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-phonetabletholder: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-phonetabletholder: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-monopod")
class CrawlTorob_MonoPod(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-monopod: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_MonoPod.TorobSpider_MonoPod, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-monopod: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-monopod: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-monopod: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-powerbank")
class CrawlTorob_PowerBank(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-powerbank: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_PowerBank.TorobSpider_PowerBank, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-powerbank: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-powerbank: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-powerbank: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-smartwatch")
class CrawlTorob_SmartWatch(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-smartwatch: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_SmartWatch.TorobSpider_SmartWatch, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-smartwatch: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-smartwatch: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-smartwatch: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-laptopnotebook")
class CrawlTorob_LaptopNotebook(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-laptopnotebook: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_LaptopNotebook.TorobSpider_LaptopNotebook, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-laptopnotebook: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-laptopnotebook: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-laptopnotebook: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-monitor")
class CrawlTorob_Monitor(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-monitor: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Monitor.TorobSpider_Monitor, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-monitor: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-monitor: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-monitor: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-allinone")
class CrawlTorob_AllInOne(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-allinone: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_AllInOne.TorobSpider_AllInOne, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-allinone: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-allinone: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-allinone: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-desktop")
class CrawlTorob_Desktop(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-desktop: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Desktop.TorobSpider_Desktop, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-desktop: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-desktop: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-desktop: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-minicomputer")
class CrawlTorob_MiniComputer(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-minicomputer: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_MiniComputer.TorobSpider_MiniComputer, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-minicomputer: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-minicomputer: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-minicomputer: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-cpu")
class CrawlTorob_CPU(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-cpu: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_CPU.TorobSpider_CPU, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-cpu: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-cpu: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-cpu: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-motherboard")
class CrawlTorob_Motherboard(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-motherboard: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Motherboard.TorobSpider_Motherboard, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-motherboard: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-motherboard: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-motherboard: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-graphiccard")
class CrawlTorob_GraphicCard(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-graphiccard: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_GraphicCard.TorobSpider_GraphicCard, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-graphiccard: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-graphiccard: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-graphiccard: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-computerram")
class CrawlTorob_ComputerRAM(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-computerram: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_ComputerRAM.TorobSpider_ComputerRAM, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-computerram: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-computerram: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-computerram: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-laptopram")
class CrawlTorob_LaptopRAM(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-laptopram: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_LaptopRAM.TorobSpider_LaptopRAM, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-laptopram: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-laptopram: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-laptopram: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-serverram")
class CrawlTorob_ServerRAM(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-serverram: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_ServerRAM.TorobSpider_ServerRAM, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-serverram: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-serverram: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-serverram: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-computerpower")
class CrawlTorob_ComputerPower(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-computerpower: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_ComputerPower.TorobSpider_ComputerPower, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-computerpower: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-computerpower: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-computerpower: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-computersoundcard")
class CrawlTorob_ComputerSoundCard(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-computersoundcard: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_ComputerSoundCard.TorobSpider_ComputerSoundCard, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-computersoundcard: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-computersoundcard: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-computersoundcard: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-keyboard")
class CrawlTorob_Keyboard(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-keyboard: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Keyboard.TorobSpider_Keyboard, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-keyboard: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-keyboard: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-keyboard: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-mouse")
class CrawlTorob_Mouse(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-mouse: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Mouse.TorobSpider_Mouse, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-mouse: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-mouse: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-mouse: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-mouseandkeyboard")
class CrawlTorob_MouseAndKeyboard(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-mouseandkeyboard: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_MouseAndKeyboard.TorobSpider_MouseAndKeyboard, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-mouseandkeyboard: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-mouseandkeyboard: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-mouseandkeyboard: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-computercase")
class CrawlTorob_ComputerCase(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-computercase: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_ComputerCase.TorobSpider_ComputerCase, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-computercase: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-computercase: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-computercase: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-casefan")
class CrawlTorob_CaseFan(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-casefan: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_CaseFan.TorobSpider_CaseFan, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-casefan: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-casefan: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-casefan: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-hub")
class CrawlTorob_Hub(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-hub: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Hub.TorobSpider_Hub, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-hub: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-hub: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-hub: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-3dprinterandessentials")
class CrawlTorob_3DPrinterAndEssentials(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-3dprinterandessentials: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_3DPrinterAndEssentials.TorobSpider_3DPrinterAndEssentials,
                                   get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-3dprinterandessentials: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-3dprinterandessentials: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-3dprinterandessentials: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-adslvdsl")
class CrawlTorob_AdslVdsl(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-adslvdsl: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_AdslVdsl.TorobSpider_AdslVdsl, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-adslvdsl: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-adslvdsl: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-adslvdsl: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-lte3g4g5g")
class CrawlTorob_Lte3G4G5G(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-lte3g4g5g: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Lte3G4G5G.TorobSpider_Lte3G4G5G, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-lte3g4g5g: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-lte3g4g5g: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-lte3g4g5g: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-fiberopticmodem")
class CrawlTorob_FiberOpticModem(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-fiberopticmodem: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_FiberOpticModem.TorobSpider_FiberOpticModem, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-fiberopticmodem: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-fiberopticmodem: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-fiberopticmodem: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-router")
class CrawlTorob_Router(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-router: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Router.TorobSpider_Router, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-router: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-router: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-router: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-accesspoint")
class CrawlTorob_AccessPoint(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-accesspoint: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_AccessPoint.TorobSpider_AccessPoint, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-accesspoint: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-accesspoint: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-accesspoint: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-networkcard")
class CrawlTorob_NetworkCard(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-networkcard: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_NetworkCard.TorobSpider_NetworkCard, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-networkcard: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-networkcard: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-networkcard: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-switch")
class CrawlTorob_Switch(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-switch: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Switch.TorobSpider_Switch, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-switch: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-switch: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-switch: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-networkcable")
class CrawlTorob_NetworkCable(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-networkcable: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_NetworkCable.TorobSpider_NetworkCable, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-networkcable: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-networkcable: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-networkcable: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-networkmemoryandstorage")
class CrawlTorob_NetworkMemoryAndStorage(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-networkmemoryandstorage: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_NetworkMemoryAndStorage.TorobSpider_NetworkMemoryAndStorage,
                                   get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-networkmemoryandstorage: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-networkmemoryandstorage: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-networkmemoryandstorage: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-server")
class CrawlTorob_Server(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-server: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Server.TorobSpider_Server, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-server: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-server: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-server: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-externalharddrive")
class CrawlTorob_ExternalHardDrive(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-externalharddrive: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_ExternalHardDrive.TorobSpider_ExternalHardDrive, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-externalharddrive: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-externalharddrive: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-externalharddrive: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-internalharddrive")
class CrawlTorob_InternalHardDrive(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-internalharddrive: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_InternalHardDrive.TorobSpider_InternalHardDrive, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-internalharddrive: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-internalharddrive: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-internalharddrive: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-ssdharddrive")
class CrawlTorob_SSDHardDrive(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-ssdharddrive: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_SSDHardDrive.TorobSpider_SSDHardDrive, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-ssdharddrive: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-ssdharddrive: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-ssdharddrive: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-serverharddrive")
class CrawlTorob_ServerHardDrive(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-serverharddrive: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_ServerHardDrive.TorobSpider_ServerHardDrive, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-serverharddrive: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-serverharddrive: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-serverharddrive: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-flashmemory")
class CrawlTorob_FlashMemory(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-flashmemory: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_FlashMemory.TorobSpider_FlashMemory, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-flashmemory: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-flashmemory: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-flashmemory: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-memorycard")
class CrawlTorob_MemoryCard(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-memorycard: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_MemoryCard.TorobSpider_MemoryCard, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-memorycard: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-memorycard: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print("********************** crawl-torob-memorycard: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-networkandsecuritycamera")
class CrawlTorob_NetworkAndSecurityCamera(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-networkandsecuritycamera: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_NetworkAndSecurityCamera.TorobSpider_NetworkAndSecurityCamera,
                                   get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-networkandsecuritycamera: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-networkandsecuritycamera: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print(
                    "********************** crawl-torob-networkandsecuritycamera: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e)
            }, 500


@api.route("/crawl-torob-recorder")
class CrawlTorob_Recorder(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self):
        try:
            # Initialize the crawler object
            print("********************** crawl-torob-recorder: crochet ... **********************")
            self.crawler = Crawler(TorobSpider_Recorder.TorobSpider_Recorder, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl()
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("crawl-torob-recorder: An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** crawl-torob-recorder: Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)

    @token_required
    def post(self):
        try:

            # Start the crawl
            self.crawl_torob_with_crochet()

            while not self.crawl_complete:
                print(
                    "********************** crawl-torob-recorder: Crawling ... **********************")
                time.sleep(5)
                if self.crawl_complete:
                    break

            return 'Crawling operation finished.', 200

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
    app.run(host='0.0.0.0', debug=False)
