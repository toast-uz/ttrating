import json
import dataclasses


# Common Dataclass with serializer
class DataclassList(list):
    @classmethod
    def read_json(cls, filename, data_type=object):
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


@dataclasses.dataclass(order=True)
class Tournament:
    fm: str = ''
    to: str = ''
    id: str = ''
    year: str = dataclasses.field(repr=True, compare=False, default='')
    type: str = dataclasses.field(repr=True, compare=False, default='')
    name: str = dataclasses.field(repr=False, compare=False, default='')


class Tournaments(DataclassList):
    @classmethod
    def read_json(cls, filename):
        return Tournaments(DataclassList.read_json(filename, Tournament))
