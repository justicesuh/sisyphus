import pytest

from sisyphus.jobs.models import Job
from sisyphus.rules.models import Rule, RuleCondition, RuleMatch
from sisyphus.rules.tasks import apply_all_rules, apply_rule_to_existing_jobs


class TestApplyAllRules:
    """Tests for the apply_all_rules task."""

    def test_applies_matching_rules(self, user_profile, company):
        rule = Rule.objects.create(
            user=user_profile, name='Filter Intern', target_status=Job.Status.FILTERED, priority=10
        )
        RuleCondition.objects.create(rule=rule, field='title', match_type='contains', value='intern')

        job = Job.objects.create(
            company=company, title='Software Intern', url='https://test.com/j/intern', populated=True, user=user_profile
        )

        result = apply_all_rules(user_profile.id)
        assert result == {'matched_count': 1}
        job.refresh_from_db()
        assert job.status == Job.Status.FILTERED

    def test_user_not_found(self, db):
        result = apply_all_rules(99999)
        assert result == {'error': 'User not found'}

    def test_only_first_matching_rule_per_job(self, user_profile, company):
        rule1 = Rule.objects.create(user=user_profile, name='Rule 1', target_status=Job.Status.FILTERED, priority=10)
        RuleCondition.objects.create(rule=rule1, field='title', match_type='contains', value='Engineer')

        rule2 = Rule.objects.create(user=user_profile, name='Rule 2', target_status=Job.Status.SAVED, priority=5)
        RuleCondition.objects.create(rule=rule2, field='title', match_type='contains', value='Engineer')

        job = Job.objects.create(
            company=company, title='Software Engineer', url='https://test.com/j/eng', populated=True, user=user_profile
        )

        result = apply_all_rules(user_profile.id)
        assert result == {'matched_count': 1}
        job.refresh_from_db()
        assert job.status == Job.Status.FILTERED
        assert RuleMatch.objects.filter(job=job).count() == 1


class TestApplyRuleToExistingJobs:
    """Tests for the apply_rule_to_existing_jobs task."""

    def test_applies_to_matching_jobs(self, user_profile, company):
        rule = Rule.objects.create(user=user_profile, name='Filter Test', target_status=Job.Status.FILTERED)
        RuleCondition.objects.create(rule=rule, field='title', match_type='contains', value='Engineer')

        job = Job.objects.create(company=company, title='Software Engineer', url='https://test.com/j/eng1', user=user_profile)

        result = apply_rule_to_existing_jobs(rule.id)
        assert result == {'matched_count': 1}
        job.refresh_from_db()
        assert job.status == Job.Status.FILTERED

    def test_rule_not_found(self, db):
        result = apply_rule_to_existing_jobs(99999)
        assert result == {'error': 'Rule not found'}

    def test_inactive_rule_skipped(self, user_profile):
        rule = Rule.objects.create(user=user_profile, name='Inactive', is_active=False)
        result = apply_rule_to_existing_jobs(rule.id)
        assert result == {'skipped': True, 'reason': 'Rule is not active'}
