from DataAccess.Interfaces.IRepository import IRepository
from DataAccess.Models.Torob.TorobModels import TorobProduct
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Represents a torob product repository
class TorobProductRepository(IRepository):
    def __init__(self, connection_string):
        self._engine = create_engine(connection_string)
        self._Session = sessionmaker(bind=self._engine)

    def get_all(self):
        session = self._Session()
        try:
            results = session.query(TorobProduct).all()
            return results
        finally:
            session.close()

    def get_by_id(self, id):
        session = self._Session()
        try:
            result = session.query(TorobProduct).filter(TorobProduct.id == id).first()
            return result
        finally:
            session.close()

    def create(self, item: TorobProduct):
        session = self._Session()
        try:
            session.add(item)
            session.commit()
            session.refresh(item)
            return item
        finally:
            session.close()