class TorobStructuredProductDto:
    def __init__(self, name1, name2, category_name, brand_name, price, price_text, created_on, is_stock, psd_id, seller_name,
                 seller_city, image_url):
        self.name1 = name1
        self.name2 = name2
        self.category_name = category_name
        self.brand_name = brand_name
        self.price = price
        self.price_text = price_text
        self.created_on = created_on
        self.is_stock = is_stock
        self.psd_id = psd_id
        self.seller_name = seller_name
        self.seller_city = seller_city
        self.image_url = image_url

    def to_json(self):
        return {
            'name1': self.name1,
            'name2': self.name2,
            'category_name': self.category_name,
            'brand_name': self.brand_name,
            'price': self.price,
            'price_text': self.price_text,
            'created_on': self.created_on,
            'is_stock': self.is_stock,
            'psd_id': self.psd_id,
            'seller_name': self.seller_name,
            'seller_city': self.seller_city,
            'image_url': self.image_url
        }