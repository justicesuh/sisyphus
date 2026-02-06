import pytest

from sisyphus.companies.models import Company, CompanyNote
from sisyphus.jobs.models import Job


class TestCompany:
    """Tests for the Company model."""

    def test_str(self, company):
        assert str(company) == 'Test Company'

    def test_add_note(self, company):
        note = company.add_note('Great company')
        assert isinstance(note, CompanyNote)
        assert note.text == 'Great company'
        assert note.company == company

    def test_ban(self, company):
        company.ban(reason='Spam')
        company.refresh_from_db()
        assert company.is_banned
        assert company.banned_at is not None
        assert company.ban_reason == 'Spam'

    def test_ban_updates_new_jobs_to_banned(self, company):
        job_new = Job.objects.create(company=company, title='Job 1', url='https://test.com/j/1', status=Job.Status.NEW)
        job_saved = Job.objects.create(
            company=company, title='Job 2', url='https://test.com/j/2', status=Job.Status.SAVED
        )
        company.ban()
        job_new.refresh_from_db()
        job_saved.refresh_from_db()
        assert job_new.status == Job.Status.BANNED
        assert job_saved.status == Job.Status.BANNED

    def test_ban_does_not_affect_applied_jobs(self, company):
        job = Job.objects.create(
            company=company, title='Job 1', url='https://test.com/j/1', status=Job.Status.APPLIED
        )
        company.ban()
        job.refresh_from_db()
        assert job.status == Job.Status.APPLIED

    def test_unban(self, company):
        company.ban(reason='Spam')
        company.unban()
        company.refresh_from_db()
        assert not company.is_banned
        assert company.banned_at is None
        assert company.ban_reason == ''

    def test_unban_restores_pre_ban_status(self, company):
        job = Job.objects.create(company=company, title='Job 1', url='https://test.com/j/1', status=Job.Status.SAVED)
        company.ban()
        job.refresh_from_db()
        assert job.status == Job.Status.BANNED
        assert job.pre_ban_status == Job.Status.SAVED

        company.unban()
        job.refresh_from_db()
        assert job.status == Job.Status.SAVED


class TestCompanyNote:
    """Tests for the CompanyNote model."""

    def test_str(self, company):
        note = CompanyNote.objects.create(company=company, text='A note')
        assert str(note) == 'Test Company | A note'
