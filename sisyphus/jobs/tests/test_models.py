import pytest

from sisyphus.jobs.models import Job, JobEvent, JobNote, Location


class TestLocation:
    """Tests for the Location model."""

    def test_str(self, location):
        assert str(location) == 'New York, NY'


class TestJob:
    """Tests for the Job model."""

    def test_str(self, job):
        assert str(job) == 'Software Engineer'

    def test_update_status(self, job):
        job.update_status(Job.Status.SAVED)
        assert job.status == Job.Status.SAVED
        assert job.cached_status == Job.Status.SAVED
        assert JobEvent.objects.filter(job=job, old_status=Job.Status.NEW, new_status=Job.Status.SAVED).exists()

    def test_update_status_same_status_noop(self, job):
        job.update_status(Job.Status.NEW)
        assert JobEvent.objects.filter(job=job).count() == 0

    def test_update_status_to_banned_saves_pre_ban_status(self, job):
        job.update_status(Job.Status.SAVED)
        job.update_status(Job.Status.BANNED)
        assert job.pre_ban_status == Job.Status.SAVED

    def test_update_status_from_banned_clears_pre_ban_status(self, job):
        job.update_status(Job.Status.BANNED)
        assert job.pre_ban_status == Job.Status.NEW
        job.update_status(Job.Status.NEW)
        assert job.pre_ban_status == ''

    def test_add_note(self, job):
        note = job.add_note('Test note')
        assert isinstance(note, JobNote)
        assert note.text == 'Test note'
        assert note.job == job

    def test_cached_status_set_on_init(self, job):
        assert job.cached_status == Job.Status.NEW


class TestJobEvent:
    """Tests for the JobEvent model."""

    def test_str(self, job):
        job.update_status(Job.Status.SAVED)
        event = JobEvent.objects.get(job=job)
        assert str(event) == 'Software Engineer | New -> Saved'


class TestJobNote:
    """Tests for the JobNote model."""

    def test_str(self, job):
        note = JobNote.objects.create(job=job, text='A note')
        assert str(note) == 'Software Engineer | A note'
