# Import needed libraries
import scrapy
import json
import logging
from scrapy.loader import ItemLoader
from items import Product, ProductSellerDetails, Seller, Category
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# Torob spider
class TorobSpider_AccessPoint(scrapy.Spider):
    name = "TorobSpider_AccessPoint"

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1,
        'LOG_LEVEL': 'DEBUG',
        'AUTOTHROTTLE_ENABLED': True,  # Enable AutoThrottle
        'AUTOTHROTTLE_START_DELAY': 1,  # Initial delay for AutoThrottle
        'AUTOTHROTTLE_MAX_DELAY': 3,  # Maximum delay for AutoThrottle
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,  # Target concurrency
        'AUTOTHROTTLE_DEBUG': False,
        'SCRAPEOPS_API_KEY': 'e79c3418-3c44-471b-9d10-7edaca2fad6a',
        'SCRAPEOPS_FAKE_USER_AGENT_ENDPOINT': 'https://headers.scrapeops.io/v1/user-agents',
        'SCRAPEOPS_FAKE_BROWSER_HEADER_ENDPOINT': 'http://headers.scrapeops.io/v1/browser-headers',
        'SCRAPEOPS_FAKE_USER_AGENT_ENABLED': True,
        'SCRAPEOPS_NUM_RESULTS': 30,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 1,
            'middlewares.ScrapeOpsFakeBrowserHeaderAgentMiddleware': 543
        },
        'ITEM_PIPELINES': {
            'pipelines.CreateDatabasePostgresPipeline': 300,
            'pipelines.InsetIntoDatabasePostgresPipeline': 400
        },
        'SPIDERMON_SPIDER_CLOSE_MONITORS': {
            'monitors.SpiderCloseMonitorSuite'
        }
    }

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)

    allowed_domains = ["api.torob.com", "proxy.scrapeops.io", "icanhazip.com"]

    myBaseUrl = ''
    start_urls = [
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=1249&category_name=%D8%A7%DA%A9%D8%B3%D8%B3-%D9%BE%D9%88%DB%8C%D9%86%D8%AA-%D9%88-%D8%B1%D8%A7%D8%AF%DB%8C%D9%88-%D9%88%D8%A7%DB%8C%D8%B1%D9%84%D8%B3&source=next_desktop&rank_offset=24&_bt__experiment=&suid=666851b061f6f51da3634898&_url_referrer='
    ]

    def __init__(self, url='', **kwargs):  
        logger.info("************************* Entered Spider -> url : %s", self.start_requests[0])
        
        # set custom settings
        self.myBaseUrl = url

        super().__init__(**kwargs)

    API_KEY = '6b98e85e-ad38-466b-806b-7c8511be9d5e'

    # Start requests
    def start_requests(self):
        logger.debug("Start of start_requests method")  # Debug log to indicate the method has started
        logger.info("********************** Starting requests ...")
        logger.info("************************* Start URLs: %s", self.start_urls)
        for url in self.start_urls:
            logger.debug("Yielding request for URL: %s", url)  # Debug log before yielding each request
            yield scrapy.Request(url=url, callback=self.parse)
        logger.debug("End of start_requests method")  # Debug log to indicate the method has completed)
            
    # Check the IP
    @staticmethod
    def parse_ip(response):
        logger.info(f"********************** Checking Current IP ...")
        ip_info = response.text
        logger.info(f"********************** Current IP: {ip_info}")

    # Parse the response
    def parse(self, response, **kwargs):
     def parse(self, response, **kwargs):
        logger.debug("Start of parse method")  # Debug log to indicate the method has started
        logger.info("************************* Is proxy in response.meta?: %s", response.meta)
    
        json_res = json.loads(response.text)
        data = json_res['results']
    
        logger.debug("Number of items in response: %d", len(data))  # Debug log to indicate how many items were found
    
        for item in data:
            more_info_url = item['more_info_url']
            logger.info("********************** more_info_url : %s", more_info_url)
        
            product_id = item['random_key']
            logger.info("********************** product_id : %s", product_id)
        
            yield response.follow(url=more_info_url, callback=self.parse_product_page, cb_kwargs={'product_id': product_id})

        next_page = json_res.get('next')
        if next_page is not None:
            logger.info("************************ next_page : %s", next_page)
            yield response.follow(url=next_page, callback=self.parse, errback=self.handle_error)
        else:
            logger.debug("No next page found")  # Debug log to indicate that pagination has ended
    
        logger.debug("End of parse method") 

    # Parses the response into our structured data
    @staticmethod
    def parse_product_page(response, product_id):
        # Load product details
        details_json = json.loads(response.text)

        # Create our structured Product item
        product_loader = ItemLoader(item=Product())
        product_loader.add_value('image_url', details_json['image_url'])
        product_loader.add_value('id', product_id)
        product_loader.add_value('name1', details_json['name1'])
        product_loader.add_value('name2', details_json['name2'])
        product_loader.add_value('more_info_url', details_json['more_info_url'])
        product_loader.add_value('price', details_json['price'])
        product_loader.add_value('price_text', details_json['price_text'])
        product_loader.add_value('shop_text', details_json['shop_text'])
        product_loader.add_value('is_stock', len(details_json['stock_status']) != 0)

        category_items = []

        for category in details_json['breadcrumbs']:
            category_loader = ItemLoader(item=Category())
            category_loader.add_value('id', category['id'])
            category_loader.add_value('title', category['title'])
            category_loader.add_value('url', category['url'])
            category_loader.add_value('brand_id', category['brand_id'])
            category_items.append(category_loader.load_item())

        # Create a list to hold ProductSellerDetails items
        product_seller_details_items = []

        # Now get data related to product seller details and seller
        for psd in details_json['products_info']['result']:
            psd_loader = ItemLoader(item=ProductSellerDetails())
            psd_loader.add_value('name1', psd['name1'])
            psd_loader.add_value('name2', psd['name2'])
            psd_loader.add_value('shop_name', psd['shop_name'])
            psd_loader.add_value('shop_city', psd['shop_name2'])
            psd_loader.add_value('price', psd['price'])
            psd_loader.add_value('price_text', psd['price_text'])
            psd_loader.add_value('last_price_change_date', psd['last_price_change_date'])
            psd_loader.add_value('page_url', psd['page_url'])
            psd_loader.add_value('seller_id', psd['shop_id'])
            psd_loader.add_value('is_stock', len(details_json['stock_status']) != 0)
            psd_loader.add_value('product_id', product_id)

            # Create a separate loader for Seller
            seller_loader = ItemLoader(item=Seller())
            seller_loader.add_value('id', psd['shop_id'])
            seller_loader.add_value('name', psd['shop_name'])
            seller_loader.add_value('city', psd['shop_name2'])

            # Load Seller item and add it to ProductSellerDetails loader
            psd_loader.add_value('seller', seller_loader.load_item())

            # Append the loaded ProductSellerDetails item to the list
            product_seller_details_items.append(psd_loader.load_item())

        # Add the list of ProductSellerDetails and Category items to the product_loader
        product_loader.add_value('product_seller_details', product_seller_details_items)
        product_loader.add_value('categories', category_items)

        yield product_loader.load_item()

    @staticmethod
    def handle_error(error):
        logger.info("********************** An error occurred: %s", error.getErrorMessage())
