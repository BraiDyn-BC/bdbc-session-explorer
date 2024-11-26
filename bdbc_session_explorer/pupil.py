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

from . import (
    core as _core,
    env as _env,
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
    try:
        import pupilfitting as pupf
        err = ''
    except ImportError as e:
        import sys
        err = str(e)
        pupf = None
    if pupf is None:
        raise RuntimeError(
            f"***failed to load 'ks-pupilfitting' package ({err}): pupil fitting cannot be performed",
            file=sys.stderr,
            flush=True,
        )

    pupil = pupf.fit_hdf(
        eyefile,
        likelihood_threshold=likelihood_threshold,
        min_valid_points=min_valid_points,
        desc=desc,
        verbose=verbose,
    )
    if not pupilfile.parent.exists():
        pupilfile.parent.mkdir(parents=True)
    pupil.to_hdf(str(pupilfile), key='df_with_missing')


def find_pupil_output_dir(session: _session.Session, pupilroot: Optional[Path]) -> Path:
    pupilroot = _env.pupilfitting_root_dir(pupilroot)
    shortdate = session.shortdate
    basename = f"{shortdate}_{session.animal}"
    if session.type != 'task':
        suffix = f"_{session.shorttype}"
        shortdate += suffix
        basename += suffix
    return pupilroot / shortdate / basename


def locate_pupil_file(
    session: _session.Session,
    pupilroot: Optional[Path],
    locate_without_eyevideo: bool = False,
) -> Optional[Path]:
    if not session.has_eyevideo() and (not locate_without_eyevideo):
        return None
    pupilroot = _env.pupilfitting_root_dir(pupilroot)
    pupildir = find_pupil_output_dir(session, pupilroot)
    if not pupildir.exists():
        _core.message(f"***directory does not exist: {pupildir}")
        return None
    candidates = tuple(pupildir.glob("*_pupilfitting.h5"))
    if len(candidates) > 1:
        raise ValueError(f"{pupildir.name}: {len(candidates)} candidates found for 'pupil'")
    elif len(candidates) == 0:
        _core.message(f"***file with pattern not found in: {pupildir}")
        return None
    return candidates[0]
