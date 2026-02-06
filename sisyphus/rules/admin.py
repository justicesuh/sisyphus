from django.contrib import admin

from sisyphus.rules.models import Rule, RuleCondition, RuleMatch


class RuleConditionInline(admin.TabularInline):  # type: ignore[type-arg]
    model = RuleCondition
    extra = 1


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('name', 'user', 'is_active', 'match_mode', 'target_status', 'priority')
    list_filter = ('is_active', 'match_mode', 'target_status')
    search_fields = ('name',)
    ordering = ('-priority', 'name')
    inlines = (RuleConditionInline,)


@admin.register(RuleCondition)
class RuleConditionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('rule', 'field', 'match_type', 'value', 'case_sensitive')
    list_filter = ('field', 'match_type', 'case_sensitive')
    search_fields = ('value', 'rule__name')


@admin.register(RuleMatch)
class RuleMatchAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('rule', 'job', 'old_status', 'new_status', 'created_at')
    list_filter = ('old_status', 'new_status')
    search_fields = ('rule__name', 'job__title')
    ordering = ('-created_at',)
