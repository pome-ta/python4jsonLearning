import json
import pathlib

from pprint import pprint

json_path = pathlib.Path('./data/sample02.json')
with json_path.open(mode='r', encoding='utf_8') as f:
  #print(f)
  obj_json = json.load(f)

#pprint(obj_json)

dmp_json = json.dumps(obj_json)

loads_json = json.loads(dmp_json)

