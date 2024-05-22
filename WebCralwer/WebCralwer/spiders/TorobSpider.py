# Import needed libraries
import scrapy
import json
from scrapy.loader import ItemLoader
from items import Product, ProductSellerDetails, Seller, Category
from urllib.parse import urlencode


# Torob spider
class TorobSpider(scrapy.Spider):
    name = "TorobSpider"

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
	'LOG_LEVEL': 'DEBUG',
        'SCRAPEOPS_API_KEY': 'e79c3418-3c44-471b-9d10-7edaca2fad6a',
        'SCRAPEOPS_FAKE_USER_AGENT_ENDPOINT': 'https://headers.scrapeops.io/v1/user-agents',
        'SCRAPEOPS_FAKE_BROWSER_HEADER_ENDPOINT': 'http://headers.scrapeops.io/v1/browser-headers',
        'SCRAPEOPS_FAKE_USER_AGENT_ENABLED': True,
        'SCRAPEOPS_NUM_RESULTS': 30,
        'DOWNLOADER_MIDDLEWARES': {
            # 'middlewares.ProxyMiddleware': 523,
            # 'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 533,
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

    allowed_domains = ["api.torob.com", "proxy.scrapeops.io"]

    myBaseUrl = ''
    start_urls = ['https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=10&category_name=%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D9%88-%DA%A9%D8%A7%D9%84%D8%A7%DB%8C-%D8%AF%DB%8C%D8%AC%DB%8C%D8%AA%D8%A7%D9%84&category_id=175&category=175&source=next_desktop&suid=66191da888517ca4b24c6853&_bt__experiment=&_url_referrer=']

    def __init__(self, url='', **kwargs):  # The category variable will have the input URL.
        print("************************* Entered Spider -> url : ", url)
        # set custom settings
        self.myBaseUrl = url
        self.start_urls.append(self.myBaseUrl)
        super().__init__(**kwargs)

    API_KEY = '6b98e85e-ad38-466b-806b-7c8511be9d5e'

    # Get proxy url from ScrapeOps proxy aggregator
    def get_proxy_url(self, url):
        print("************************* Getting proxy ... **********************")
        # Load the api key
        payload = {'api_key': self.API_KEY, 'url': url}
        # ScrapeOps url
        proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        print("************************* Proxy url : ", proxy_url)
        return proxy_url

    # Start requests
    def start_requests(self):
        print("********************** Starting requests ...")
        # yield scrapy.Request(url=self.get_proxy_url(self.start_urls[0]), callback=self.parse)
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse)

    # Parse the response
    def parse(self, response, **kwargs):
        json_res = json.loads(response.text)

        data = json_res['results']

        for item in data:
            # Response contains a field with the name of 'more_info_url', it is the details url of the product
            more_info_url = item['more_info_url']

            print("********************** more_info_url : ", more_info_url)

            # Fetch the product_id from the response
            product_id = item['random_key']

            print("********************** product_id : ", product_id)
            # Send api call to the more info url
            # yield scrapy.Request(url=self.get_proxy_url(more_info_url), callback=self.parse_product_page,
            #                      cb_kwargs={'product_id': product_id})
            yield response.follow(url=more_info_url, callback=self.parse_product_page,
                                  cb_kwargs={'product_id': product_id})

        # Response contains a field with the name of 'next' which is the url of the next page in our pagination,
        # when it does not exist means that there are no next pages
        # next_page = json_res['next']
        # if next_page is not None:
        #     print("************************ next_page : ", next_page)
        #     # Send an api call to the next page
        #     yield response.follow(url=self.get_proxy_url(next_page), callback=self.parse, errback=self.handle_error)

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

    def handle_error(error):
        print("********************** An error occurred:", error.getErrorMessage())
