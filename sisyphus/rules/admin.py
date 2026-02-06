from typing import ClassVar

from django.contrib import admin

from sisyphus.rules.models import Rule, RuleCondition, RuleMatch


class RuleConditionInline(admin.TabularInline):
    model = RuleCondition
    extra = 1


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ['name', 'user', 'is_active', 'match_mode', 'target_status', 'priority']
    list_filter: ClassVar[list[str]] = ['is_active', 'match_mode', 'target_status']
    search_fields: ClassVar[list[str]] = ['name']
    ordering: ClassVar[list[str]] = ['-priority', 'name']
    inlines: ClassVar[list[type]] = [RuleConditionInline]


@admin.register(RuleCondition)
class RuleConditionAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ['rule', 'field', 'match_type', 'value', 'case_sensitive']
    list_filter: ClassVar[list[str]] = ['field', 'match_type', 'case_sensitive']
    search_fields: ClassVar[list[str]] = ['value', 'rule__name']


@admin.register(RuleMatch)
class RuleMatchAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ['rule', 'job', 'old_status', 'new_status', 'created_at']
    list_filter: ClassVar[list[str]] = ['old_status', 'new_status']
    search_fields: ClassVar[list[str]] = ['rule__name', 'job__title']
    ordering: ClassVar[list[str]] = ['-created_at']
