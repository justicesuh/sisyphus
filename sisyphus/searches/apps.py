from django.apps import AppConfig


class SearchesConfig(AppConfig):
    name = 'sisyphus.searches'

    def ready(self):
        from django.db.models.signals import post_delete, post_save  # noqa: PLC0415

        from sisyphus.searches.models import Search  # noqa: PLC0415

        def sync_schedule(sender, instance, **kwargs):
            instance.sync_schedule()

        def delete_schedule(sender, instance, **kwargs):
            from django_celery_beat.models import PeriodicTask  # noqa: PLC0415
            PeriodicTask.objects.filter(name=f'search-{instance.uuid}').delete()

        post_save.connect(sync_schedule, sender=Search)
        post_delete.connect(delete_schedule, sender=Search)
