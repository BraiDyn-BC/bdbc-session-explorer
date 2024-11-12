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

from typing import Literal, Union, Optional, Iterable
from pathlib import Path
from datetime import datetime
import sys as _sys
import warnings as _warnings


PathLike = Union[str, Path]
PathsLike = Union[PathLike, Iterable[PathLike]]
ErrorHandling = Literal['ignore', 'message', 'warn', 'error']


def message(
    msg: str,
    end: str = '\n',
    verbose: bool = True
):
    if verbose:
        print(msg, end=end, file=_sys.stderr, flush=True)


class FileNotFoundWarning(UserWarning):
    pass


class SessionExplorationError(RuntimeError):
    def __init__(self, msg):
        super().__init__(self, msg)


class SessionExplorationWarning(UserWarning):
    pass


def maybe_path(path: Optional[PathLike]) -> Optional[Path]:
    if path is not None:
        return Path(path)
    else:
        return None


def parse_date(datestr: str) -> datetime:
    if '-' in datestr:
        return datetime.strptime(datestr, '%Y-%m-%d')
    else:
        return datetime.strptime(datestr, '%y%m%d')


def handle_error(
    msg,
    type: ErrorHandling = 'warn',
    errorcls: type = SessionExplorationError,
    warncls: type = SessionExplorationWarning,
):
    if type == 'ignore':
        return
    elif type == 'message':
        message(f"***{msg}", verbose=True)
    elif type == 'warn':
        _warnings.warn(msg, category=warncls, stacklevel=3)
        return
    elif type == 'error':
        raise errorcls(msg)
    else:
        raise ValueError(f'unexpected error handling type: {type}')
