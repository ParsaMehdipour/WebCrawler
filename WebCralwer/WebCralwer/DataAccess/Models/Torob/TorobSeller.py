from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Create the Base class
Base = declarative_base()

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
