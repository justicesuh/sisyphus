import json
import sys

import requests

if len(sys.argv) != 4:
    print(f'Usage: {sys.argv[0]} <email> <password> <searches.json>')
    sys.exit(1)

email, password, searches_file = sys.argv[1], sys.argv[2], sys.argv[3]

with open(searches_file) as f:
    searches_data = json.load(f)

BASE_URL = 'http://localhost:8000'

response = requests.post(f'{BASE_URL}/api/token/', json={'email': email, 'password': password})
if response.status_code != 200:
    print(f'Login failed: {response.stauts_code}')
    sys.exit(1)

token = response.json()['access']
headers = {'Authorization': f'Bearer {token}'}

def add_search(term):
    data = {
        'keywords': term,
        'is_hybrid': False,
        'is_onsite': False,
        'is_remote': True,
        'source': 'LinkedIn',
        'location': 'United States',
        'schedule': '0 0,12 * * *',
    }
    for easy_apply in [True, False]:
        data['easy_apply'] = easy_apply
        response = requests.post(f'{BASE_URL}/searches/api/', json=data, headers=headers)
        if response.status_code == 201:
            print(f'Created: {data["keywords"]} | Easy Apply: {easy_apply}')
        else:
            print(f'Failed ({response.status_code}): {data["keywords"]} | Easy Apply: {easy_apply} - {response.text}')

for term in searches_data['terms']:
    add_search(term)
