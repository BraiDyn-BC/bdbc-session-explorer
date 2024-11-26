# MIT License
#
# Copyright (c) 2024 Keisuke Sehara
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from typing import Optional, Iterator, Callable
from datetime import datetime

from . import (
    core as _core,
    env as _env,
    session as _session,
)

PathLike = _core.PathLike


def iterate_sessions(
    animal: Optional[str] = None,
    batch: Optional[str] = None,
    fromdate: Optional[str] = None,
    todate: Optional[str] = None,
    type: Optional[str] = None,
    sessions_root_dir: Optional[PathLike] = None,
    verbose: bool = True
) -> Iterator[_session.Session]:
    is_animal = matcher.animal(animal)
    is_batch = matcher.batch(batch)
    is_date = matcher.date(from_date=fromdate, to_date=todate)
    is_type = matcher.session_type(type)

    def _matches(session: _session.Session) -> bool:
        return is_animal(session.animal) and is_batch(session.batch) and is_date(session.date) and is_type(session.type)

    sessions_root_dir = _env.sessions_root_dir(sessions_root_dir)
    _core.message(f"...SESSIONS_ROOT_DIR={repr(str(sessions_root_dir))}", verbose=verbose)
    if not sessions_root_dir.exists():
        raise RuntimeError(f"session directory not found: {str(sessions_root_dir)}")

    found = 0
    for sess in _session.iterate_sessions_from_root(sessions_root_dir):
        found += 1
        if _matches(sess):
            yield sess
    if found == 0:
        _core.message("***no sessions found (maybe inappropriate session directory setting?)", verbose=True)


class matcher:
    @staticmethod
    def matches_all(query: str) -> bool:
        return True

    @staticmethod
    def animal(ref: Optional[str]) -> Callable[[str], bool]:
        if ref is None:
            return matcher.matches_all
        else:
            refs = tuple(item.strip() for item in ref.split(','))

            def match(query: str) -> bool:
                return (query in refs)

            return match

    @staticmethod
    def batch(ref: Optional[str]) -> Callable[[str], bool]:
        if ref is None:
            return matcher.matches_all
        else:
            refs = tuple(item.strip() for item in ref.split(','))

            def match(query: str) -> bool:
                return (query in refs)

            return match

    @staticmethod
    def from_date(ref: Optional[str]) -> Callable[[datetime], bool]:
        if ref is None:
            return matcher.matches_all
        else:
            ref = _core.parse_date(ref)

            def match(query: datetime) -> bool:
                return (query >= ref)

            return match

    @staticmethod
    def to_date(ref: Optional[str]) -> Callable[[datetime], bool]:
        if ref is None:
            return matcher.matches_all
        else:
            ref = _core.parse_date(ref)

            def match(query: datetime) -> bool:
                return (query <= ref)

            return match

    @staticmethod
    def date(
        from_date: Optional[str],
        to_date: Optional[str]
    ) -> Callable[[str], bool]:
        from_date = matcher.from_date(from_date)
        to_date = matcher.to_date(to_date)

        def match(query: datetime) -> bool:
            return from_date(query) and to_date(query)

        return match

    @staticmethod
    def session_type(
        ref: Optional[str]
    ) -> Callable[[str], bool]:
        if ref is None:
            return matcher.matches_all
        else:
            mapping = _session.Session.LONG_TYPES
            refs = tuple(item.strip() for item in ref.split(','))
            norm = []
            for ref in refs:
                if ref in mapping.keys():
                    ref = mapping[ref]
                if ref not in _session.Session.LONG_TYPES.values():
                    raise ValueError(f"expected one of ('task', 'resting-state', 'sensory-stim'), got '{ref}'")
                norm.append(ref)
            refs = tuple(norm)

            def match(query: str) -> bool:
                query = _session.Session.LONG_TYPES.get(query, query)
                return (query in refs)
            return match
