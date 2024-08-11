from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean
from datetime import datetime


# Represents user model
class UserModel(db.Model):
    __tablename__ = 'users'
    id = Column(db.Integer, primary_key=True)
    username = Column(db.String(120), unique=True, nullable=False)
    password = Column(db.String(120), nullable=False)
