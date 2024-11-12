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

from typing import Optional, Iterator, ClassVar
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime as _datetime
import re as _re

import pandas as _pd

from . import (
    core as _core,
    env as _env,
)

PathLike = _core.PathLike
ANIMAL_ID_PATTERN = _re.compile(r'VG1-GC#([0-9]+)')


def parse_animal_ID(anifile: Path) -> int:
    grab = ANIMAL_ID_PATTERN.match(anifile.stem)
    if not grab:
        raise ValueError(f"failed to parse animal ID from file: {anifile.name}")
    return int(grab.group(1))


@dataclass
class Availability:
    rawdata: Optional[bool]
    bodyvideo: Optional[bool]
    facevideo: Optional[bool]
    eyevideo: Optional[bool]
    VIDEO_VIEWS: ClassVar[tuple[str]] = ('body', 'face', 'eye')

    def has_rawdata(self) -> bool:
        return (self.rawdata is not None) and (self.rawdata == True)

    def has_video(self, view: str) -> bool:
        val = getattr(self, f"{view}video")
        return (val is not None) and (val == True)

    def has_any_videos(self) -> bool:
        return any(self.has_video(view) for view in self.VIDEO_VIEWS)


@dataclass
class Session:
    batch: str
    animal: str
    date: _datetime
    type: str
    dayindex: int
    sessionindex: int
    availability: Availability
    description: str
    comments: str
    FMT_SHORT_DATE: ClassVar[str] = '%y%m%d'
    FMT_LONG_DATE: ClassVar[str]  = '%Y-%m-%d'
    SHORT_TYPES: ClassVar[dict[str, str]] = {
        'task': 'task',
        'resting-state': 'rest',
        'sensory-stim': 'ss',
    }
    LONG_TYPES: ClassVar[dict[str, str]] = {
        'task': 'task',
        'rest': 'resting-state',
        'ss': 'sensory-stim',
    }

    @property
    def escaped_animal(self) -> str:
        return self.animal.replace('-', '').replace('#', '-')

    @property
    def shortdate(self) -> str:
        return self.date.strftime(self.FMT_SHORT_DATE)

    @property
    def longdate(self) -> str:
        return self.date.strftime(self.FMT_LONG_DATE)

    @property
    def shorttype(self) -> str:
        return self.SHORT_TYPES[self.type]

    @property
    def longtype(self) -> str:
        return self.type

    @property
    def day(self) -> int:
        return self.dayindex

    @property
    def longday(self) -> str:
        if self.dayindex >= 0:
            return f"day{self.dayindex}"
        else:
            return f"day({self.dayindex})"

    @property
    def index(self) -> int:
        return self.sessionindex

    @property
    def shortbase(self) -> str:
        if self.type == 'task':
            return f"{self.shortdate}_{self.animal}"
        else:
            return f"{self.shortdate}_{self.animal}_{self.shorttype}"

    @property
    def longbase(self) -> str:
        return f"{self.animal}_{self.longdate}_{self.longtype}-{self.longday}"

    def has_rawdata(self) -> bool:
        return self.availability.has_rawdata()

    def has_any_videos(self) -> bool:
        return self.availability.has_any_videos()

    def has_bodyvideo(self) -> bool:
        return self.availability.has_video('body')

    def has_facevideo(self) -> bool:
        return self.availability.has_video('face')

    def has_eyevideo(self) -> bool:
        return self.availability.has_video('eye')

    def metadata(self) -> dict[str, str]:
        return {
            'batch': self.batch,
            'animal': self.animal,
            'date': self.longdate,
            'type': self.longtype,
            'dayindex': self.dayindex,
            'sessionindex': self.sessionindex,
            'rawdata': self.availability.rawdata,
            'bodyvideo': self.availability.bodyvideo,
            'facevideo': self.availability.facevideo,
            'eyevideo': self.availability.eyevideo,
            'description': self.description,
            'comments': self.comments,
        }


def iterate_sessions_from_root(
    sessroot: Optional[PathLike],
    animal_strain: Optional[str] = None,
) -> Iterator[Session]:
    sessroot = _env.sessions_root_dir(sessroot)
    animal_strain = _env.animal_strain_ID(animal_strain)
    for batchdir in sorted(Path(sessroot).glob("run*")):
        batch = batchdir.stem
        for anifile in sorted(batchdir.glob(f"{animal_strain}*.csv"), key=parse_animal_ID):
            yield from iterate_sessions_from_animal(anifile, batch=batch)


def iterate_sessions_from_animal(
    anifile: Path,
    batch: str,
) -> Iterator[Session]:
    animal = anifile.stem
    records = _pd.read_csv(str(anifile), sep=',', header=0)
    for (date,), sessions in records.groupby(['Date']):
        date = _datetime.strptime(date, Session.FMT_LONG_DATE)
        for i, (_, row) in enumerate(sessions.iterrows(), start=1):
            yield format_session_record(
                row,
                batch=batch,
                animal=animal,
                date=date,
                sessionindex=i,
            )


def format_session_record(
    row: _pd.Series,
    batch: str = 'NA',
    animal: str = 'NA',
    date: Optional[_datetime] = None,
    sessionindex: int = 0,
) -> Session:
    descs = tuple(item.strip() for item in row.Description.split(';'))
    desc = descs[0]
    comm = '; '.join(descs[1:]) if len(descs) > 1 else ''
    avail = Availability(
        rawdata=bool(row.Data > 0),
        bodyvideo=bool(row.Body > 0),
        facevideo=bool(row.Face > 0),
        eyevideo=bool(row.Eye > 0),
    )
    return Session(
        batch=batch,
        animal=animal,
        date=date,
        type=str(row.Type),
        dayindex=int(row.Day),
        sessionindex=sessionindex,
        availability=avail,
        description=desc,
        comments=comm,
    )
