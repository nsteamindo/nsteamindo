from __future__ import annotations

import typing as t
import contextlib


class GetOrDefault:
    data: t.Optional[t.Union[dict, list, str]]

    def __init__(self, dict_list_str: t.Optional[t.Union[dict, list, str]]):
        self.data = dict_list_str

    def __call__(self, item, default=None):
        """
        get or default
        """

        try:
            return self.data[item]  # key/index
        except (KeyError, IndexError, TypeError):
            return default  # default

    def __getitem__(self, item):
        """
        get or null
        """

        if self.data is None:
            return self  # None

        with contextlib.suppress(KeyError, IndexError):
            x = self.data[item]

            if type(x) in (dict, list) or x is None:
                return GetOrDefault(x)

            return x

        return GetOrDefault(None)

    def __setitem__(self, key, value):
        with contextlib.suppress(KeyError, IndexError):
            self.data[key] = value

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(self.data)

    def __iter__(self):
        return iter(self.data)


def first_ifn_null(first, second: t.Optional[t.Any]) -> t.Optional[t.Any]:
    """
    return the first argument if the second argument is not null
    """
    if second is not None:
        return first
