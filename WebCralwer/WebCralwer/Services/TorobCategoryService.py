from WebCralwer.DataAccess.Models.Torob.TorobModels import TorobCategory


# Represents a torob category service
class TorobCategoryService:
    def __init__(self, repository):
        self._repository = repository

    def get_all_items(self):
        return self._repository.get_all()

    def get_item_by_id(self, id):
        return self._repository.get_by_id(id)

    def create_item(self, item: TorobCategory):
        return self._repository.create(item)
