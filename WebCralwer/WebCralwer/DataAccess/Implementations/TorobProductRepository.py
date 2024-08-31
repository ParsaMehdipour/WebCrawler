from DataAccess.Interfaces.IRepository import IRepository
from DataAccess.Models.Torob.TorobProduct import TorobProduct


# Represents a torob product repository
class TorobProductRepository(IRepository):
    def __init__(self, connection_string):
        # initialize database connection
        self._connection_string = connection_string
        self._connection = db.connect(connection_string)

    def get_all(self):
        # query all records from database
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM torob_products")
        results = cursor.fetchall()
        return results

    def get_by_id(self, id):
        # query record by id from database
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM torob_products WHERE id=?", (id,))
        result = cursor.fetchone()
        return result if result is not None else None

    def create(self, item: TorobProduct):
        # insert record into database
        cursor = self._connection.cursor()
        cursor.execute("INSERT INTO torob_products(image_url,"
                       " name1,"
                       " name2,"
                       " more_info_url,"
                       " price,"
                       " price_text,"
                       " shop_text,"
                       " is_stock,"
                       " category_name,"
                       " brand_name,"
                       " created_on ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (item['image_url'],
                        item['name1'],
                        item['name2'],
                        item['more_info_url'],
                        item['price'],
                        item['price_text'],
                        item['shop_text'],
                        item['is_stock'],
                        item['category_name'],
                        item['brand_name'],
                        item['created_on']))
        self._connection.commit()
        item['id'] = cursor.lastrowid
        return item
