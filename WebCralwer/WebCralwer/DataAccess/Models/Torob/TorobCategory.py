from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Create the Base class
Base = declarative_base()

# Represent torob category database model
class TorobCategory(Base):
    __tablename__ = 'torob_categories'
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
