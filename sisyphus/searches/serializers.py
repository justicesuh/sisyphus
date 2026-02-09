from rest_framework import serializers

from sisyphus.searches.models import Search, SearchRun


class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = (
            'uuid', 'keywords', 'location', 'source',
            'easy_apply', 'is_hybrid', 'is_onsite', 'is_remote',
            'is_active', 'schedule', 'status', 'last_executed_at',
            'created_at', 'updated_at',
        )
        read_only_fields = ('uuid', 'status', 'last_executed_at', 'created_at', 'updated_at')


class SearchRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchRun
        fields = (
            'uuid', 'status', 'period',
            'started_at', 'completed_at',
            'jobs_found', 'jobs_created',
            'error_message',
        )
