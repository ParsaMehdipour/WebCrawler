# Import needed libraries
import scrapy
import json
from scrapy.loader import ItemLoader
from WebCralwer.items import Product
from WebCralwer.items import ProductSellerDetails
from WebCralwer.items import Seller
from urllib.parse import urlencode


# Torob spider
class TorobSpider(scrapy.Spider):
    name = "TorobSpider"
    allowed_domains = ["api.torob.com", "proxy.scrapeops.io"]
    start_urls = [
        "https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=100&category_name=%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D9%88-%DA%A9%D8%A7%D9%84%D8%A7%DB%8C-%D8%AF%DB%8C%D8%AC%DB%8C%D8%AA%D8%A7%D9%84&category_id=175&category=175&source=next_desktop&suid=66191da888517ca4b24c6853&_bt__experiment=&_url_referrer="
        # PCs "https://api.torob.com/v4/base-product/search/?page=2&sort=popularity&size=100&category_name=%D9%84%D9%BE-%D8%AA%D8%A7%D9%BE-%DA%A9%D8%A7%D9%85%D9%BE%DB%8C%D9%88%D8%AA%D8%B1-%D8%A7%D8%AF%D8%A7%D8%B1%DB%8C&category_id=173&category=173&_url_referrer=https%3A%2F%2Fwww.google.com%2F&source=next_desktop&suid=661be9fcf070a382b364232b&_bt__experiment=&_url_referrer="
    ]

    API_KEY = '5bfd225b-d4fc-4c4b-889d-7c4c996f6a02'

    # Get proxy url from ScrapeOps proxy aggregator
    def get_proxy_url(self, url):
        # Load the api key
        payload = {'api_key': self.API_KEY, 'url': url}
        # ScrapeOps url
        proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        return proxy_url

    # Start requests
    def start_requests(self):
        yield scrapy.Request(url=self.get_proxy_url(self.start_urls[0]), callback=self.parse)

    # Parse the response
    def parse(self, response, **kwargs):
        json_res = json.loads(response.text)

        data = json_res['results']

        for item in data:
            # Response contains a field with the name of 'more_info_url', it is the details url of the product
            more_info_url = item['more_info_url']

            # Fetch the product_id from the response
            product_id = item['random_key']
            # Send api call to the more info url
            yield scrapy.Request(url=self.get_proxy_url(more_info_url), callback=self.parse_product_page,
                                 cb_kwargs={'product_id': product_id})

        # Response contains a field with the name of 'next' which is the url of the next page in our pagination,
        # when it does not exist means that there are no next pages
        next_page = json_res['next']
        if next_page is not None:
            # Send an api call to the next page
            yield response.follow(url=self.get_proxy_url(next_page), callback=self.parse)

        # Parses the response into our structured data

    @staticmethod
    def parse_product_page(response, product_id):
        # Load product details
        details_json = json.loads(response.text)

        # Create our structured Product item
        details_loader = ItemLoader(item=Product())
        details_loader.add_value('image_url', details_json['image_url'])
        details_loader.add_value('id', product_id)
        details_loader.add_value('name1', details_json['name1'])
        details_loader.add_value('name2', details_json['name2'])
        details_loader.add_value('more_info_url', details_json['more_info_url'])
        details_loader.add_value('price', details_json['price'])
        details_loader.add_value('price_text', details_json['price_text'])
        details_loader.add_value('shop_text', details_json['shop_text'])

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

        # Add the list of ProductSellerDetails items to the details_loader
        details_loader.add_value('product_seller_details', product_seller_details_items)

        yield details_loader.load_item()


