from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from sisyphus.accounts.models import UserProfile
from sisyphus.searches.models import Search
from sisyphus.searches.serializers import SearchRunSerializer, SearchSerializer


class SearchViewSet(ModelViewSet):
    serializer_class = SearchSerializer
    lookup_field = 'uuid'

    def get_profile(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_queryset(self):
        return Search.objects.filter(user=self.get_profile()).select_related('source', 'location')

    def perform_create(self, serializer):
        search = serializer.save(user=self.get_profile())
        search.sync_schedule()

    def perform_update(self, serializer):
        search = serializer.save()
        search.sync_schedule()

    def perform_destroy(self, instance):
        from django_celery_beat.models import PeriodicTask  # noqa: PLC0415
        PeriodicTask.objects.filter(name=f'search-{instance.uuid}').delete()
        instance.delete()

    @action(detail=True, methods=['post'])
    def toggle(self, request, uuid=None):
        search = self.get_object()
        search.is_active = not search.is_active
        search.save(update_fields=['is_active'])
        search.sync_schedule()
        return Response(SearchSerializer(search).data)

    @action(detail=True, methods=['post'])
    def execute(self, request, uuid=None):
        search = self.get_object()
        from sisyphus.searches.tasks import execute_search  # noqa: PLC0415

        execute_search.delay(search.id, self.get_profile().id)
        search.set_status(Search.Status.QUEUED)
        return Response({'status': 'queued'})

    @action(detail=True, methods=['get'])
    def runs(self, request, uuid=None):
        search = self.get_object()
        runs = search.runs.all()[:25]
        return Response(SearchRunSerializer(runs, many=True).data)
