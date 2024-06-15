# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from itemadapter import ItemAdapter
from datetime import datetime
import psycopg2
from items import Product, ProductSellerDetails, Seller

Base = declarative_base()


# Define your SQLAlchemy models
class DatabaseProduct(Base):
    __tablename__ = 'products'
    id = Column(String, primary_key=True)
    image_url = Column(String)
    name1 = Column(String)
    name2 = Column(String)
    more_info_url = Column(String)
    price = Column(Integer)
    price_text = Column(String)
    shop_text = Column(String)
    is_stock = Column(Boolean, default=False)
    category_name = Column(String)
    brand_name = Column(String)
    created_on = Column(DateTime, default=datetime.now)

    def to_json(self):
        return {
            'id': self.id,
            'image_url': self.image_url,
            'name1': self.name1,
            'name2': self.name2,
            'more_info_url': self.more_info_url,
            'price': self.price,
            'price_text': self.price_text,
            'shop_text': self.shop_text,
            'is_stock': self.is_stock,
            'created_on': self.created_on
        }


class DatabaseSeller(Base):
    __tablename__ = 'sellers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String)
    is_flagged = Column(Boolean, default=False)
    created_on = Column(DateTime, default=datetime.now)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'is_flagged': self.is_flagged,
            'created_on': self.created_on
        }


class DatabaseProductSellerDetails(Base):
    __tablename__ = 'product_seller_details'
    id = Column(Integer, primary_key=True)
    name1 = Column(String)
    name2 = Column(String)
    shop_name = Column(String)
    shop_city = Column(String)
    price = Column(Integer)
    price_text = Column(String)
    last_price_change_date = Column(String)
    page_url = Column(String)
    is_stock = Column(Boolean, default=False)
    created_on = Column(DateTime, default=datetime.now)
    seller_id = Column(Integer, ForeignKey('sellers.id'))
    product_id = Column(String, ForeignKey('products.id'))
    product = relationship("DatabaseProduct")
    seller = relationship("DatabaseSeller")

    def to_json(self):
        return {
            'id': self.id,
            'name1': self.name1,
            'name2': self.name2,
            'shop_name': self.shop_name,
            'shop_city': self.shop_city,
            'price': self.price,
            'price_text': self.price_text,
            'last_price_change_date': self.last_price_change_date,
            'page_url': self.page_url,
            'is_stock': self.is_stock,
            'seller_id': self.seller_id,
            'product_id': self.product_id,
            'created_on': self.created_on
        }


class DatabaseBrand(Base):
    __tablename__ = 'brands'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    created_on = Column(DateTime, default=datetime.now)

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'created_on': self.created_on
        }


class DatabaseCategory(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    brand_id = Column(Integer, ForeignKey('brands.id'))
    created_on = Column(DateTime, default=datetime.now)

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'brand_id': self.brand_id,
            'created_on': self.created_on
        }


class StructuredProductDto:
    def __init__(self, name1, name2, category_name, brand_name, price, price_text, created_on, is_stock, psd_id, seller_name,
                 seller_city, image_url):
        self.name1 = name1
        self.name2 = name2
        self.category_name = category_name
        self.brand_name = brand_name
        self.price = price
        self.price_text = price_text
        self.created_on = created_on
        self.is_stock = is_stock
        self.psd_id = psd_id
        self.seller_name = seller_name
        self.seller_city = seller_city
        self.image_url = image_url

    def to_json(self):
        return {
            'name1': self.name1,
            'name2': self.name2,
            'category_name': self.category_name,
            'brand_name': self.brand_name,
            'price': self.price,
            'price_text': self.price_text,
            'created_on': self.created_on,
            'is_stock': self.is_stock,
            'psd_id': self.psd_id,
            'seller_name': self.seller_name,
            'seller_city': self.seller_city,
            'image_url': self.image_url
        }


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
                user='postgres',
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
        self.engine = create_engine('postgresql://postgres:docker@postgresDb/crawler_db')
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)

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
                            existing_brand = session.query(DatabaseBrand).filter_by(id=brand_id).first()
                            if existing_brand is None:
                                brand = DatabaseBrand(
                                    id=brand_id,
                                    title=category.get('title', 'Empty'),
                                    created_on=datetime.now()
                                )
                                session.add(brand)
                                session.commit()
                            category_name = category_name + category['title']
                            brand_name = category['title']
                        else:
                            existing_category = session.query(DatabaseCategory).filter_by(id=category['id']).first()
                            if existing_category is None:
                                database_category = DatabaseCategory(
                                    id=category['id'],
                                    title=category.get('title', 'Empty'),
                                    url=category.get('url', 'Empty'),
                                    brand_id=None,
                                    created_on=datetime.now()
                                )
                                session.add(database_category)
                                session.commit()
                            category_name = category_name + category['title'] + " - "

                print("********************** Product item:", item['id'], item['name1'], item.get('name2', 'Empty'))
                product_id = item['id']
                existing_product = session.query(DatabaseProduct).filter_by(id=product_id).first()
                if existing_product is None:
                    product = DatabaseProduct(
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
                    session.add(product)
                    session.commit()
                else:
                    print("********************** Product item with the fallowing id exists: ", product_id)

                psds = item['product_seller_details']

                if psds is not None:
                    for psd in psds:

                        seller = psd['seller']

                        if seller is not None:
                            # Check if Seller exists
                            seller_id = seller['id']
                            existing_seller = session.query(DatabaseSeller).filter_by(id=seller_id).first()
                            if existing_seller is None:
                                seller = DatabaseSeller(
                                    id=seller['id'],
                                    name=seller.get('name', 'Empty'),
                                    city=seller.get('city', 'Empty'),
                                    created_on=datetime.now()
                                )
                                session.add(seller)
                                session.commit()
                        else:
                            print("********************** Seller item with the fallowing id exists: ", seller_id)

                        product_seller_details = DatabaseProductSellerDetails(
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
                        session.add(product_seller_details)
                        session.commit()
            else:
                print("********************** Unknown item type:", type(item))
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

        return item
