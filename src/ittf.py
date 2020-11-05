import json
import dataclasses
from dataclasses import field


# Common Dataclass with serializer
class DataclassList(list):
    @classmethod
    def read_json(cls, filename, data_type):
        result = []
        with open(filename, mode='r', encoding='utf-8') as f:
            json_data = json.load(f)
            for o in json_data:
                result.append(data_type(** o))
        return DataclassList(result)

    class DataclassJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)

    def to_json(self, filename):
        with open(filename, mode='w', encoding='utf-8') as f:
            json.dump(self, f, ensure_ascii=False, indent=4,
                      cls=self.DataclassJSONEncoder)

    # Common function from attr:value to a self=list content.
    # - Throw exception if the attr:value is not exist.
    # - Throw exception if the attr:value is duplicated.
    def _content_by_attr(self, attr, value):
        result_list = [x for x in self if getattr(x, attr) == value]
        assert len(result_list) == 1
        return result_list[0] if result_list else None

    def by_id(self, id):
        return self._content_by_attr('id', id)

    def by_name(self, name):
        return self._content_by_attr('name', name)


@dataclasses.dataclass()
class Tournament:
    id: str = ''
    fm: str = field(compare=False, default='')
    to: str = field(compare=False, default='')
    year: str = field(compare=False, default='')
    type: str = field(compare=False, default='')
    name: str = field(repr=False, compare=False, default='')


class Tournaments(DataclassList):
    @classmethod
    def read_json(cls, filename):
        return Tournaments(DataclassList.read_json(filename, Tournament))


@dataclasses.dataclass()
class Player:
    id: str = ''
    name: str = field(compare=False, default='')
    nameJa: str = field(compare=False, default='')
    country: str = field(compare=False, default='')
    rank: int = field(compare=False, default=0)
    rating: float = field(compare=False, default=1500)
    wins: int = field(compare=False, default=0)
    loses: int = field(compare=False, default=0)
    points: int = field(repr=False, compare=False, default=0)
    points_EMA: int = field(repr=False, compare=False, default=-1)
    rating_EMA: float = field(repr=False, compare=False, default=-1)
    rating_china: float = field(repr=False, compare=False, default=1500)
    rating_china_EMA: float = field(repr=False, compare=False, default=-1)
    wins_china: int = field(repr=False, compare=False, default=0)
    loses_china: int = field(repr=False, compare=False, default=0)
    tournaments: dict = field(repr=False, compare=False, default_factory=dict)
    tournaments_last_update: str = field(
        repr=False, compare=False, default='2000-01-01')


class Players(DataclassList):
    @classmethod
    def read_json(cls, filename):
        return Players(DataclassList.read_json(filename, Player))
