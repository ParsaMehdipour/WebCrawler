import scrapy
import json

from scrapy.loader import ItemLoader
from WebCralwer.items import Product

class TorobSpider(scrapy.Spider):
    name = "torob"
    allowed_domains = ["api.torob.com"]
    start_urls = ["https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=100&category_name=%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D9%88-%DA%A9%D8%A7%D9%84%D8%A7%DB%8C-%D8%AF%DB%8C%D8%AC%DB%8C%D8%AA%D8%A7%D9%84&category_id=175&category=175&source=next_desktop&suid=66191da888517ca4b24c6853&_bt__experiment=&_url_referrer="]

    def parse(self, response):
        json_res = json.loads(response.text)

        data = json_res['results']
        for item in data:
            loader = ItemLoader(item=Product())
            loader.add_value('image_url', item['image_url'])
            loader.add_value('name1', item['name1'])
            loader.add_value('name2', item['name2'])
            loader.add_value('more_info_url', item['more_info_url'])
            loader.add_value('price', item['price'])
            loader.add_value('price_text', item['price_text'])
            loader.add_value('shop_text', item['shop_text'])
            loader.add_value('delivery_city_name', item['delivery_city_name'])
            loader.add_value('delivery_city_flag', item['delivery_city_flag'])
            yield loader.load_item()

        next_page = json_res['next']
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

