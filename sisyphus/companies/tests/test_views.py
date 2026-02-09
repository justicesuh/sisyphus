import pytest
from django.urls import reverse

from sisyphus.companies.models import Company, CompanyNote
from sisyphus.jobs.models import Job

pytestmark = pytest.mark.usefixtures('user_profile')


class TestCompanyListView:
    """Tests for the company_list view."""

    def test_get(self, client, user, company):
        client.force_login(user)
        response = client.get(reverse('companies:company_list'))
        assert response.status_code == 200

    def test_search_filter(self, client, user, company):
        Company.objects.create(name='Other Corp', website='https://other.com', user=company.user)
        client.force_login(user)
        response = client.get(reverse('companies:company_list'), {'q': 'Test'})
        assert response.status_code == 200
        assert b'Test Company' in response.content
        assert b'Other Corp' not in response.content

    def test_banned_filter(self, client, user, company):
        banned = Company.objects.create(name='Bad Corp', is_banned=True, user=company.user)
        client.force_login(user)
        response = client.get(reverse('companies:company_list'), {'banned': 'yes'})
        assert response.status_code == 200
        assert b'Bad Corp' in response.content
        assert b'Test Company' not in response.content

    def test_sort(self, client, user, company):
        Company.objects.create(name='Alpha Corp', website='https://alpha.com', user=company.user)
        client.force_login(user)
        response = client.get(reverse('companies:company_list'), {'sort': 'name'})
        assert response.status_code == 200

    def test_requires_login(self, client):
        response = client.get(reverse('companies:company_list'))
        assert response.status_code == 302
        assert 'login' in response.url


class TestCompanyDetailView:
    """Tests for the company_detail view."""

    def test_get(self, client, user, company):
        client.force_login(user)
        response = client.get(reverse('companies:company_detail', kwargs={'uuid': company.uuid}))
        assert response.status_code == 200

    def test_404(self, client, user):
        import uuid

        client.force_login(user)
        response = client.get(reverse('companies:company_detail', kwargs={'uuid': uuid.uuid4()}))
        assert response.status_code == 404


class TestCompanyToggleBanView:
    """Tests for the company_toggle_ban view."""

    def test_ban(self, client, user, company):
        client.force_login(user)
        response = client.post(
            reverse('companies:company_toggle_ban', kwargs={'uuid': company.uuid}),
            {'reason': 'Spam'},
        )
        assert response.status_code == 302
        company.refresh_from_db()
        assert company.is_banned

    def test_unban(self, client, user, company):
        company.ban(reason='Spam')
        client.force_login(user)
        response = client.post(reverse('companies:company_toggle_ban', kwargs={'uuid': company.uuid}))
        assert response.status_code == 302
        company.refresh_from_db()
        assert not company.is_banned

    def test_get_not_allowed(self, client, user, company):
        client.force_login(user)
        response = client.get(reverse('companies:company_toggle_ban', kwargs={'uuid': company.uuid}))
        assert response.status_code == 405


class TestCompanyAddNoteView:
    """Tests for the company_add_note view."""

    def test_post_creates_note(self, client, user, company):
        client.force_login(user)
        response = client.post(
            reverse('companies:company_add_note', kwargs={'uuid': company.uuid}),
            {'text': 'Nice company'},
        )
        assert response.status_code == 302
        assert company.notes.filter(text='Nice company').exists()

    def test_empty_text_no_note(self, client, user, company):
        client.force_login(user)
        client.post(
            reverse('companies:company_add_note', kwargs={'uuid': company.uuid}),
            {'text': ''},
        )
        assert company.notes.count() == 0


class TestCompanyDeleteNoteView:
    """Tests for the company_delete_note view."""

    def test_post_deletes_note(self, client, user, company):
        note = company.add_note('To delete')
        client.force_login(user)
        response = client.post(
            reverse('companies:company_delete_note', kwargs={'uuid': company.uuid, 'note_id': note.id}),
        )
        assert response.status_code == 302
        assert not CompanyNote.objects.filter(id=note.id).exists()
