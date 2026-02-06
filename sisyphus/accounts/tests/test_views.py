import pytest
from django.test import Client
from django.urls import reverse


class TestProfileView:
    """Tests for the profile view."""

    def test_get(self, client, user):
        client.force_login(user)
        response = client.get(reverse('accounts:profile'))
        assert response.status_code == 200

    def test_post_updates_name_and_timezone(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse('accounts:profile'),
            {'first_name': 'Jane', 'last_name': 'Smith', 'timezone': 'US/Eastern'},
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.first_name == 'Jane'
        assert user.last_name == 'Smith'
        assert user.profile.timezone == 'US/Eastern'

    def test_requires_login(self, client):
        response = client.get(reverse('accounts:profile'))
        assert response.status_code == 302
        assert 'login' in response.url


class TestResumeDeleteView:
    """Tests for the resume_delete view."""

    def test_get_not_allowed(self, client, user):
        client.force_login(user)
        response = client.get(reverse('accounts:resume_delete'))
        assert response.status_code == 405

    def test_requires_login(self, client):
        response = client.post(reverse('accounts:resume_delete'))
        assert response.status_code == 302
        assert 'login' in response.url
