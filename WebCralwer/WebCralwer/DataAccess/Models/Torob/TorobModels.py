from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Create the Base class
Base = declarative_base()

# Represent torob product database model
class TorobProduct(Base):
    __tablename__ = 'torob_products'
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


# Represents torob product seller detail database model
class TorobProductSellerDetails(Base):
    __tablename__ = 'torob_product_seller_details'
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
    seller_id = Column(Integer, ForeignKey('torob_sellers.id'))
    product_id = Column(String, ForeignKey('torob_products.id'))
    product = relationship("TorobProduct")
    seller = relationship("TorobSeller")

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

# Represents torob seller database model
class TorobSeller(Base):
    __tablename__ = 'torob_sellers'
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


class TorobCategory(Base):
    __tablename__ = 'torob_categories'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    created_on = Column(DateTime, default=datetime.now)

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'created_on': self.created_on
        }


class TorobBrand(Base):
    __tablename__ = 'torob_brands'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    created_on = Column(DateTime, default=datetime.now)

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'created_on': self.created_on
        }
