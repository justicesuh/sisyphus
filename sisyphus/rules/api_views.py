from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from sisyphus.accounts.models import UserProfile
from sisyphus.rules.models import Rule
from sisyphus.rules.serializers import RuleSerializer


class RuleViewSet(ModelViewSet):
    serializer_class = RuleSerializer
    lookup_field = 'uuid'

    def get_profile(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_queryset(self):
        return Rule.objects.filter(user=self.get_profile()).prefetch_related('conditions')

    def perform_create(self, serializer):
        serializer.save(user=self.get_profile())

    @action(detail=True, methods=['post'])
    def toggle(self, request, uuid=None):
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save(update_fields=['is_active'])
        return Response(RuleSerializer(rule).data)

    @action(detail=True, methods=['post'])
    def apply(self, request, uuid=None):
        rule = self.get_object()
        from sisyphus.rules.tasks import apply_rule_to_existing_jobs  # noqa: PLC0415

        apply_rule_to_existing_jobs.delay(rule.id)
        return Response({'status': 'queued'})

    @action(detail=False, methods=['post'], url_path='apply-all')
    def apply_all(self, request):
        from sisyphus.rules.tasks import apply_all_rules  # noqa: PLC0415

        profile = self.get_profile()
        apply_all_rules.delay(profile.id)
        return Response({'status': 'queued'})
