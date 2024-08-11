# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import psycopg2
from items import Product
from DataAccess.Models.Torob.TorobProduct import TorobProduct
from DataAccess.Models.Torob.TorobSeller import TorobSeller
from DataAccess.Models.Torob.TorobProductSellerDetails import TorobProductSellerDetails
from DataAccess.Models.Torob.TorobBrand import TorobBrand
from DataAccess.Models.Torob.TorobCategory import TorobCategory
from DataAccess.Implementations.TorobProductRepository import TorobProductRepository
from DataAccess.Implementations.TorobSellerRepository import TorobSellerRepository
from DataAccess.Implementations.TorobCategoryRepository import TorobCategoryRepository
from DataAccess.Implementations.TorobBrandRepository import TorobBrandRepository
from DataAccess.Implementations.TorobProductSellerDetailsRepository import TorobProductSellerDetailsRepository
from Services.TorobProductService import TorobProductService
from Services.TorobBrandService import TorobBrandService
from Services.TorobSellerService import TorobSellerService
from Services.TorobCategoryService import TorobCategoryService
from Services.TorobProductSellerDetailsService import TorobProductSellerDetailsService

Base = declarative_base()


class WebcralwerPipeline:
    @staticmethod
    def process_item(item, spider):
        print("********************** Processing item in pipeline:", item)
        return item


class CreateDatabasePostgresPipeline:
    def __init__(self):
        print("********************** Creating database postgres **********************")
        # Connect to the PostgresSQL database
        try:
            self.connection = psycopg2.connect(
                host='postgresDb',
                user='docker',
                password='docker',
                database='crawler_db'
            )

            self.cursor = self.connection.cursor()
            print("********************** cursor: ", self.cursor)

            # Create 'public' schema if it doesn't exist
            self.cursor.execute("CREATE SCHEMA IF NOT EXISTS public")

            # Create Products table if none exists
            self.cursor.execute("""
                                    CREATE TABLE IF NOT EXISTS public.Brands(
                                    id SERIAL PRIMARY KEY, 
                                    title TEXT,
                                    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    )
                                    """)

            # Create Products table if none exists
            self.cursor.execute("""
                                  CREATE TABLE IF NOT EXISTS public.Categories(
                                  id SERIAL PRIMARY KEY, 
                                  title TEXT,
                                  url TEXT,
                                  brand_id INTEGER REFERENCES public.Brands(id), 
                                  created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                  )
                                  """)

            # Create Products table if none exists
            self.cursor.execute("""
                  CREATE TABLE IF NOT EXISTS public.Products(
                  id TEXT PRIMARY KEY, 
                  image_url TEXT,
                  name1 TEXT,
                  name2 TEXT,
                  more_info_url TEXT,
                  price FLOAT,
                  price_text TEXT,
                  shop_text TEXT,
                  category_name TEXT,
                  brand_name TEXT,
                  is_stock BOOLEAN,
                  created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)

            # Create Seller if none exists
            self.cursor.execute("""
                        CREATE TABLE IF NOT EXISTS public.Sellers(
                         id SERIAL PRIMARY KEY,
                         name TEXT,
                         city TEXT,
                         is_flagged BOOLEAN,
                         created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                          )
                        """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS public.ProductSellerDetails(
                    id SERIAL PRIMARY KEY,
                    name1 TEXT,
                    name2 TEXT,
                    shop_name TEXT,
                    shop_name2 TEXT,
                    price FLOAT,
                    price_text TEXT,
                    last_price_change_date DATE,
                    page_url TEXT,
                    product_id TEXT REFERENCES public.Products(id),
                    seller_id INTEGER REFERENCES public.Sellers(id),
                    is_stock BOOLEAN,
                    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.connection.commit()
        except Exception as e:
            print("Error:", e)

    def close_spider(self, spider):
        # Close cursor & connection to database
        print("***************Closing spider***************")
        self.cursor.close()
        self.connection.close()


class InsetIntoDatabasePostgresPipeline:
    def __init__(self):
        # Connect to the database
        self.connectionString = create_engine('postgresql://docker:docker@postgresDb/crawler_db')
        self.torobProductRepository = TorobProductRepository(self.connectionString)
        self.torobSellerRepository = TorobSellerRepository(self.connectionString)
        self.torobCategoryRepository = TorobCategoryRepository(self.connectionString)
        self.torobBrandRepository = TorobBrandRepository(self.connectionString)
        self.torobProductSellerDetailsRepository = TorobProductSellerDetailsRepository(self.connectionString)
        self.torobProductService = TorobProductService(self.torobProductRepository)
        self.torobBrandService = TorobBrandService(self.torobBrandRepository)
        self.torobSellerService = TorobSellerService(self.torobSellerRepository)
        self.torobCategoryService = TorobCategoryService(self.torobCategoryRepository)
        self.torobProductSellerDetailsService = TorobProductSellerDetailsService(
            self.torobProductSellerDetailsRepository)

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_item(self, item, spider):
        session = self.Session()
        print("********************** Processing item type:", type(item))
        try:
            if isinstance(item, Product):
                category_name = ""
                brand_name = ""
                categories = item['categories']

                if categories is not None:
                    for category in categories:
                        brand_id = category.get('brand_id', 'Empty')
                        if brand_id != "Empty":
                            existing_brand = self.torobBrandService.get_item_by_id(brand_id)
                            if existing_brand is None:
                                brand = TorobBrand(
                                    id=brand_id,
                                    title=category.get('title', 'Empty'),
                                    created_on=datetime.now()
                                )
                                self.torobBrandService.create_item(brand)
                            category_name = category_name + category['title']
                            brand_name = category['title']
                        else:
                            existing_category = self.torobCategoryService.get_item_by_id(category['id'])
                            if existing_category is None:
                                database_category = TorobCategory(
                                    id=category['id'],
                                    title=category.get('title', 'Empty'),
                                    url=category.get('url', 'Empty'),
                                    brand_id=None,
                                    created_on=datetime.now()
                                )
                                self.torobCategoryService.create_item(category)
                            category_name = category_name + category['title'] + " - "

                print("********************** Product item:", item['id'], item['name1'], item.get('name2', 'Empty'))
                product_id = item['id']
                existing_product = self.torobProductService.get_item_by_id(product_id)
                if existing_product is None:
                    product = TorobProduct(
                        id=item['id'],
                        image_url=item.get('image_url', 'Empty'),
                        name1=item.get('name1', 'Empty'),
                        name2=item.get('name2', 'Empty'),
                        more_info_url=item['more_info_url'],
                        price=item.get('price', 'Empty'),
                        price_text=item.get('price_text', 'Empty'),
                        shop_text=item.get('shop_text', 'Empty'),
                        is_stock=item.get('is_stock', 'Empty'),
                        category_name=category_name,
                        brand_name=brand_name,
                        created_on=datetime.now()
                    )
                    self.torobProductService.create_item(product)
                else:
                    print("********************** Product item with the fallowing id exists: ", product_id)

                psds = item['product_seller_details']

                if psds is not None:
                    for psd in psds:

                        seller = psd['seller']

                        if seller is not None:
                            # Check if Seller exists
                            seller_id = seller['id']
                            existing_seller = self.torobSellerService.get_item_by_id(seller_id)
                            if existing_seller is None:
                                seller = TorobSeller(
                                    id=seller['id'],
                                    name=seller.get('name', 'Empty'),
                                    city=seller.get('city', 'Empty'),
                                    created_on=datetime.now()
                                )
                                self.torobSellerService.create_item(seller)
                        else:
                            print("********************** Seller item with the fallowing id exists: ", seller_id)

                        product_seller_details = TorobProductSellerDetails(
                            name1=psd.get('name1', 'Empty'),
                            name2=psd.get('name2', 'Empty'),
                            shop_name=psd.get('shop_name', 'Empty'),
                            shop_city=psd.get('shop_city', 'Empty'),
                            price=psd.get('price', 'Empty'),
                            price_text=psd.get('price_text', 'Empty'),
                            last_price_change_date=psd.get('last_price_change_date', 'Empty'),
                            page_url=psd.get('page_url', 'Empty'),
                            seller_id=psd.get('seller_id', 'Empty'),
                            product_id=psd.get('product_id', 'Empty'),
                            is_stock=psd.get('is_stock', 'Empty'),
                            created_on=datetime.now()
                        )
                        self.torobProductSellerDetailsService.create_item(product_seller_details)
            else:
                print("********************** Unknown item type:", type(item))
        except Exception as e:
            raise e

        return item
