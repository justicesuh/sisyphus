import re

from django.db import models
from django.utils.translation import gettext_lazy as _

from sisyphus.accounts.models import UserProfile
from sisyphus.core.models import UUIDModel
from sisyphus.jobs.models import Job


class Rule(UUIDModel):
    class MatchMode(models.TextChoices):
        ALL = 'all', _('All conditions must match')
        ANY = 'any', _('Any condition matches')

    user = models.ForeignKey(UserProfile, related_name='rules', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    match_mode = models.CharField(max_length=3, choices=MatchMode.choices, default=MatchMode.ALL)
    target_status = models.CharField(max_length=12, choices=Job.Status.choices, default=Job.Status.FILTERED)
    priority = models.PositiveIntegerField(default=0, help_text=_('Higher priority rules are evaluated first'))

    class Meta:
        ordering = ['-priority', 'name']

    def __str__(self):
        return self.name

    def matches(self, job):
        conditions = self.conditions.all()
        if not conditions:
            return False

        if self.match_mode == self.MatchMode.ALL:
            return all(condition.matches(job) for condition in conditions)
        return any(condition.matches(job) for condition in conditions)

    @classmethod
    def find_duplicate(cls, user, match_mode, target_status, conditions, exclude_rule=None):
        """Find an existing rule with the same settings and conditions.

        Args:
            user: UserProfile instance
            match_mode: Rule.MatchMode value
            target_status: Job.Status value
            conditions: List of dicts with 'field', 'match_type', 'value' keys
            exclude_rule: Optional Rule instance to exclude (for edits)

        Returns:
            Rule instance if duplicate found, None otherwise

        """
        queryset = cls.objects.filter(
            user=user,
            match_mode=match_mode,
            target_status=target_status,
        )

        if exclude_rule:
            queryset = queryset.exclude(pk=exclude_rule.pk)

        # Normalize conditions for comparison
        condition_set = frozenset((c['field'], c['match_type'], c['value']) for c in conditions)

        for rule in queryset.prefetch_related('conditions'):
            rule_conditions = frozenset((c.field, c.match_type, c.value) for c in rule.conditions.all())
            if rule_conditions == condition_set:
                return rule

        return None


class RuleCondition(UUIDModel):
    class Field(models.TextChoices):
        TITLE = 'title', _('Title')
        DESCRIPTION = 'description', _('Description')
        COMPANY = 'company', _('Company')
        LOCATION = 'location', _('Location')
        URL = 'url', _('URL')

    class MatchType(models.TextChoices):
        CONTAINS = 'contains', _('Contains')
        EXACT = 'exact', _('Exact match')
        REGEX = 'regex', _('Regular expression')
        NOT_CONTAINS = 'not_contains', _('Does not contain')

    rule = models.ForeignKey(Rule, related_name='conditions', on_delete=models.CASCADE)
    field = models.CharField(max_length=11, choices=Field.choices)
    match_type = models.CharField(max_length=12, choices=MatchType.choices, default=MatchType.CONTAINS)
    value = models.CharField(max_length=500)
    case_sensitive = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.get_field_display()} {self.get_match_type_display()} "{self.value}"'

    def _get_field_value(self, job):
        if self.field == self.Field.TITLE:
            return job.title or ''
        if self.field == self.Field.DESCRIPTION:
            return job.description or ''
        if self.field == self.Field.COMPANY:
            return job.company.name if job.company else ''
        if self.field == self.Field.LOCATION:
            return job.location.name if job.location else ''
        if self.field == self.Field.URL:
            return job.url or ''
        return ''

    def matches(self, job):
        field_value = self._get_field_value(job)
        pattern = self.value

        # Always case-insensitive for non-regex matches
        if self.match_type != self.MatchType.REGEX:
            field_value = field_value.lower()
            pattern = pattern.lower()

        if self.match_type == self.MatchType.CONTAINS:
            return pattern in field_value
        if self.match_type == self.MatchType.EXACT:
            return pattern == field_value
        if self.match_type == self.MatchType.REGEX:
            try:
                return bool(re.search(pattern, field_value, re.IGNORECASE))
            except re.error:
                return False
        elif self.match_type == self.MatchType.NOT_CONTAINS:
            return pattern not in field_value

        return False


class RuleMatch(UUIDModel):
    rule = models.ForeignKey(Rule, related_name='match_history', on_delete=models.CASCADE)
    job = models.ForeignKey(Job, related_name='rule_matches', on_delete=models.CASCADE)
    old_status = models.CharField(max_length=12, choices=Job.Status.choices)
    new_status = models.CharField(max_length=12, choices=Job.Status.choices)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rule.name} matched {self.job.title}'
