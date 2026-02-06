import pytest
from django.urls import reverse

from sisyphus.jobs.models import Job
from sisyphus.rules.models import Rule, RuleCondition


class TestRuleListView:
    """Tests for the rule_list view."""

    def test_get(self, client, user, user_profile):
        client.force_login(user)
        response = client.get(reverse('rules:rule_list'))
        assert response.status_code == 200

    def test_requires_login(self, client):
        response = client.get(reverse('rules:rule_list'))
        assert response.status_code == 302
        assert 'login' in response.url


class TestRuleCreateView:
    """Tests for the rule_create view."""

    def test_get_form(self, client, user):
        client.force_login(user)
        response = client.get(reverse('rules:rule_create'))
        assert response.status_code == 200

    def test_post_creates_rule(self, client, user, user_profile):
        client.force_login(user)
        response = client.post(
            reverse('rules:rule_create'),
            {
                'name': 'New Rule',
                'match_mode': 'all',
                'target_status': 'filtered',
                'priority': '0',
                'condition_count': '1',
                'condition_0_field': 'title',
                'condition_0_match_type': 'contains',
                'condition_0_value': 'intern',
            },
        )
        assert response.status_code == 302
        assert Rule.objects.filter(name='New Rule').exists()
        rule = Rule.objects.get(name='New Rule')
        assert rule.conditions.count() == 1


class TestRuleDeleteView:
    """Tests for the rule_delete view."""

    def test_post_deletes_rule(self, client, user, user_profile):
        rule = Rule.objects.create(user=user_profile, name='To Delete')
        client.force_login(user)
        response = client.post(reverse('rules:rule_delete', kwargs={'uuid': rule.uuid}))
        assert response.status_code == 302
        assert not Rule.objects.filter(id=rule.id).exists()


class TestRuleToggleView:
    """Tests for the rule_toggle view."""

    def test_post_toggles_active(self, client, user, user_profile):
        rule = Rule.objects.create(user=user_profile, name='Toggle Me', is_active=True)
        client.force_login(user)
        response = client.post(reverse('rules:rule_toggle', kwargs={'uuid': rule.uuid}))
        assert response.status_code == 302
        rule.refresh_from_db()
        assert not rule.is_active
