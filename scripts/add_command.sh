#!/bin/sh

if [ $# -ne 2 ]; then
    echo "Usage: $0 <app_name> <command_name>"
    exit 1
fi

APP_NAME=$1
COMMAND_NAME=$2
APP_DIR="sisyphus/$APP_NAME"
COMMANDS_DIR="$APP_DIR/management/commands"

if [ ! -d "$APP_DIR" ]; then
    echo "Error: App '$APP_NAME' does not exist at $APP_DIR"
    exit 1
fi

mkdir -p "$COMMANDS_DIR"
touch "$APP_DIR/management/__init__.py"
touch "$COMMANDS_DIR/__init__.py"

COMMAND_FILE="$COMMANDS_DIR/$COMMAND_NAME.py"

if [ -f "$COMMAND_FILE" ]; then
    echo "Error: Command '$COMMAND_NAME' already exists at $COMMAND_FILE"
    exit 1
fi

cat > "$COMMAND_FILE" << 'EOF'
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        pass
EOF

sh ./scripts/recursive_chown.sh

echo "Created $COMMAND_FILE"
