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
from pathlib import Path

import pupilfitting as _pupf

from . import (
    core as _core,
    session as _session,
    dlc as _dlc,
)


def fit_pupil(
    dlc_output: _dlc.DLCOutputFiles,
    pupilfile: Path,
    likelihood_threshold: float = 0.9999,
    min_valid_points: int = 15,
    overwrite: bool = False,
    verbose: bool = True,
) -> Path:
    if dlc_output.eye is None:
        raise FileNotFoundError(f"eye file not found in: {dlc_output.directory}")
    session = dlc_output.session
    
    # FIXME: compare update timestamp with `dlcoutput.eye`
    if (not overwrite) and pupilfile.exists():
        _core.message(f"{session.date}_{session.animal}: pupil already fitted", verbose=verbose)
        return
    process_eye_file(
        eyefile=dlc_output.eye,
        pupilfile=pupilfile,
        likelihood_threshold=likelihood_threshold,
        min_valid_points=min_valid_points,
        verbose=verbose
    )
    return pupilfile


def process_eye_file(
    eyefile: Path,
    pupilfile: Path,
    likelihood_threshold: float = 0.9999,
    min_valid_points: int = 15,
    desc: str = 'fitting',
    verbose: bool = True,
):
    pupil = _pupf.fit_hdf(
        eyefile,
        likelihood_threshold=likelihood_threshold,
        min_valid_points=min_valid_points,
        desc=desc,
        verbose=verbose,
    )
    if not pupilfile.parent.exists():
        pupilfile.parent.mkdir(parents=True)
    pupil.to_hdf(str(pupilfile), key='df_with_missing')


def find_pupil_output_dir(session: _session.Session, pupilroot: Path) -> Path:
    return pupilroot / f"{session.shortdate}_{session.animal}"


def locate_pupil_file(
    session: _session.Session,
    pupilroot: Path,
    locate_without_eyevideo: bool = False,
) -> Optional[Path]:
    if not session.has_eyevideo() and (not locate_without_eyevideo):
        return None
    pupildir = find_pupil_output_dir(session, pupilroot)
    return pupildir / f"{session.shortdate}_{session.animal}_pupilfitting.h5"

