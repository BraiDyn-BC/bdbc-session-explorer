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

from typing import Optional, Union
from typing_extensions import Self
from pathlib import Path
from dataclasses import dataclass
import sys as _sys
import shutil as _shutil

from . import (
    core as _core,
    env as _env,
    session as _session,
    videos as _videos,
)

PathLike = _core.PathLike


def dlc_config_files(**project_dirs) -> dict[str, Path]:
    filename_cfg = 'config.yaml'
    configs = dict()
    for view in _env.video_views().keys():
        projdir = _env.dlc_model_dir(
            view,
            modeldir=project_dirs.get(view, None),
        )
        configs[view] = projdir / filename_cfg
    assert all((config is not None) and config.exists() for config in configs.values())
    return configs


@dataclass
class DLCOutputFile:
    directory: Optional[Path] = None
    path: Optional[Path] = None

    @classmethod
    def empty(cls) -> Self:
        return cls(
            directory=None,
            path=None
        )

    @classmethod
    def from_path(cls, path: Optional[PathLike]) -> Self:
        if path is None:
            return cls.empty()
        path = _core.maybe_path(path)
        return cls(directory=path.parent, path=path)

    def __post_init__(self):
        self.directory = _core.maybe_path(self.directory)
        self.path = _core.maybe_path(self.path)
        if (self.directory is None) and (self.path is not None):
            self.directory = self.path.parent

    def is_available(self) -> bool:
        return (self.directory is not None) and (self.path is not None)


@dataclass
class DLCOutputFiles:
    session: Optional[_session.Session]
    body: DLCOutputFile
    face: DLCOutputFile
    eye: DLCOutputFile

    def __post_init__(self):
        if self.body is None:
            self.body = DLCOutputFile.empty()
        elif isinstance(self.body, (Path, str)):
            self.body = DLCOutputFile.from_path(self.body)
        if self.face is None:
            self.face = DLCOutputFile.empty()
        elif isinstance(self.face, (Path, str)):
            self.face = DLCOutputFile.from_path(self.face)
        if self.eye is None:
            self.eye = DLCOutputFile.empty()
        elif isinstance(self.eye, (Path, str)):
            self.eye = DLCOutputFile.from_path(self.eye)

    def has_all_files(self) -> bool:
        return all(getattr(self, view).is_available() for view in _env.video_views().keys())

    def replace(
        self,
        body: Optional[Union[PathLike, DLCOutputFile]] = None,
        face: Optional[Union[PathLike, DLCOutputFile]] = None,
        eye: Optional[Union[PathLike, DLCOutputFile]] = None,
    ) -> Self:
        return self.__class__(
            session=self.session,
            body=DLCOutputFile.from_path(body),
            face=DLCOutputFile.from_path(face),
            eye=DLCOutputFile.from_path(eye),
        )


def ensure_dlc_output(
    videos: _videos.VideoFiles,
    dlc_project_dirs: Optional[dict[str, Optional[Path]]] = None,
    dlc_output_dirs: Optional[dict[str, Optional[Path]]] = None,
    overwrite: bool = False,
    gpu_to_use: Optional[int] = 0,
    verbose: bool = True,
) -> DLCOutputFiles:
    if dlc_project_dirs is None:
        dlc_project_dirs = dict()
    if dlc_output_dirs is None:
        dlc_output_dirs = dict()
    configs = dlc_config_files(**dlc_project_dirs)
    session = videos.session
    files   = dlc_output_files_from_session(session, **dlc_output_dirs)

    if (not overwrite) and files.has_all_files():
        _core.message(
            f"{session.date}_{session.animal}: all videos have been already analyzed",
            verbose=verbose,
        )

    def _find_results_path(
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
        import deeplabcut as dlc
    except ImportError:
        dlc = None
    if dlc is None:
        raise NotImplementedError("install DeepLabCut to perform landmark estimation")

    temp_videos = videos.copy_to_temp(verbose=verbose)
    newly_computed = dict()
    try:
        for view in _env.video_views().keys():
            source_video: Optional[Path] = getattr(temp_videos, view)
            output_info: DLCOutputFile = getattr(files, view)
            project_config: str = str(configs[view])

            if source_video is None:
                continue
            if (not overwrite) and output_info.is_available():
                _core.message(
                    f"{session.date}_{session.animal}: {view} video has been already analyzed",
                    verbose=verbose,
                )
                continue

            dlc.analyze_videos(
                project_config,
                [str(source_video)],
                gputouse=gpu_to_use,
            )
            results_file = _find_results_path(source_video)
            _sys.stdout.flush()
            _core.message(
                f"{session.date}_{session.animal}: {view}: copying the results...",
                end='',
                verbose=verbose
            )
            output_path = output_info.directory / results_file.name
            if output_path.exists():
                output_path.unlink()
            elif not output_info.directory.exists():
                output_info.directory.mkdir(parents=True)
            _shutil.move(results_file, output_path)
            newly_computed[view] = output_path
            _core.message("done.", verbose=verbose)

        return files.replace(**newly_computed)
    finally:
        _shutil.rmtree(temp_videos.directory)


def dlc_output_files_from_session(
    session: _session.Session,
    **dlcroot,
) -> DLCOutputFiles:
    files = dict()
    for dtype, label in _env.video_views().items():
        resultsroot = _env.dlcresults_root_dir(dtype, dlcroot.get(dtype, None))
        resultsdir = find_dlc_output_dir(session, resultsroot)
        try:
            dpath = find_dlc_output(resultsdir, dtype, label)
        except ValueError:
            dpath = None
        files[dtype] = dpath
    return DLCOutputFiles(
        session=session,
        **files
    )


def find_dlc_output_dir(session: _session.Session, dlcroot: Path) -> Path:
    basename = f"{session.shortdate}_{session.animal}"
    if session.type != 'task':
        basename += f"_{session.shorttype}"
    return dlcroot / session.shortdate / basename


def find_dlc_output(dlcdir: Path, dtype: str = 'eye', label: str = 'Eye') -> Optional[Path]:
    candidates = list(dlcdir.glob(f'*_{label}_*DLC*.h5'))
    if len(candidates) > 1:
        raise ValueError(f"{dlcdir.name}: {len(candidates)} candidates found for '{dtype}'")
    elif len(candidates) == 0:
        return None
    return candidates[0]
