from DataAccess.Interfaces.IRepository import IRepository
from DataAccess.Models.Torob.TorobSeller import TorobSeller


# Represents a torob seller repository
class TorobSellerRepository(IRepository):
    def __init__(self, connection_string):
        # initialize database connection
        self._connection_string = connection_string
        self._connection = db.connect(connection_string)

    def get_all(self):
        # query all records from database
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM torob_sellers")
        results = cursor.fetchall()
        return results

    def get_by_id(self, id):
        # query record by id from database
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM torob_sellers WHERE id=?", (id,))
        result = cursor.fetchone()
        return result if result is not None else None

    def create(self, item: TorobSeller):
        # insert record into database
        cursor = self._connection.cursor()
        cursor.execute("INSERT INTO torob_sellers(name,"
                       " city,"
                       " is_flagged,"
                       " created_on) VALUES (?, ?)",
                       (item['name'],
                        item['city'],
                        item['is_flagged'],
                        item['created_on']))
        self._connection.commit()
        item['id'] = cursor.lastrowid
        return item
