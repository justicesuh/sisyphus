import pytest
from django.urls import reverse

from sisyphus.metrics.views import _trend


class TestTrend:
    """Tests for the _trend helper function."""

    def test_up(self):
        result = _trend(15, 10)
        assert result == {'pct': '50%', 'direction': 'up'}

    def test_down(self):
        result = _trend(5, 10)
        assert result == {'pct': '50%', 'direction': 'down'}

    def test_zero_previous_with_current(self):
        result = _trend(5, 0)
        assert result == {'pct': '100%', 'direction': 'up'}

    def test_zero_both(self):
        result = _trend(0, 0)
        assert result == {'pct': '0%', 'direction': 'down'}


class TestIndexView:
    """Tests for the metrics index view."""

    def test_get(self, client, user):
        client.force_login(user)
        response = client.get(reverse('metrics:index'))
        assert response.status_code == 200

    def test_requires_login(self, client):
        response = client.get(reverse('metrics:index'))
        assert response.status_code == 302
        assert 'login' in response.url
