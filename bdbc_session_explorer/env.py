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

"""retrieves values from the environment.

The default values may be supplied from environment variables:
- BDBC_SESSION_ROOT: root directory for session metadata files
- BDBC_RAWDATA_ROOT: root directory for raw-data HDF files
- BDBC_VIDEOS_ROOT: root directory for video files
- BDBC_MESOSCALER_ROOT: root directory for mesoscaler (atlas registration) files
- BDBC_<view>MODEL_DIR: the DeepLabCut project directory for <view> (body/face/eye) model
- BDBC_<view>RESULTS_ROOT: root directory for DeepLabCut results files of <view> (body/face/eye) model
- BDBC_PUPILFITTING_ROOT: root directory for pupil-fitting results files
- BDBC_PUBLICATION_ROOT: root directory for the resulting NWB files

Some values may also be overridden by additional environment variables
(by default, the metadata from BDBC_SESSION_ROOT will be used):
- BDBC_ANIMAL_STRAIN: the animal strain used for the experiments
- BDBC_TASK_TYPE: the type of the task
"""

from typing import Optional, Any
from pathlib import Path
import os as _os
import json as _json

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


GeneralInfo = dict[str, str]
TrialSpec = dict[str, Any]
TrialSpecSet = dict[str, TrialSpec]


def animal_strain_prefix(
    strain: Optional[str] = None,
    general_info: Optional[GeneralInfo] = None,
    sessionroot: Optional[PathLike] = None,
) -> str:
    if strain is None:
        strain = _os.environ.get('BDBC_ANIMAL_STRAIN', None)
    if strain is None:
        try:
            general_info = get_general_info(general_info, sessionroot)
            strain = general_info['animal_strain_prefix']
        except FileNotFoundError:
            pass
    if strain is None:
        raise ValueError("specify 'animal_strain', specify the BDBC_ANIMAL_STRAIN environment variable, or define metadata/general.json under BDBC_SESSION_ROOT")
    return str(strain)


def task_type(
    tasktype: Optional[str] = None,
    general_info: Optional[GeneralInfo] = None,
    sessionroot: Optional[PathLike] = None
) -> str:
    if tasktype is None:
        tasktype = _os.environ.get('BDBC_TASK_TYPE', None)
    if tasktype is None:
        try:
            general_info = get_general_info(general_info, sessionroot)
            tasktype = general_info['task_type']
        except FileNotFoundError:
            pass
    if tasktype is None:
        raise ValueError("specify 'tasktype', specify the BDBC_TASK_TYPE environment variable, or define metadata/general.json under BDBC_SESSION_ROOT")
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
    elif isinstance(rawroot, str):
        return tuple(Path(item) for item in str(rawroot).split(PATHSEP) if len(item) > 0)
    elif isinstance(rawroot, Path):
        return (rawroot,)
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


def get_general_info(
    info: Optional[GeneralInfo] = None,
    sessionroot: Optional[PathLike] = None,
) -> GeneralInfo:
    if info is None:
        sessroot = sessions_root_dir(sessionroot)
        infofile = sessroot / "metadata" / "general.json"
        if not infofile.exists():
            raise FileNotFoundError(str(infofile))
        with open(infofile, 'r') as src:
            info = _json.load(src)
    return info


def get_trials_metadata(
    metadata: Optional[TrialSpecSet] = None,
    sessionroot: Optional[PathLike] = None
) -> TrialSpecSet:
    if metadata is None:
        sessroot = sessions_root_dir(sessionroot)
        trialspec_dir = sessroot / "metadata" / "trials"
        if not trialspec_dir.exists():
            raise FileNotFoundError(str(trialspec_dir))

        metadata = {}
        for specfile in trialspec_dir.glob('*.json'):
            with open(specfile, 'r') as src:
                metadata[specfile.stem] = _json.load(src)
        if "task" not in metadata.keys():
            raise KeyError(f"'task' trial type not found in: {str(trialspec_dir)}")
    return metadata
