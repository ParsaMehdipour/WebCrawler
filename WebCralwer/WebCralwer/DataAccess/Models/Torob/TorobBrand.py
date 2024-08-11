from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Create the Base class
Base = declarative_base()

# Represents torob brand database model
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
