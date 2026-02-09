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
