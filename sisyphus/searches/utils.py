from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bs4 import NavigableString, Tag


class NullableTag:
    def __init__(self, tag: Tag | None = None):
        self._tag = tag

    def find(self, *args, **kwargs) -> NullableTag:
        if self._tag is None:
            return NullableTag()
        return NullableTag(self._tag.find(*args, **kwargs))

    def find_all(self, *args, **kwargs) -> list[Tag]:
        if self._tag is None:
            return []
        return self._tag.find_all(*args, **kwargs)

    def select_one(self, *args, **kwargs) -> NullableTag:
        if self._tag is None:
            return NullableTag()
        return NullableTag(self._tag.select_one(*args, **kwargs))

    def select(self, *args, **kwargs) -> list[Tag]:
        if self._tag is None:
            return []
        return self._tag.select(*args, **kwargs)

    def get_text(self, *args, **kwargs) -> str:
        if self._tag is None:
            return ''
        return self._tag.get_text(*args, **kwargs)

    @property
    def text(self) -> str:
        if self._tag is None:
            return ''
        return self._tag.text

    @property
    def string(self) -> NavigableString | None:
        if self._tag is None:
            return None
        return self._tag.string

    def get(self, key: str, default: str | None = None) -> str | None:
        if self._tag is None:
            return default
        return self._tag.get(key, default)

    def __getitem__(self, key: str) -> str:
        if self._tag is None:
            raise KeyError(key)
        return self._tag[key]

    def __bool__(self) -> bool:
        return self._tag is not None

    def __repr__(self) -> str:
        return f'NullableTag({self._tag!r})'
