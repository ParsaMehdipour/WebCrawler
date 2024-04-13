# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

from scrapy import Item, Field
from scrapy.loader.processors import TakeFirst, Join, Compose


class Product(scrapy.Item):
    # define the fields for your item here like:
    image_url = Field(output_processor=TakeFirst())
    name1 = Field(output_processor=TakeFirst())
    name2 = Field(output_processor=TakeFirst())
    more_info_url = Field(output_processor=TakeFirst())
    price = Field(output_processor=TakeFirst())
    price_text = Field(output_processor=TakeFirst())
    shop_text = Field(output_processor=TakeFirst())
    product_seller_details = Field()


class ProductSellerDetails(scrapy.Item):
    name1 = Field(output_processor=TakeFirst())
    name2 = Field(output_processor=TakeFirst())
    shop_name = Field(output_processor=TakeFirst())
    shop_name2 = Field(output_processor=TakeFirst())
    price = Field(output_processor=TakeFirst())
    price_text = Field(output_processor=TakeFirst())
    last_price_change_date = Field(output_processor=TakeFirst())
