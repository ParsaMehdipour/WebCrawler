from ..Interfaces.IRepository import IRepository
from ..Models.Torob.TorobProductSellerDetails import TorobProductSellerDetails


# Represents a torob product seller details repository
class TorobProductSellerDetailsRepository(IRepository):
    def __init__(self, connection_string):
        # initialize database connection
        self._connection_string = connection_string
        self._connection = db.connect(connection_string)

    def get_all(self):
        # query all records from database
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM torob_product_seller_details")
        results = cursor.fetchall()
        return results

    def get_by_id(self, id):
        # query record by id from database
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM torob_product_seller_details WHERE id=?", (id,))
        result = cursor.fetchone()
        return result if result is not None else None

    def create(self, item: TorobProductSellerDetails):
        # insert record into database
        cursor = self._connection.cursor()
        cursor.execute("INSERT INTO torob_product_seller_details( name1,"
                       " name2,"
                       " shop_name,"
                       " shop_city,"
                       " price,"
                       " price_text,"
                       " last_price_change_date,"
                       " page_url,"
                       " is_stock,"
                       " cretaed_on,"
                       " seller_id,"
                       " product_id ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (item['name1'],
                        item['name2'],
                        item['shop_name'],
                        item['shop_city'],
                        item['price'],
                        item['price_text'],
                        item['last_price_change_date'],
                        item['page_url'],
                        item['is_stock'],
                        item['cretaed_on'],
                        item['seller_id'],
                        item['product_id']))
        self._connection.commit()
        item['id'] = cursor.lastrowid
        return item
