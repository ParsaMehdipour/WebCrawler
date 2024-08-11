from DataAccess.Models.Torob.TorobProductSellerDetails import TorobProductSellerDetails


# Represents a torob product seller details service
class TorobProductSellerDetailsService:
    def __init__(self, repository):
        self._repository = repository

    def get_all_items(self):
        return self._repository.get_all()

    def get_item_by_id(self, id):
        return self._repository.get_by_id(id)

    def create_item(self, item: TorobProductSellerDetails):
        return self._repository.create(item)
