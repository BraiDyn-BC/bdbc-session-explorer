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

from typing import Optional
from typing_extensions import Self
from pathlib import Path
from collections import namedtuple as _namedtuple
import sys as _sys
import shutil as _shutil
import tempfile as _tempfile

from . import (
    core as _core,
    session as _session,
)


class VideoFiles(_namedtuple('VideoFiles', ('session', 'body', 'face', 'eye'))):
    LABELS = {
        'body': 'Front',
        'face': 'Side',
        'eye': 'Eye',
    }

    @classmethod
    def empty(
        cls,
        session: Optional[_session.Session] = None
    ) -> Self:
        return cls(
            session=session,
            body=None,
            face=None,
            eye=None
        )

    @property
    def directory(self) -> Path:
        return self.body.parent

    def is_not_empty(self) -> bool:
        return any((getattr(self, lab) is not None) for lab in self.LABELS.keys())

    def copy_to_temp(
        self,
        verbose: bool = True
    ) -> Self:
        tempdir = Path(_tempfile.mkdtemp(prefix='dlc_'))
        try:
            videos = dict()
            _core.message(f"copying {self.directory.name}: ", end='', verbose=verbose)
            for vtype in self.LABELS.keys():
                _core.message(f"{vtype}...", end='', verbose=verbose)
                video = getattr(self, vtype)
                if video is not None:
                    vpath = tempdir / video.name
                    _shutil.copy(video, vpath)
                    videos[vtype] = vpath
                else:
                    videos[vtype] = None
            _core.message("done.", verbose=verbose)
        except:
            t, v, tb = _sys.exc_info()
            _shutil.rmtree(tempdir)
            raise (t, v, tb)
        return self.__class__(session=session, **videos)


def video_files_from_session(
    session: _session.Session,
    videoroot: Path,
    error_handling: _core.ErrorHandling = 'warn',
) -> VideoFiles:
    if not session.has_any_videos():
        return VideoFiles.empty(session=session)
    videodir = find_video_dir(session, videoroot=videoroot)
    if not videodir.exists():
        _core.handle_error(
            f"{videodir.name}: video directory not found",
            type=error_handling
        )
        return VideoFiles.empty(session)
    videos = dict()
    for vtype, vlab in VideoFiles.LABELS.items():
        if session.availability.has_video(vtype):
            vpath = find_video_file(videodir=videodir, videotype=vlab)
            if (vpath is None) or (not vpath.exists()):
                _core.handle_error(
                    f"{videodir.name}: {vtype} video not found",
                    type=error_handling,
                )
        else:
            vpath = None
        videos[vtype] = vpath
    return VideoFiles(session=session, **videos)


def find_video_dir(session: _session.Session, videoroot: Path) -> Path:
    datename = session.shortdate
    sessname = f"{session.shortdate}_{session.animal}"
    if session.shorttype != 'task':
        datename = f"{datename}_{session.shorttype}"
        sessname = f"{sessname}_{session.shorttype}"
    return videoroot / datename / sessname


def find_video_file(videodir: Path, videotype: str = 'Eye') -> Optional[Path]:
    candidates = list(videodir.glob(f'*_{videotype}_*.mp4'))
    if len(candidates) > 1:
        raise ValueError(f"{videodir.name}: {len(candidates)} candidates found for '{videotype}'")
    elif len(candidates) == 0:
        return None
    return candidates[0]

