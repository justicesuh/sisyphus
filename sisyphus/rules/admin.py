from django.contrib import admin

from sisyphus.rules.models import Rule, RuleCondition, RuleMatch


class RuleConditionInline(admin.TabularInline):  # type: ignore[type-arg]
    model = RuleCondition
    extra = 1


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ['name', 'user', 'is_active', 'match_mode', 'target_status', 'priority']  # noqa: RUF012
    list_filter = ['is_active', 'match_mode', 'target_status']  # noqa: RUF012
    search_fields = ['name']  # noqa: RUF012
    ordering = ['-priority', 'name']  # noqa: RUF012
    inlines = [RuleConditionInline]  # noqa: RUF012


@admin.register(RuleCondition)
class RuleConditionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ['rule', 'field', 'match_type', 'value', 'case_sensitive']  # noqa: RUF012
    list_filter = ['field', 'match_type', 'case_sensitive']  # noqa: RUF012
    search_fields = ['value', 'rule__name']  # noqa: RUF012


@admin.register(RuleMatch)
class RuleMatchAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ['rule', 'job', 'old_status', 'new_status', 'created_at']  # noqa: RUF012
    list_filter = ['old_status', 'new_status']  # noqa: RUF012
    search_fields = ['rule__name', 'job__title']  # noqa: RUF012
    ordering = ['-created_at']  # noqa: RUF012
