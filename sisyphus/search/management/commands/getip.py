from django.core.management.base import BaseCommand, CommandError

from sisyphus.search.parsers.base import IPParser


class Command(BaseCommand):
    def handle(self, **options):
        parser = IPParser()
        ip = parser.parse()
        if ip is not None:
            self.stdout.write(self.style.SUCCESS(ip))
        else:
            raise CommandError('IP not found.')
        parser.quit()
