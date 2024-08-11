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
