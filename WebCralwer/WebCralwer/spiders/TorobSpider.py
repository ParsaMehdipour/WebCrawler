import scrapy
import json

from scrapy.loader import ItemLoader
from WebCralwer.items import Product
from WebCralwer.items import ProductSellerDetails


class TorobSpider(scrapy.Spider):
    name = "TorobSpider"
    allowed_domains = ["api.torob.com"]
    start_urls = [
        "https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=100&category_name=%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D9%88-%DA%A9%D8%A7%D9%84%D8%A7%DB%8C-%D8%AF%DB%8C%D8%AC%DB%8C%D8%AA%D8%A7%D9%84&category_id=175&category=175&source=next_desktop&suid=66191da888517ca4b24c6853&_bt__experiment=&_url_referrer="
        # PCs "https://api.torob.com/v4/base-product/search/?page=2&sort=popularity&size=100&category_name=%D9%84%D9%BE-%D8%AA%D8%A7%D9%BE-%DA%A9%D8%A7%D9%85%D9%BE%DB%8C%D9%88%D8%AA%D8%B1-%D8%A7%D8%AF%D8%A7%D8%B1%DB%8C&category_id=173&category=173&_url_referrer=https%3A%2F%2Fwww.google.com%2F&source=next_desktop&suid=661be9fcf070a382b364232b&_bt__experiment=&_url_referrer="
    ]

    def parse(self, response):
        json_res = json.loads(response.text)

        data = json_res['results']
        for item in data:
            more_info_url = item['more_info_url']
            yield scrapy.Request(more_info_url, callback=self.parse_product_page)

        next_page = json_res['next']
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_product_page(self, response):
        details_json = json.loads(response.text)
        details_loader = ItemLoader(item=Product())
        details_loader.add_value('image_url', details_json['image_url'])
        details_loader.add_value('name1', details_json['name1'])
        details_loader.add_value('name2', details_json['name2'])
        details_loader.add_value('more_info_url', details_json['more_info_url'])
        details_loader.add_value('price', details_json['price'])
        details_loader.add_value('price_text', details_json['price_text'])
        details_loader.add_value('shop_text', details_json['shop_text'])

        product_seller_details = details_json['products_info']['result']

        for psd in product_seller_details:
            psd_loader = ItemLoader(item=ProductSellerDetails())
            psd_loader.add_value('name1', psd['name1'])
            psd_loader.add_value('name2', psd['name2'])
            psd_loader.add_value('shop_name', psd['shop_name'])
            psd_loader.add_value('shop_name2', psd['shop_name2'])
            psd_loader.add_value('price', psd['price'])
            psd_loader.add_value('price_text', psd['price_text'])
            psd_loader.add_value('last_price_change_date', psd['last_price_change_date'])
            details_loader.add_value('product_seller_details', psd_loader.load_item())

        yield details_loader.load_item()
