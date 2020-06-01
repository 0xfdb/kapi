import json
from pprint import pprint
from urllib import request

r = request.Request(
    "http://127.0.0.1:8989/nowplaying",
    headers={"Auth-Key": "qZu3vhYicbJA87Xq2bofnwQMyQ"},
    method="GET",
)

with request.urlopen(r) as res:
    pprint(json.loads(res.read()))
