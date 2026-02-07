import pytest

from sisyphus.jobs.models import Job
from sisyphus.rules.models import Rule, RuleCondition, RuleMatch


class TestRule:
    """Tests for the Rule model."""

    def test_str(self, user_profile):
        rule = Rule.objects.create(user=user_profile, name='Filter Interns')
        assert str(rule) == 'Filter Interns'

    def test_matches_all_mode(self, user_profile, job_with_description):
        rule = Rule.objects.create(user=user_profile, name='Test Rule', match_mode=Rule.MatchMode.ALL)
        RuleCondition.objects.create(rule=rule, field='title', match_type='contains', value='Senior')
        RuleCondition.objects.create(rule=rule, field='description', match_type='contains', value='Python')
        assert rule.matches(job_with_description)

    def test_matches_any_mode(self, user_profile, job_with_description):
        rule = Rule.objects.create(user=user_profile, name='Test Rule', match_mode=Rule.MatchMode.ANY)
        RuleCondition.objects.create(rule=rule, field='title', match_type='contains', value='Nonexistent')
        RuleCondition.objects.create(rule=rule, field='description', match_type='contains', value='Python')
        assert rule.matches(job_with_description)

    def test_no_conditions_returns_false(self, user_profile, job_with_description):
        rule = Rule.objects.create(user=user_profile, name='Empty Rule')
        assert not rule.matches(job_with_description)

    def test_find_duplicate(self, user_profile):
        rule = Rule.objects.create(
            user=user_profile, name='Existing', match_mode=Rule.MatchMode.ALL, target_status=Job.Status.FILTERED
        )
        RuleCondition.objects.create(rule=rule, field='title', match_type='contains', value='intern')

        conditions = [{'field': 'title', 'match_type': 'contains', 'value': 'intern'}]
        duplicate = Rule.find_duplicate(user_profile, Rule.MatchMode.ALL, Job.Status.FILTERED, conditions)
        assert duplicate == rule

    def test_find_duplicate_none(self, user_profile):
        conditions = [{'field': 'title', 'match_type': 'contains', 'value': 'intern'}]
        duplicate = Rule.find_duplicate(user_profile, Rule.MatchMode.ALL, Job.Status.FILTERED, conditions)
        assert duplicate is None


class TestRuleCondition:
    """Tests for the RuleCondition model."""

    def test_str(self, user_profile):
        rule = Rule.objects.create(user=user_profile, name='Test Rule')
        cond = RuleCondition.objects.create(rule=rule, field='title', match_type='contains', value='intern')
        assert str(cond) == 'Title Contains "intern"'

    def test_matches_contains(self, user_profile, job):
        rule = Rule.objects.create(user=user_profile, name='Test')
        cond = RuleCondition.objects.create(rule=rule, field='title', match_type='contains', value='Software')
        assert cond.matches(job)

    def test_matches_exact(self, user_profile, job):
        rule = Rule.objects.create(user=user_profile, name='Test')
        cond = RuleCondition.objects.create(rule=rule, field='title', match_type='exact', value='Software Engineer')
        assert cond.matches(job)

    def test_matches_regex(self, user_profile, job):
        rule = Rule.objects.create(user=user_profile, name='Test')
        cond = RuleCondition.objects.create(rule=rule, field='title', match_type='regex', value=r'Software\s+Engineer')
        assert cond.matches(job)

    def test_matches_not_contains(self, user_profile, job):
        rule = Rule.objects.create(user=user_profile, name='Test')
        cond = RuleCondition.objects.create(rule=rule, field='title', match_type='not_contains', value='Manager')
        assert cond.matches(job)

    def test_invalid_regex_returns_false(self, user_profile, job):
        rule = Rule.objects.create(user=user_profile, name='Test')
        cond = RuleCondition.objects.create(rule=rule, field='title', match_type='regex', value='[invalid')
        assert not cond.matches(job)

    def test_field_value_company(self, user_profile, job):
        rule = Rule.objects.create(user=user_profile, name='Test')
        cond = RuleCondition.objects.create(rule=rule, field='company', match_type='contains', value='Test')
        assert cond.matches(job)

    def test_field_value_location(self, user_profile, job_with_description):
        rule = Rule.objects.create(user=user_profile, name='Test')
        cond = RuleCondition.objects.create(rule=rule, field='location', match_type='contains', value='New York')
        assert cond.matches(job_with_description)

    def test_field_value_url(self, user_profile, job):
        rule = Rule.objects.create(user=user_profile, name='Test')
        cond = RuleCondition.objects.create(rule=rule, field='url', match_type='contains', value='test.com')
        assert cond.matches(job)


class TestRuleMatch:
    """Tests for the RuleMatch model."""

    def test_str(self, user_profile, job):
        rule = Rule.objects.create(user=user_profile, name='My Rule')
        match = RuleMatch.objects.create(rule=rule, job=job, old_status=Job.Status.NEW, new_status=Job.Status.FILTERED)
        assert str(match) == 'My Rule matched Software Engineer'
