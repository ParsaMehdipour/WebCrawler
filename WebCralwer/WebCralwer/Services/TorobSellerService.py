from DataAccess.Models.Torob.TorobSeller import TorobSeller


# Represents a torob seller service
class TorobSellerService:
    def __init__(self, repository):
        self._repository = repository

    def get_all_items(self):
        return self._repository.get_all()

    def get_item_by_id(self, id):
        return self._repository.get_by_id(id)

    def create_item(self, item: TorobSeller):
        return self._repository.create(item)
