from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Create the Base class
Base = declarative_base()

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
