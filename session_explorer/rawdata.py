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

from typing import Union, Generator, Literal, Tuple, Dict, Optional, Iterable
from pathlib import Path
from collections import namedtuple as _namedtuple
from datetime import datetime as _datetime
import warnings as _warnings
import re as _re

import numpy as _np
import numpy.typing as _npt
import h5py as _h5

from . import (
    core as _core,
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


class TaskType(_namedtuple('TaskType', ('name', 'abbrev', 'pattern', 'defaultindex'))):
    def directory_name(self, file_version: RawFileVersion = 'v1') -> str:
        if file_version == 'v0':
            return self.name
        elif file_version == 'v1':
            return self.abbrev
        else:
            raise ValueError(f"unexpected file version: {file_version}")


TASK_TYPES = (
    TaskType('resting_state', 'rest', 'res*', 2),
    TaskType('sensory_stim', 'ss', 'ss', 1),
    TaskType('task', 'task', '', 1),
)


class RawData(_namedtuple('RawData', ('version', 'session', 'sessionindex', 'path'))):
    FILE_GLOB = "RawData_*.h5"
    DATE_PATTERN_V0 = _re.compile(r"RawData_([0-9]+)_([a-zA-Z0-9#-]+)")
    DATE_PATTERN_V1 = _re.compile(r"RawData_([0-9-]+)_([a-zA-Z0-9#-]+)")

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
    def date(self) -> str:
        return self.session.date

    @property
    def type(self) -> str:
        return self.session.type

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


def collect_rawdata_by_animal(
    rootdir: PathLike,
    batch: Optional[Union[str, Iterable[str]]] = None,
    animal: Optional[Union[str, Iterable[str]]] = None,
    file_version: RawFileVersion = 'v1',
    error_handling: _core.ErrorHandling = 'warn',
) -> Dict[str, Tuple[RawData]]:
    def _filter(sessions):
        yield from filter_rawdata_by_animal(filter_rwadata_by_batch(sessions, batch), animal)

    rawfiles = tuple(_filter(iterate_rawdata(
        rootdir,
        file_version=file_version,
        error_handling=error_handling
    )))

    animals = tuple(sorted(
        set(raw.session.animal for raw in rawfiles),
        key=_parse_animal_ID,
    ))

    data = dict()
    for animal in animals:
        data[animal] = []
    for raw in rawfiles:
        data[raw.session.animal].append(raw)
    return dict((animal, tuple(rawx)) for animal, rawx in data.items())


def iterate_rawdata(
    rootdir: PathLike,
    file_version: RawFileVersion = 'v1',
    error_handling: _core.ErrorHandling = 'warn',
) -> Generator[RawData, None, None]:
    rootdir = Path(rootdir)
    for batch in (path for path in rootdir.iterdir() if path.name.startswith('run')):
        for anidir in (path for path in batch.iterdir() if _is_valid_animal_dir(path)):
            for tasktype in TASK_TYPES:
                groupdir = anidir / tasktype.directory_name(file_version=file_version)
                if not groupdir.exists():
                    _core.handle_error(
                        f"not found: {groupdir}",
                        type=error_handling,
                        errorcls=RawDataDirectoryError,
                        warncls=RawDataDirectoryWarning
                    )
                    continue

                if file_version == 'v0':
                    yield from _iterate_from_group_v0(
                        groupdir,
                        batch.name,
                        anidir.name,
                        tasktype,
                    )
                elif file_version == 'v1':
                    yield from _iterate_from_group_v1(
                        groupdir,
                        batch.name,
                        anidir.name,
                        tasktype,
                    )


def _iterate_from_group_v0(
    groupdir: Path,
    batch: str,
    animal: str,
    tasktype: TaskType,
) -> Generator[RawData, None, None]:
    for datedir in (path for path in groupdir.iterdir() if _is_valid_date_dir(path)):
        for i, sessfile in enumerate(sorted(datedir.glob(RawData.FILE_GLOB))):
            # a dirty modification to deal with the 'first' resting-state sessions in some batches
            if _re.match(r'run\d$', batch) and (tasktype.name == 'resting_state') and (i == 0):
                idx = 1
            else:
                idx = tasktype.defaultindex
            session = _core.Session(
                batch=batch,
                animal=animal,
                date=datedir.name,
                type=tasktype.abbrev,
            )
            yield RawData(
                version='v0',
                session=session,
                sessionindex=idx,
                path=sessfile
            )


def _iterate_from_group_v1(
    groupdir: Path,
    batch: str,
    animal: str,
    tasktype: TaskType,
) -> Generator[RawData, None, None]:
    for i, sessfile in enumerate(sorted(groupdir.glob(RawData.FILE_GLOB))):
        # a dirty modification to deal with the 'first' resting-state sessions in some batches
        if _re.match(r'run\d$', batch) and (tasktype.name == 'resting_state') and (i == 0):
            idx = 1
        else:
            idx = tasktype.defaultindex
        session = _core.Session(
            batch=batch,
            animal=animal,
            date=_parse_date_v1(sessfile.name),
            type=tasktype.abbrev,
        )
        yield RawData(
            version='v1',
            session=session,
            sessionindex=idx,
            path=sessfile
        )


def filter_rawdata_by_attr(
    iterable: Iterable[RawData],
    name: str,
    value: Optional[Union[str, Iterable[str]]] = None,
) -> Generator[RawData, None, None]:
    if value is None:
        # no filtering
        yield from iterable
    else:
        if isinstance(value, str):
            value = (value,)
        else:
            value = tuple(value)
        for sess in iterable:
            val = getattr(sess, name)
            if val in value:
                yield sess
            else:
                continue


def filter_rawdata_by_animal(
    iterable: Iterable[RawData],
    animal: Optional[Union[str, Iterable[str]]] = None,
) -> Generator[RawData, None, None]:
    yield from filter_by_attr(iterable, name='animal', value=animal)


def filter_rawdata_by_batch(
    iterable: Iterable[RawData],
    batch: Optional[Union[str, Iterable[str]]] = None,
) -> Generator[RawData, None, None]:
    yield from filter_by_attr(iterable, name='batch', value=batch)


def _is_valid_date_dir(path: Path) -> bool:
    try:
        _ = int(path.name)
        return True
    except ValueError:
        return False


def _is_valid_animal_dir(anidir: Path) -> bool:
    try:
        _parse_animal_ID(anidir.name)
        return True
    except ValueError:
        return False


def _parse_date_v1(filename: str) -> str:
    matched = RawData.DATE_PATTERN_V1.match(filename)
    if not matched:
        raise ValueError(f"does not match date pattern: {filename}")
    date = _datetime.strptime(matched.group(1), '%Y-%m-%d')
    return date.strftime('%y%m%d')


def _parse_animal_ID(animal: str) -> int:
    idx = animal.index('#')
    return int(animal[(idx + 1):])

