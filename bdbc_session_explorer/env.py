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
import os as _os

from . import (
    core as _core,
)

PathLike = _core.PathLike
PathsLike = _core.PathsLike
PATHSEP  = ':'


VIDEO_VIEWS = {
    'body': 'Front',
    'face': 'Side',
    'eye': 'Eye',
}


def animal_strain_ID(strain: Optional[str] = None) -> str:
    if strain is None:
        strain = _os.environ.get('BDBC_ANIMAL_STRAIN', 'VG1-GC')
        if strain is None:
            raise ValueError("specify 'animal_strain' or the BDBC_ANIMAL_STRAIN environment variable")
    return str(strain)


def task_type(tasktype: Optional[str] = None) -> str:
    if tasktype is None:
        tasktype = _os.environ.get('BDBC_TASK_TYPE', 'cued-lever-pull')
        if tasktype is None:
            raise ValueError("specify 'tasktype' or the BDBC_TASK_TYPE environment variable")
    return str(tasktype)


def video_views() -> dict[str, str]:
    return VIDEO_VIEWS.copy()


def ensure_root_dir(
    name: str,
    envname: str,
    root: Optional[PathLike] = None,
) -> Path:
    if root is None:
        root = _os.environ.get(envname, None)
        if root is None:
            raise ValueError(f"specify `{name}` or the {envname} environment variable")
    return Path(root)


def sessions_root_dir(sessionroot: Optional[PathLike] = None) -> Path:
    return ensure_root_dir(
        name='sessionroot',
        envname='BDBC_SESSION_ROOT',
        root=sessionroot
    )


def rawdata_root_dirs(rawroot: Optional[PathsLike] = None) -> tuple[Path]:
    if rawroot is None:
        rawroot = _os.environ.get('BDBC_RAWDATA_ROOT', None)
        if rawroot is None:
            raise ValueError("specify `rawroot` or the BDBC_RAWDATA_ROOT environment variable")
        return tuple(Path(item) for item in str(rawroot).split(PATHSEP) if len(item) > 0)
    elif isinstance(rawroot, (str, Path)):
        return tuple(Path(item) for item in str(rawroot).split(PATHSEP) if len(item) > 0)
    else:
        return tuple(Path(item) for item in rawroot)


def mesoscaler_root_dir(mesoroot: Optional[PathLike] = None) -> Path:
    return ensure_root_dir(
        name='mesoroot',
        envname='BDBC_MESOSCALER_ROOT',
        root=mesoroot
    )


def videos_root_dir(videoroot: Optional[PathLike] = None) -> Path:
    return ensure_root_dir(
        name='videoroot',
        envname='BDBC_VIDEOS_ROOT',
        root=videoroot
    )


def dlc_model_dir(view: str, modeldir: Optional[PathLike] = None) -> Path:
    return ensure_root_dir(
        name=f'{view}_modeldir',
        envname=f'BDBC_{view.upper()}MODEL_DIR',
        root=modeldir
    )


def dlcresults_root_dir(view: str, dlcroot: Optional[PathLike] = None) -> Path:
    return ensure_root_dir(
        name='dlcroot',
        envname=f'BDBC_{view.upper()}RESULTS_ROOT',
        root=dlcroot
    )


def pupilfitting_root_dir(pupilroot: Optional[PathLike] = None) -> Path:
    return ensure_root_dir(
        name='pupilroot',
        envname='BDBC_PUPILFITTING_ROOT',
        root=pupilroot
    )


def publication_root_dir(nwbroot: Optional[PathLike] = None) -> Path:
    return ensure_root_dir(
        name='nwbroot',
        envname='BDBC_PUBLICATION_ROOT',
        root=nwbroot
    )
