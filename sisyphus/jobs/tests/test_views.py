import uuid

import pytest
from django.urls import reverse

from sisyphus.jobs.models import Job, JobNote


class TestJobListView:
    """Tests for the job_list view."""

    def test_get(self, client, user, job):
        client.force_login(user)
        response = client.get(reverse('jobs:job_list'))
        assert response.status_code == 200

    def test_search_filter(self, client, user, job, company):
        Job.objects.create(company=company, title='Data Analyst', url='https://test.com/j/other')
        client.force_login(user)
        response = client.get(reverse('jobs:job_list'), {'q': 'Software'})
        assert response.status_code == 200
        assert b'Software Engineer' in response.content
        assert b'Data Analyst' not in response.content

    def test_status_filter(self, client, user, job, company):
        saved_job = Job.objects.create(
            company=company, title='Saved Job', url='https://test.com/j/saved', status=Job.Status.SAVED
        )
        client.force_login(user)
        response = client.get(reverse('jobs:job_list'), {'status': 'saved'})
        assert response.status_code == 200
        assert b'Saved Job' in response.content
        assert b'Software Engineer' not in response.content

    def test_flexibility_filter(self, client, user, job_with_description):
        client.force_login(user)
        response = client.get(reverse('jobs:job_list'), {'flexibility': 'remote'})
        assert response.status_code == 200
        assert b'Senior Developer' in response.content

    def test_requires_login(self, client):
        response = client.get(reverse('jobs:job_list'))
        assert response.status_code == 302
        assert 'login' in response.url


class TestJobDetailView:
    """Tests for the job_detail view."""

    def test_get(self, client, user, job):
        client.force_login(user)
        response = client.get(reverse('jobs:job_detail', kwargs={'uuid': job.uuid}))
        assert response.status_code == 200

    def test_404(self, client, user):
        client.force_login(user)
        response = client.get(reverse('jobs:job_detail', kwargs={'uuid': uuid.uuid4()}))
        assert response.status_code == 404


class TestJobUpdateStatusView:
    """Tests for the job_update_status view."""

    def test_post_updates_status(self, client, user, job):
        client.force_login(user)
        response = client.post(
            reverse('jobs:job_update_status', kwargs={'uuid': job.uuid}),
            {'status': 'saved'},
        )
        assert response.status_code == 302
        job.refresh_from_db()
        assert job.status == Job.Status.SAVED

    def test_get_not_allowed(self, client, user, job):
        client.force_login(user)
        response = client.get(reverse('jobs:job_update_status', kwargs={'uuid': job.uuid}))
        assert response.status_code == 405


class TestJobAddNoteView:
    """Tests for the job_add_note view."""

    def test_post_creates_note(self, client, user, job):
        client.force_login(user)
        response = client.post(
            reverse('jobs:job_add_note', kwargs={'uuid': job.uuid}),
            {'text': 'Looks promising'},
        )
        assert response.status_code == 302
        assert job.notes.filter(text='Looks promising').exists()


class TestJobDeleteNoteView:
    """Tests for the job_delete_note view."""

    def test_post_deletes_note(self, client, user, job):
        note = job.add_note('To delete')
        client.force_login(user)
        response = client.post(
            reverse('jobs:job_delete_note', kwargs={'uuid': job.uuid, 'note_id': note.id}),
        )
        assert response.status_code == 302
        assert not JobNote.objects.filter(id=note.id).exists()


class TestJobReviewView:
    """Tests for the job_review view."""

    def test_get_default_new(self, client, user, job_with_description):
        client.force_login(user)
        response = client.get(reverse('jobs:job_review'))
        assert response.status_code == 200

    def test_get_saved_filter(self, client, user, job_with_description):
        job_with_description.update_status(Job.Status.SAVED)
        client.force_login(user)
        response = client.get(reverse('jobs:job_review'), {'status': 'saved'})
        assert response.status_code == 200


class TestJobReviewActionView:
    """Tests for the job_review_action view."""

    def test_post_updates_status_and_redirects(self, client, user, job):
        client.force_login(user)
        response = client.post(
            reverse('jobs:job_review_action', kwargs={'uuid': job.uuid}),
            {'status': 'dismissed'},
        )
        assert response.status_code == 302
        assert 'review' in response.url
        job.refresh_from_db()
        assert job.status == Job.Status.DISMISSED
