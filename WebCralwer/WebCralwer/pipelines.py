# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from WebCralwer.items import Product, ProductSellerDetails, Seller
from itemadapter import ItemAdapter
import psycopg2

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


class DatabaseSeller(Base):
    __tablename__ = 'sellers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String)


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
    seller_id = Column(Integer, ForeignKey('sellers.id'))
    product_id = Column(String, ForeignKey('products.id'))
    product = relationship("DatabaseProduct")
    seller = relationship("DatabaseSeller")


class WebcralwerPipeline:
    @staticmethod
    def process_item(item, spider):
        print("Processing item in pipeline:", item)
        return item


class CreateDatabasePostgresPipeline:
    def __init__(self):
        # Connect to the PostgresSQL database
        connection = psycopg2.connect(
            host='localhost',
            user='docker',
            password='docker',
            database='crawler_db'
        )

        cursor = connection.cursor()

        # Create Products table if none exists
        cursor.execute("""
              CREATE TABLE IF NOT EXISTS Products(
              id TEXT PRIMARY KEY, 
              image_url TEXT,
              name1 TEXT,
              name2 TEXT,
              more_info_url TEXT,
              price FLOAT,
              price_text TEXT,
              shop_text TEXT
               )
               """)

        # Create Seller if none exits
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Sellers(
                     id SERIAL PRIMARY KEY,
                     name TEXT,
                     city TEXT
                      )
                    """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ProductSellerDetails(
                id SERIAL PRIMARY KEY,
                name1 TEXT,
                name2 TEXT,
                shop_name TEXT,
                shop_name2 TEXT,
                price FLOAT,
                price_text TEXT,
                last_price_change_date DATE,
                page_url TEXT,
                product_id TEXT REFERENCES Products(id),
                seller_id INTEGER REFERENCES Sellers(id)
            )
        """)

    def close_spider(self, spider):
        # Close cursor & connection to database
        print("***************Closing spider***************")
        cursor.close()
        connection.close()


class InsetIntoDatabasePostgresPipeline:
    def __init__(self):
        # Connect to the database
        self.engine = create_engine('postgresql://docker:docker@localhost/crawler_db')
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_item(self, item, spider):
        session = self.Session()
        print("Processing item type:", type(item))
        try:
            if isinstance(item, Product):
                print("Product item:", item['id'], item['name1'], item['name2'])
                product = DatabaseProduct(
                    id=item['id'],
                    image_url=item['image_url'],
                    name1=item['name1'],
                    name2=item['name2'],
                    more_info_url=item['more_info_url'],
                    price=item['price'],
                    price_text=item['price_text'],
                    shop_text=item['shop_text']
                )
                session.add(product)
                session.commit()
                psds = item['product_seller_details']

                if psds is not None:
                    for psd in psds:
                        
                        seller = psd['seller']

                        if seller is not None:
                            seller = DatabaseSeller(
                                id=seller['id'],
                                name=seller['name'],
                                city=seller['city']
                            )
                            session.add(seller)
                            session.commit()

                        product_seller_detail = DatabaseProductSellerDetails(
                            name1=psd['name1'],
                            name2=psd['name2'],
                            shop_name=psd['shop_name'],
                            shop_city=psd['shop_city'],
                            price=psd['price'],
                            price_text=psd['price_text'],
                            last_price_change_date=psd['last_price_change_date'],
                            page_url=psd['page_url'],
                            seller_id=psd['seller_id'],
                            product_id=psd['product_id']
                        )
                        session.add(product_seller_detail)
                        session.commit()


            # elif isinstance(item, ProductSellerDetails):
            #     print("ProductSellerDetails item:", item['name1'], item['shop_name'])
            #     product_seller_detail = DatabaseProductSellerDetails(
            #         name1=item['name1'],
            #         name2=item['name2'],
            #         shop_name=item['shop_name'],
            #         shop_city=item['shop_name2'],
            #         price=item['price'],
            #         price_text=item['price_text'],
            #         last_price_change_date=item['last_price_change_date'],
            #         page_url=item['page_url'],
            #         seller_id=item['seller_id'],
            #         product_id=item['product_id']
            #     )
            #     session.add(product_seller_detail)
            #     session.commit()
            # elif isinstance(item, Seller):
            #     print("Seller item:", item['id'], item['name'], item['city'])
            #     seller = DatabaseSeller(
            #         id=item['id'],
            #         name=item['name'],
            #         city=item['city']
            #     )
            #     session.add(seller)
            #     session.commit()
            else:
                print("Unknown item type:", type(item))

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

        return item
