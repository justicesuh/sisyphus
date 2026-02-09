"""Add filter rules via the API."""

import json
import sys

import requests

if len(sys.argv) != 4:
    print(f'Usage: {sys.argv[0]} <email> <password> <rules.json>')
    sys.exit(1)

email, password, rules_file = sys.argv[1], sys.argv[2], sys.argv[3]

with open(rules_file) as f:
    rules_data = json.load(f)

BASE_URL = 'http://localhost:8000'

# Authenticate
response = requests.post(f'{BASE_URL}/api/token/', json={'email': email, 'password': password})
if response.status_code != 200:
    print(f'Login failed: {response.status_code}')
    sys.exit(1)

token = response.json()['access']
headers = {'Authorization': f'Bearer {token}'}


def add_rule(term, status='filtered'):
    data = {
        'name': term,
        'match_mode': 'all',
        'target_status': status,
        'priority': 0 if status == 'filtered' else 10,
        'conditions': [
            {'field': 'title', 'match_type': 'contains', 'value': term, 'case_sensitive': False},
        ],
    }
    resp = requests.post(f'{BASE_URL}/rules/api/', json=data, headers=headers)
    if resp.status_code == 201:
        print(f'  Created: {data["name"]}')
    else:
        print(f'  Failed ({resp.status_code}): {data["name"]} - {resp.text}')


for status, terms in rules_data.items():
    print(f'Adding {status} rules...')
    for term in terms:
        add_rule(term, status)

print('Done.')
