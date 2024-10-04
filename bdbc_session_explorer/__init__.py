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

from importlib import reload as _reload

from . import (
    core,
    session,
    rawdata,
    videos,
    dlc,
    pupil,
    mesoscaler,
)

_reload(core)
_reload(session)
_reload(rawdata)
_reload(videos)
_reload(dlc)
_reload(pupil)
_reload(mesoscaler)

Session = session.Session
RawData = rawdata.RawData
RawFileVersion = rawdata.RawFileVersion
VideoFiles = videos.VideoFiles
DLCOutputFiles = dlc.DLCOutputFiles

iterate_sessions = session.iterate_sessions
rawdata_from_session = rawdata.rawdata_from_session
locate_rawdata_file = rawdata.locate_rawdata_file
video_files_from_session = videos.video_files_from_session
dlc_output_files_from_session = dlc.dlc_output_files_from_session
ensure_dlc_output = dlc.ensure_dlc_output
locate_pupil_file = pupil.locate_pupil_file
fit_pupil = pupil.fit_pupil
locate_mesoscaler_file = mesoscaler.locate_mesoscaler_file
