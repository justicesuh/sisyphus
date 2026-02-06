from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import admin

if TYPE_CHECKING:
    from django.http import HttpRequest


class UUIDModelAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    readonly_fields = ('uuid',)

    def get_readonly_fields(self, request: HttpRequest, obj: object = None) -> tuple[str, ...]:
        """Return readonly fields, including timestamps if present."""
        fields = tuple(super().get_readonly_fields(request, obj))
        return fields + tuple(field for field in ('created_at', 'updated_at') if hasattr(self.model, field))

    def get_fields(self, request: HttpRequest, obj: object = None) -> list[Any]:
        """Return fields with uuid moved to the first position."""
        fields = list(super().get_fields(request, obj))
        fields.remove('uuid')
        fields.insert(0, 'uuid')
        return fields
