import json
import random
import time
from catboost import CatBoostRegressor

class SingletonMeta(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class RealEstateModel(metaclass=SingletonMeta):
    name = 'real_estate'
    _features = (
        "land_type",
        "sewerage_type",
        "heating_type",
        "construction",
        "garage",
        "bathhouse",
        "swimming_pool",
        "security",
        "area",
        "land_area",
        "year",
        "lat",
        "lon",
    )

    def __init__(self):
        self._model = None

    def up(self):
        catboost_model = CatBoostRegressor()
        catboost_model.load_model('catboost_v1')
        self._model = catboost_model

    def prepare_data(self, data):
        data = json.loads(data)
        data = [data[name] for name in self._features]
        return data

    def process_result(self, result):
        return str(result)

    def run(self, data: dict) -> str:
        data = self.prepare_data(data)
        result = self._model.predict(data)
        return self.process_result(result)


model = RealEstateModel()
model.up()
