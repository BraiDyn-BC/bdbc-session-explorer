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

from typing import Union, Literal, Tuple, Dict, Optional, Iterable
from pathlib import Path
from collections import namedtuple as _namedtuple

import numpy as _np
import numpy.typing as _npt
import h5py as _h5

from . import (
    core as _core,
    session as _session,
)

PathLike = _core.PathLike
RawFileVersion = Literal['v0', 'v1']
ImageChannel = Literal['green', 'blue']

# FIXME: want to write _npt.NDArray[Tuple[int, int], _np.float32]
# # but it somehow results in an error in a certain case...
AverageFrame = _npt.NDArray[_np.float32]


class RawDataDirectoryWarning(UserWarning):
    pass


class RawDataDirectoryError(RuntimeError):
    def __init__(self, msg):
        super().__init__(msg)


class RawData(_namedtuple('RawData', ('version', 'session', 'path'))):
    @classmethod
    def empty(
        cls,
        version: RawFileVersion = 'v1',
        session: Optional[_session.Session] = None,
    ):
        return cls(version, session, None)

    @property
    def base(self) -> str:
        return self.session.base

    @property
    def batch(self) -> str:
        return self.session.batch

    @property
    def animal(self) -> str:
        return self.session.animal

    @property
    def shortdate(self) -> str:
        return self.session.shortdate

    @property
    def longdate(self) -> str:
        return self.session.longdate

    @property
    def shorttype(self) -> str:
        return self.session.shorttype

    @property
    def longtype(self) -> str:
        return self.session.longtype

    def metadata(self) -> Dict[str, str]:
        return self.session.metadata()

    def read_avg_frames(
        self,
        channel: ImageChannel = 'green',
        transposed: bool = True,
    ) -> Tuple[AverageFrame, AverageFrame]:
        """returns (meanframe, stdframe)

        the option `transposed` is set to True by default,
        because the data is in the MATLAB/FORTRAN order,
        and we want images to be in NumPy/C order.
        """
        meanpath, stdpath = _avg_frame_paths(self.version, channel)
        with _h5.File(str(self.path), 'r') as src:
            meanframe = _np.array(src[meanpath], dtype=_np.float32)  # copy
            stdframe = _np.array(src[stdpath], dtype=_np.float32)  # copy
        if transposed == True:
            meanframe = meanframe.T
            stdframe = stdframe.T
        return meanframe, stdframe


def _avg_frame_paths(
    file_version: RawFileVersion = 'v1',
    image_channel: ImageChannel = 'green',
) -> Tuple[str, str]:
    if file_version == 'v0':
        if image_channel == 'green':
            return ('Image/Bavg', 'Image/Bstd')
        elif image_channel == 'blue':
            return ('Image/Vavg', 'Image/Vstd')
        else:
            raise ValueError(f"unexpected channel spec: {image_channel}")
    elif file_version == 'v1':
        if image_channel == 'green':
            return ('image/Ib_avg', 'image/Ib_std')
        elif image_channel == 'blue':
            return ('image/Iv_avg', 'image/Iv_std')
        else:
            raise ValueError(f"unexpected channel spec: {image_channel}")
    else:
        raise ValueError(f"unexpected file version: {file_version}")


def rawdata_from_session(
    session: _session.Session,
    rawroot: Union[PathLike, Iterable[PathLike]],
    file_version: RawFileVersion = 'v1',
    error_handling: _core.ErrorHandling = 'warn',
    locate_without_rawdata: bool = False,
) -> RawData:
    if (not session.has_rawdata()) and (not locate_without_rawdata):
        return RawData.empty(version=file_version, session=session)

    rawfile = locate_rawdata_file(
        session=session,
        rawroot=rawroot,
        file_version=file_version,
        error_handling=error_handling,
        locate_without_rawdata=locate_without_rawdata,
    )
    return RawData(version=file_version, session=session, path=rawfile)


def locate_rawdata_file(
    session: _session.Session,
    rawroot: Union[PathLike, Iterable[PathLike]],
    file_version: RawFileVersion = 'v1',
    error_handling: _core.ErrorHandling = 'warn',
    locate_without_rawdata: bool = False,
) -> Optional[Path]:

    def _camel_session(session):
        base = session.longtype.replace('-', '_')
        return base[0].upper() + base[1:]

    def _configure_v0(anidir, session):
        parent = anidir / _camel_session(session) / session.shortdate
        pat = f"RawData_{session.shortdate}_{session.animal}*.h5"
        return parent, pat

    def _configure_v1(anidir, session):
        parent = anidir / session.shorttype
        pat = f"RawData_{session.longdate}_{session.animal}*.h5"
        return parent, pat

    if (not session.has_rawdata()) and (not locate_without_rawdata):
        return None
    if isinstance(rawroot, (str, Path)):
        rawroot = (rawroot,)
    for root in rawroot:
        anidir = root / session.batch / session.animal
        if file_version == 'v0':
            parent, pat = _configure_v0(anidir, session)
        elif file_version == 'v1':
            parent, pat = _configure_v1(anidir, session)
        else:
            raise ValueError(f"unexpected file version: {file_version}")
        if not parent.exists():
            continue

        candidates = tuple(parent.glob(pat))
        if len(candidates) == 0:
            _core.handle_error(
                f"no file found with pattern: {pat}",
                type=error_handling,
                errorcls=FileNotFoundError,
                warncls=_core.FileNotFoundWarning,
            )
            return None
        elif len(candidates) > 1:
            _core.handle_error(
                f"{len(candidates)} files found with pattern: {pat}",
                type=error_handling,
                errorcls=RawDataDirectoryError,
                warncls=RawDataDirectoryWarning,
            )
            return None
        else:
            return candidates[0]

    _core.handle_error(
        f"no raw-data directory found for session: {session.shortdate} {session.animal}",
        type=error_handling,
        errorcls=RawDataDirectoryError,
        warncls=RawDataDirectoryWarning,
    )
    return None
