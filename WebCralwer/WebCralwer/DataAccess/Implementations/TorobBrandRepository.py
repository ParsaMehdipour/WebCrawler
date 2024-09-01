from ..Interfaces.IRepository import IRepository
from WebCralwer.DataAccess.Models.Torob.TorobModels import TorobBrand
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Represents a torob brand repository
class TorobBrandRepository(IRepository):
    def __init__(self, connection_string):
        self._engine = create_engine(connection_string)
        self._Session = sessionmaker(bind=self._engine)

    def get_all(self):
        session = self._Session()
        try:
            results = session.query(TorobBrand).all()
            return results
        finally:
            session.close()

    def get_by_id(self, id):
        session = self._Session()
        try:
            result = session.query(TorobBrand).filter(TorobBrand.id == id).first()
            return result
        finally:
            session.close()

    def create(self, item: TorobBrand):
        session = self._Session()
        try:
            session.add(item)
            session.commit()
            session.refresh(item)
            return item
        finally:
            session.close()

