import pathlib
import json

file_path = pathlib.Path('./test-data/large-file.json')
with file_path.open(encoding='utf_8') as f:
  data = json.load(f)

user_to_repos = {}
for record in data:
  user = record['actor']['login']
  repo = record['repo']['name']
  if user not in user_to_repos:
    user_to_repos[user] = set()
    user_to_repos[user].add(repo)
