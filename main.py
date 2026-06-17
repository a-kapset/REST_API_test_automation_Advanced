# curl -X 'POST' \
#   'http://185.185.143.231:5051/v1/account' \
#   -H 'accept: */*' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "login": "a1",
#   "email": "a1@test.com",
#   "password": "qwerty123"
# }'


import requests
import pprint

url = 'http://185.185.143.231:5051/v1/account'

headers = {
    'accept': '*/*',
    'Content-Type': 'application/json'
}

json = {
    "login": "a2",
    "email": "a2@test.com",
    "password": "qwerty123"
}

response = requests.post(
    url=url,
    headers=headers,
    json=json
)

print(response.status_code)
# pprint.pprint(response.json())