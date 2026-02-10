from rest_framework import serializers

from sisyphus.jobs.models import Location
from sisyphus.searches.models import Search, SearchRun, Source


class SearchSerializer(serializers.ModelSerializer):
    source = serializers.SlugRelatedField(slug_field='name', queryset=Source.objects.all())
    location = serializers.SlugRelatedField(slug_field='name', queryset=Location.objects.all())

    class Meta:
        model = Search
        fields = (
            'uuid', 'keywords', 'location', 'source',
            'easy_apply', 'is_hybrid', 'is_onsite', 'is_remote',
            'is_active', 'schedule', 'status', 'last_executed_at',
            'created_at', 'updated_at',
        )
        read_only_fields = ('uuid', 'status', 'last_executed_at', 'created_at', 'updated_at')

    def validate(self, data):
        user = self.context['request'].user.profile
        duplicate = Search.find_duplicate(
            user=user,
            keywords=data.get('keywords', ''),
            source=data.get('source'),
            location=data.get('location'),
            easy_apply=data.get('easy_apply', False),
            exclude_search=self.instance,
        )
        if duplicate:
            raise serializers.ValidationError(
                f'A search with these keywords, source, and location already exists: "{duplicate.keywords}"'
            )
        return data


class SearchRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchRun
        fields = (
            'uuid', 'status', 'period',
            'started_at', 'completed_at',
            'jobs_found', 'jobs_created',
            'error_message',
        )
