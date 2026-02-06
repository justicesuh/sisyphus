import pytest

from sisyphus.accounts.models import User, UserProfile
from sisyphus.companies.models import Company
from sisyphus.jobs.models import Job, Location


@pytest.fixture
def user(db):
    """Create a regular user."""
    return User.objects.create_user(email='test@example.com', password='testpass123')


@pytest.fixture
def user_profile(user):
    """Create a user profile for the test user."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@pytest.fixture
def company(db):
    """Create a test company."""
    return Company.objects.create(name='Test Company', website='https://test.com')


@pytest.fixture
def location(db):
    """Create a test location."""
    return Location.objects.create(name='New York, NY')


@pytest.fixture
def job(company):
    """Create a basic test job (not populated)."""
    return Job.objects.create(
        company=company,
        title='Software Engineer',
        url='https://test.com/jobs/1',
    )


@pytest.fixture
def job_with_description(company, location):
    """Create a populated job with a description."""
    return Job.objects.create(
        company=company,
        title='Senior Developer',
        url='https://test.com/jobs/2',
        location=location,
        populated=True,
        description='We are looking for a senior developer with Python experience.',
        flexibility=Job.Flexibility.REMOTE,
    )
