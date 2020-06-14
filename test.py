import json
from pprint import pprint
from urllib import request

r = request.Request(
    "http://127.0.0.1:8989/search?title=ai%20rising",
    headers={"Auth-Key": "abc123"},
    method="GET",
)

with request.urlopen(r) as res:
    pprint(json.loads(res.read()))
