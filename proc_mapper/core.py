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

from typing import Literal
from typing_extensions import Self
from collections import namedtuple as _namedtuple
from datetime import datetime as _datetime
import sys as _sys
import warnings as _warnings

import rawdata_explorer as _rawx


ErrorHandling = Literal['ignore', 'warn', 'error']


def message(
    msg: str,
    end: str = '\n',
    verbose: bool = True
):
    if verbose:
        print(msg, end=end, file=_sys.stderr, flush=True)


class SessionExplorationError(RuntimeError):
    def __init__(self, msg):
        super().__init__(self, msg)


class SessionExplorationWarning(UserWarning):
    pass


def handle_error(msg, type: ErrorHandling = 'warn'):
    if type == 'ignore':
        return
    elif type == 'warn':
        _warnings.warn(msg, category=SessionExplorationWarning, stacklevel=2)
        return
    elif type == 'error':
        raise SessionExplorationError(msg)
    else:
        raise ValueError(f'unexpected error handling type: {type}')


class Session(_namedtuple('Session', ('batch', 'animal', 'date', 'type'))):
    FMT_SHORT_DATE = '%y%m%d'
    FMT_LONG_DATE  = '%Y-%m-%d'
    
    @property
    def longdate(self) -> str:
        return _datetime.strptime(self.date, self.FMT_SHORT_DATE).strftime(self.FMT_LONG_DATE)

    @classmethod
    def from_rawdata(cls, raw: _rawx.RawData) -> Self:
        return cls(**dict((key, getattr(raw, key)) for key in cls._fields))


def session_from_rawdata(raw: _rawx.RawData) -> Session:
    return Session.from_rawdata(raw)
