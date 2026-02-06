import pytest

from sisyphus.accounts.models import User, UserProfile


class TestUserManager:
    """Tests for the custom UserManager."""

    def test_create_user(self, db):
        user = User.objects.create_user(email='user@example.com', password='pass123')
        assert user.email == 'user@example.com'
        assert user.check_password('pass123')
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_no_email_raises(self, db):
        with pytest.raises(ValueError, match='The email field must be set.'):
            User.objects.create_user(email='', password='pass123')

    def test_create_superuser(self, db):
        user = User.objects.create_superuser(email='admin@example.com', password='pass123')
        assert user.email == 'admin@example.com'
        assert user.is_staff
        assert user.is_superuser

    def test_create_superuser_not_staff_raises(self, db):
        with pytest.raises(ValueError, match='Superuser must have is_staff=True.'):
            User.objects.create_superuser(email='admin@example.com', password='pass123', is_staff=False)

    def test_create_superuser_not_superuser_raises(self, db):
        with pytest.raises(ValueError, match='Superuser must have is_superuser=True.'):
            User.objects.create_superuser(email='admin@example.com', password='pass123', is_superuser=False)


class TestUser:
    """Tests for the User model."""

    def test_str(self, user):
        assert str(user) == user.email

    def test_get_full_name(self, user):
        user.first_name = 'John'
        user.last_name = 'Doe'
        assert user.get_full_name() == 'John Doe'

    def test_get_full_name_partial(self, user):
        user.first_name = 'John'
        user.last_name = ''
        assert user.get_full_name() == 'John'

    def test_get_short_name(self, user):
        user.first_name = 'John'
        assert user.get_short_name() == 'John'

    def test_clean_normalizes_email(self, user):
        user.email = 'Test@EXAMPLE.COM'
        user.clean()
        assert user.email == 'Test@example.com'


class TestUserProfile:
    """Tests for the UserProfile model."""

    def test_str(self, user_profile):
        assert str(user_profile) == user_profile.user.email
