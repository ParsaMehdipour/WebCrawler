# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

from scrapy import Item, Field
from scrapy.loader.processors import Join, Compose
from itemloaders.processors import TakeFirst


class Product(scrapy.Item):
    # define the fields for your item here like:
    id = Field(output_processor=TakeFirst())
    image_url = Field(output_processor=TakeFirst())
    name1 = Field(output_processor=TakeFirst())
    name2 = Field(output_processor=TakeFirst())
    more_info_url = Field(output_processor=TakeFirst())
    price = Field(output_processor=TakeFirst())
    price_text = Field(output_processor=TakeFirst())
    shop_text = Field(output_processor=TakeFirst())
    is_stock = Field(output_processor=TakeFirst())
    product_seller_details = Field()
    categories = Field()


class ProductSellerDetails(scrapy.Item):
    id = Field(output_processor=TakeFirst())
    name1 = Field(output_processor=TakeFirst())
    name2 = Field(output_processor=TakeFirst())
    shop_name = Field(output_processor=TakeFirst())
    shop_city = Field(output_processor=TakeFirst())
    price = Field(output_processor=TakeFirst())
    price_text = Field(output_processor=TakeFirst())
    last_price_change_date = Field(output_processor=TakeFirst())
    is_stock = Field(output_processor=TakeFirst())
    page_url = Field(output_processor=TakeFirst())
    product_id = Field(output_processor=TakeFirst())
    seller_id = Field(output_processor=TakeFirst())
    seller = Field(output_processor=TakeFirst())


class Seller(scrapy.Item):
    id = Field(output_processor=TakeFirst())
    name = Field(output_processor=TakeFirst())
    city = Field(output_processor=TakeFirst())


class Category(scrapy.Item):
    id = Field(output_processor=TakeFirst())
    title = Field(output_processor=TakeFirst())
    url = Field(output_processor=TakeFirst())
    brand_id = Field(output_processor=TakeFirst())
