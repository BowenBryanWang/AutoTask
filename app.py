import json
import requests

response = requests.post("http://166.111.139.119:12321/query", headers={
    'content-type': 'application/json',
}, data=json.dumps({
    'msg': "hello",
    'temp': 1,
}))
print(json.loads(response.text)['response'])
