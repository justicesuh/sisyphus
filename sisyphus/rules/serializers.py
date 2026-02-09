from rest_framework import serializers

from sisyphus.rules.models import Rule, RuleCondition


class RuleConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleCondition
        fields = ('uuid', 'field', 'match_type', 'value', 'case_sensitive')
        read_only_fields = ('uuid',)


class RuleSerializer(serializers.ModelSerializer):
    conditions = RuleConditionSerializer(many=True)

    class Meta:
        model = Rule
        fields = ('uuid', 'name', 'is_active', 'match_mode', 'target_status', 'priority', 'conditions', 'created_at', 'updated_at')
        read_only_fields = ('uuid', 'created_at', 'updated_at')

    def validate(self, data):
        user = self.context['request'].user.profile
        conditions = [
            {'field': c['field'], 'match_type': c['match_type'], 'value': c['value']}
            for c in data.get('conditions', [])
        ]
        duplicate = Rule.find_duplicate(
            user=user,
            match_mode=data.get('match_mode', Rule.MatchMode.ALL),
            target_status=data.get('target_status', ''),
            conditions=conditions,
            exclude_rule=self.instance,
        )
        if duplicate:
            raise serializers.ValidationError(f'A rule with these settings already exists: "{duplicate.name}"')
        return data

    def create(self, validated_data):
        conditions_data = validated_data.pop('conditions')
        rule = Rule.objects.create(**validated_data)
        for condition in conditions_data:
            RuleCondition.objects.create(rule=rule, **condition)
        return rule

    def update(self, instance, validated_data):
        conditions_data = validated_data.pop('conditions')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        instance.conditions.all().delete()
        for condition in conditions_data:
            RuleCondition.objects.create(rule=instance, **condition)

        return instance
