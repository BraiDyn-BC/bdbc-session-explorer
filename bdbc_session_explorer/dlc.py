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

from typing import Optional, Dict
from pathlib import Path
from collections import namedtuple as _namedtuple
import sys as _sys
import os as _os
import shutil as _shutil

from . import (
    core as _core,
    session as _session,
    videos as _videos,
)


def dlc_config_files() -> Dict[str, Path]:
    filename_cfg = 'config.yaml'
    configs = {
        'eye': Path(_os.environ['DLC_EYEMODEL_DIR']) / filename_cfg,
        'face': Path(_os.environ['DLC_FACEMODEL_DIR']) / filename_cfg,
        'body': Path(_os.environ['DLC_BODYMODEL_DIR']) / filename_cfg,
    }
    assert all(config.exists() for config in configs.values())
    return configs


class DLCOutputFiles(_namedtuple('DLCOutput', ('session', 'directory', 'body', 'face', 'eye'))):
    LABELS = {
        'body': 'Front',
        'face': 'Side',
        'eye': 'Eye',
    }


def ensure_dlc_output(
    videos: _videos.VideoFiles,
    dlcroot: Path,
    overwrite: bool = False,
    verbose: bool = True,
) -> DLCOutputFiles:
    configs = dlc_config_files()
    session = videos.session
    status  = dlc_output_files_from_session(session, dlcroot)

    if (not overwrite) and all((getattr(status, dtype) is not None) for dtype in status.LABELS.keys()):
        _core.message(
            f"{session.date}_{session.animal}: all videos have been already analyzed",
            verbose=verbose,
        )

    
    def _dlc_output(
        videopath: Path
    ) -> Optional[Path]:
        candidates = list(videopath.parent.glob(f"{videopath.stem}DLC*.h5"))
        if len(candidates) > 1:
            raise RuntimeError(f"{len(candidates)} candidates found for DLC output: {videopath.name}")
        elif len(candidates) == 0:
            return None
        else:
            return candidates[0]

    try:
        import deeplabcut as _dlc
    except ImportError:
        _dlc = None
    if _dlc is None:
        raise NotImplementedError("install DeepLabCut to run this procedure")

    temp_videos = videos.copy_to_temp(verbose=verbose)
    computed = dict()
    try:
        for vtype in temp_videos.LABELS.keys():
            vpath = getattr(temp_videos, vtype)
            if vpath is None:
                continue
            if (not overwrite) and (getattr(status, vtype) is not None):
                _core.message(
                    f"{session.date}_{session.animal}: {vtype} video has been already analyzed",
                    verbose=verbose,
                )
                continue
            _dlc.analyze_videos(
                str(configs[vtype]),
                [str(vpath)],
                gputouse=0,
            )
            output = _dlc_output(vpath)
            _sys.stdout.flush()
            _core.message(
                f"{session.date}_{session.animal}: {vtype}: copying the results...",
                end='',
                verbose=verbose
            )
            dlcpath = status.directory / output.name
            if dlcpath.exists():
                dlcpath.unlink()
            _shutil.move(output, dlcpath)
            _core.message("done.", verbose=verbose)

        return status._replace(**computed)
    finally:
        _shutil.rmtree(temp_videos.directory)


def dlc_output_files_from_session(
    session: _session.Session,
    dlcroot: Path,
) -> DLCOutputFiles:
    dlcdir = find_dlc_output_dir(session, dlcroot)
    files = dict()
    for dtype, label in DLCOutputFiles.LABELS.items():
        try:
            dpath = find_dlc_output(dlcdir, dtype, label)
        except ValueError:
            dpath = None
        files[dtype] = dpath
    return DLCOutputFiles(
        session=session,
        directory=dlcdir,
        **files
    )


def find_dlc_output_dir(session: _session.Session, dlcroot: Path) -> Path:
    basename = f"{session.shortdate}_{session.animal}"
    if session.type != 'task':
        basename += f"_{session.shorttype}"
    return dlcroot / basename


def find_dlc_output(dlcdir: Path, dtype: str = 'eye', label: str = 'Eye') -> Optional[Path]:
    candidates = list(dlcdir.glob(f'*_{label}_*DLC*.h5'))
    if len(candidates) > 1:
        raise ValueError(f"{dlcdir.name}: {len(candidates)} candidates found for '{dtype}'")
    elif len(candidates) == 0:
        return None
    return candidates[0]

