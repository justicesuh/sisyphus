import pytest
from django.core.exceptions import ValidationError

from sisyphus.core.fields import UUIDField


class TestUUIDField:
    """Tests for the custom UUIDField."""

    def test_default_version_4(self):
        field = UUIDField()
        assert field.default is not None

    def test_version_2_raises(self):
        with pytest.raises(ValidationError, match='UUID version 2 is not supported.'):
            UUIDField(version=2)

    def test_invalid_version_raises(self):
        with pytest.raises(ValidationError, match='UUID version is not valid.'):
            UUIDField(version=0)
        with pytest.raises(ValidationError, match='UUID version is not valid.'):
            UUIDField(version=8)
