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
        'DOWNLOAD_DELAY': 1,
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
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=10&category=94&category_name=%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-mobile&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66606f82d64bebbac440c734&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=10&category=95&category_name=%D8%AA%D8%A8%D9%84%D8%AA-tablet&source=next_desktop&rank_offset=24&_bt__experiment=&suid=6660720269ecceb34e8c9f65&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=97&category_name=%D9%87%D8%AF%D9%81%D9%88%D9%86-%D9%87%D8%AF%D8%B3%D8%AA-%D9%88-%D9%87%D9%86%D8%AF%D8%B2%D9%81%D8%B1%DB%8C-headphone-and-headset&source=next_desktop&rank_offset=24&_bt__experiment=&suid=666067ca1204d5d876c29bba&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=1460&category_name=%D8%B4%D8%A7%D8%B1%DA%98%D8%B1&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608a1338824c8929c63b58&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=1007&category_name=%DA%A9%D8%A7%D8%A8%D9%84-%D9%88-%D8%AA%D8%A8%D8%AF%DB%8C%D9%84&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608a34bf45a3c7f360a314&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=760&category_name=%D9%BE%D8%A7%DB%8C%D9%87-%D9%86%DA%AF%D9%87%D8%AF%D8%A7%D8%B1%D9%86%D8%AF%D9%87-%DA%AF%D9%88%D8%B4%DB%8C-%D9%88-%D8%AA%D8%A8%D9%84%D8%AA&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608a4fcb27f2f5942a370a&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=366&category_name=%D9%85%D9%88%D9%86%D9%88%D9%BE%D8%A7%D8%AF-%D9%88-%DA%AF%DB%8C%D9%85%D8%A8%D8%A7%D9%84-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-monopod&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608a7603f08311ae71bba2&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=369&category_name=%D9%BE%D8%A7%D9%88%D8%B1%D8%A8%D8%A7%D9%86%DA%A9-%D9%88-%D8%B4%D8%A7%D8%B1%DA%98%D8%B1-%D9%87%D9%85%D8%B1%D8%A7%D9%87-powerbank&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608a8cbddead49eff5d0fa&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=282&category_name=%D8%B3%D8%A7%D8%B9%D8%AA-%D9%88-%D9%85%DA%86-%D8%A8%D9%86%D8%AF-%D9%87%D9%88%D8%B4%D9%85%D9%86%D8%AF-smart-watch&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608aa285243f8e2e7bcde8&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=99&category_name=%D9%84%D9%BE-%D8%AA%D8%A7%D9%BE-%D9%88-%D9%86%D9%88%D8%AA-%D8%A8%D9%88%DA%A9-laptop&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608ac02bd8d60d0fc66f11&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=230&category_name=%D9%85%D8%A7%D9%86%DB%8C%D8%AA%D9%88%D8%B1-monitor&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608a3110d2eb042df38e4d&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=231&category_name=%DA%A9%D8%A7%D9%85%D9%BE%DB%8C%D9%88%D8%AA%D8%B1-%D9%87%D8%A7%DB%8C-all-in-one-all-in-one&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608af60b95b3c24c452c6d&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=232&category_name=%DA%A9%D8%A7%D9%85%D9%BE%DB%8C%D9%88%D8%AA%D8%B1-%D8%AF%D8%B3%DA%A9%D8%AA%D8%A7%D9%BE-others-monitor&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608b1780a05ab48bb2549c&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=970&category_name=%D9%85%DB%8C%D9%86%DB%8C-%DA%A9%D8%A7%D9%85%D9%BE%DB%8C%D9%88%D8%AA%D8%B1&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608b3f0c3cfc9755a134a1&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=519&category_name=%D9%BE%D8%B1%D8%AF%D8%A7%D8%B2%D9%86%D8%AF%D9%87-cpu&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608b5423e65b6f8f615332&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=520&category_name=%D9%85%D8%A7%D8%AF%D8%B1%D8%A8%D9%88%D8%B1%D8%AF-computer-moderboard&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608b674e92b9c25e4e9577&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=522&category_name=%DA%A9%D8%A7%D8%B1%D8%AA-%DA%AF%D8%B1%D8%A7%D9%81%DB%8C%DA%A9-graphic-card&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608b992ce6ea5342efd92f&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=518&category_name=%D8%B1%D9%85-%DA%A9%D8%A7%D9%85%D9%BE%DB%8C%D9%88%D8%AA%D8%B1-computer-ram&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608bb5ea576b44cb7f1075&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=523&category_name=%D8%B1%D9%85-%D9%84%D9%BE-%D8%AA%D8%A7%D9%BE-laptop-ram&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608bd3739a9457446a6de5&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=1866&category_name=%D8%B1%D9%85-%D8%B3%D8%B1%D9%88%D8%B1&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608bf9ee48bf2ca8ec4549&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=521&category_name=%D9%BE%D8%A7%D9%88%D8%B1-%DA%A9%D8%A7%D9%85%D9%BE%DB%8C%D9%88%D8%AA%D8%B1-computer-power&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608c11f78fd2158ab0cb49&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=1013&category_name=%DA%A9%D8%A7%D8%B1%D8%AA-%D8%B5%D8%AF%D8%A7-%DA%A9%D8%A7%D9%85%D9%BE%DB%8C%D9%88%D8%AA%D8%B1-computer-sound-card&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608c5f2bd8d60d0fc67254&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=233&category_name=%DA%A9%DB%8C%D8%A8%D9%88%D8%B1%D8%AF-keyboard&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608870d173f37eb2d04b73&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=234&category_name=%D9%85%D8%A7%D9%88%D8%B3-mouse&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608c85d9bd7a869fa48221&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=242&category_name=%D8%B3%D8%AA-%D9%85%D8%A7%D9%88%D8%B3-%D9%88-%DA%A9%DB%8C%D8%A8%D9%88%D8%B1%D8%AF-mouse-and-keyboard&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608c9f287106ba976637cf&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=239&category_name=%DA%A9%DB%8C%D8%B3-%DA%A9%D8%A7%D9%85%D9%BE%DB%8C%D9%88%D8%AA%D8%B1-case&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608ab964b45e5a74468acd&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=983&category_name=%D9%81%D9%86-%DA%A9%DB%8C%D8%B3&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608cd5f6a5a10a25ce4ac4&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=1011&category_name=%D9%87%D8%A7%D8%A8-usb&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608cf0727290ef1833165a&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=939&category_name=%D9%BE%D8%B1%DB%8C%D9%86%D8%AA%D8%B1-%D8%B3%D9%87-%D8%A8%D8%B9%D8%AF%DB%8C-%D9%88-%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608d09167806859caa0d1a&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=1246&category_name=%D9%85%D9%88%D8%AF%D9%85-adsl-vdsl&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608d2312ce57544255742e&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=1247&category_name=%D9%85%D9%88%D8%AF%D9%85-lte-3g-4g-5g&source=next_desktop&rank_offset=24&_bt__experiment=&suid=6660892c78a318bc11bc2b3d&_url_referrer=',
        'https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=24&category=1253&category_name=%D9%85%D9%88%D8%AF%D9%85-%D9%81%DB%8C%D8%A8%D8%B1-%D9%86%D9%88%D8%B1%DB%8C-%D9%88-%D9%85%D8%AE%D8%A7%D8%A8%D8%B1%D8%A7%D8%AA%DB%8C&source=next_desktop&rank_offset=24&_bt__experiment=&suid=66608c8e2bd8d60d0fc672a5&_url_referrer='
    ]

    def __init__(self, url='', **kwargs):  # The category variable will have the input URL.
        print("************************* Entered Spider -> url : ", url)
        # set custom settings
        self.myBaseUrl = url
        # self.start_urls.append(self.myBaseUrl)
        super().__init__(**kwargs)

        # if len(self.start_urls) > 0:
        #     self.start_urls.clear()

        # with open('startUrls.txt') as my_file:
        #     self.start_urls = [line.strip() for line in my_file.readlines()]

    API_KEY = '6b98e85e-ad38-466b-806b-7c8511be9d5e'

    # Start requests
    def start_requests(self):
        print("********************** Starting requests ...")
        # Check IP address to verify proxy
        ip_check_url = 'https://icanhazip.com/'
        yield scrapy.Request(url=ip_check_url, callback=self.parse_ip)
        # yield scrapy.Request(url=self.get_proxy_url(self.start_urls[0]), callback=self.parse)
        print("********************** Passed Urls till now : ", self.start_urls)
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    # Check the IP
    def parse_ip(self, response):
        print(f"********************** Checking Current IP ...")
        ip_info = response.text
        print(f"********************** Current IP: {ip_info}")

    # Parse the response
    def parse(self, response, **kwargs):
        json_res = json.loads(response.text)
        print("********************** Is proxy in response.meta?: ", response.meta)

        data = json_res['results']

        for item in data:
            # Response contains a field with the name of 'more_info_url', it is the details url of the product
            more_info_url = item['more_info_url']

            print("********************** more_info_url : ", more_info_url)

            # Fetch the product_id from the response
            product_id = item['random_key']

            print("********************** product_id : ", product_id)
            # Send api call to the more info url
            yield response.follow(url=more_info_url, callback=self.parse_product_page,
                                  cb_kwargs={'product_id': product_id})

        # Response contains a field with the name of 'next' which is the url of the next page in our pagination,
        # when it does not exist means that there are no next pages
        next_page = json_res['next']
        if next_page is not None:
            print("************************ next_page : ", next_page)
            # Send an api call to the next page
            yield response.follow(url=next_page, callback=self.parse, errback=self.handle_error)

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
