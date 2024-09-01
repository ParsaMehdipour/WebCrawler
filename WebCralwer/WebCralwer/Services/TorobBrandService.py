from DataAccess.Models.Torob.TorobModels import TorobBrand


# Represents a torob brand service
class TorobBrandService:
    def __init__(self, repository):
        self._repository = repository

    def get_all_items(self):
        return self._repository.get_all()

    def get_item_by_id(self, id):
        return self._repository.get_by_id(id)

    def create_item(self, item: TorobBrand):
        return self._repository.create(item)
