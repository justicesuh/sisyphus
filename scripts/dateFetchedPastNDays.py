import base64
import json
from argparse import ArgumentParser
from urllib.parse import unquote


def main():
    parser = ArgumentParser()
    parser.add_argument('state')
    args = parser.parse_args()
    data = json.loads(unquote(base64.b64decode(args.state)))
    print(data['dateFetchedPastNDays'])


if __name__ == '__main__':
    main()
