from django.apps import AppConfig


class RulesConfig(AppConfig):
    name = 'sisyphus.rules'

    def ready(self):
        import sisyphus.rules.signals  # noqa: F401
