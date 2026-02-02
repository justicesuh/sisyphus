#!/bin/sh

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <email> <password>"
    exit 1
fi

docker exec -it sisyphus_django uv run manage.py shell -c "
from sisyphus.accounts.models import User
if not User.objects.filter(email='$1').exists():
    User.objects.create_superuser('$1', '$2')
else:
    print('User with that email already exists.')
"
