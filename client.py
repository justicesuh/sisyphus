"""Simple script to test JWT authentication."""

import sys

import requests

if len(sys.argv) != 3:
    print(f'Usage: {sys.argv[0]} <email> <password>')
    sys.exit(1)

email, password = sys.argv[1], sys.argv[2]

BASE_URL = 'http://localhost:8000'

# Obtain tokens
response = requests.post(f'{BASE_URL}/api/token/', json={
    'email': email,
    'password': password,
})
print(f'Token: {response.status_code}')
tokens = response.json()
print(tokens)

# Refresh token
response = requests.post(f'{BASE_URL}/api/token/refresh/', json={
    'refresh': tokens['refresh'],
})
print(f'\nRefresh: {response.status_code}')
print(response.json())
