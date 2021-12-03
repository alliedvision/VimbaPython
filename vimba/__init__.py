"""BSD 2-Clause License

Copyright (c) 2019, Allied Vision Technologies GmbH
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# Suppress 'imported but unused' - Error from static style checker.
# flake8: noqa: F401

__version__ = '1.2.0'

__all__ = [
    'Vimba',
    'Camera',
    'CameraChangeHandler',
    'CameraEvent',
    'AccessMode',
    'PersistType',
    'Interface',
    'InterfaceType',
    'InterfaceChangeHandler',
    'InterfaceEvent',
    'PixelFormat',
    'Frame',
    'FeatureTypes',
    'FrameHandler',
    'FrameStatus',
    'AllocationMode',
    'Debayer',
    'intersect_pixel_formats',
    'MONO_PIXEL_FORMATS',
    'BAYER_PIXEL_FORMATS',
    'RGB_PIXEL_FORMATS',
    'RGBA_PIXEL_FORMATS',
    'BGR_PIXEL_FORMATS',
    'BGRA_PIXEL_FORMATS',
    'YUV_PIXEL_FORMATS',
    'YCBCR_PIXEL_FORMATS',
    'COLOR_PIXEL_FORMATS',
    'OPENCV_PIXEL_FORMATS',

    'VimbaSystemError',
    'VimbaCameraError',
    'VimbaInterfaceError',
    'VimbaFeatureError',
    'VimbaFrameError',
    'VimbaTimeout',

    'IntFeature',
    'FloatFeature',
    'StringFeature',
    'BoolFeature',
    'EnumEntry',
    'EnumFeature',
    'CommandFeature',
    'RawFeature',

    'LogLevel',
    'LogConfig',
    'Log',
    'LOG_CONFIG_TRACE_CONSOLE_ONLY',
    'LOG_CONFIG_TRACE_FILE_ONLY',
    'LOG_CONFIG_TRACE',
    'LOG_CONFIG_INFO_CONSOLE_ONLY',
    'LOG_CONFIG_INFO_FILE_ONLY',
    'LOG_CONFIG_INFO',
    'LOG_CONFIG_WARNING_CONSOLE_ONLY',
    'LOG_CONFIG_WARNING_FILE_ONLY',
    'LOG_CONFIG_WARNING',
    'LOG_CONFIG_ERROR_CONSOLE_ONLY',
    'LOG_CONFIG_ERROR_FILE_ONLY',
    'LOG_CONFIG_ERROR',
    'LOG_CONFIG_CRITICAL_CONSOLE_ONLY',
    'LOG_CONFIG_CRITICAL_FILE_ONLY',
    'LOG_CONFIG_CRITICAL',

    'TraceEnable',
    'ScopedLogEnable',
    'RuntimeTypeCheckEnable'
]

# Import everything exported from the top level module
from .vimba import Vimba

from .camera import AccessMode, PersistType, Camera, CameraChangeHandler, CameraEvent, FrameHandler

from .interface import Interface, InterfaceType, InterfaceChangeHandler, InterfaceEvent

from .frame import PixelFormat, Frame, Debayer, intersect_pixel_formats, MONO_PIXEL_FORMATS, \
                   BAYER_PIXEL_FORMATS, RGB_PIXEL_FORMATS, RGBA_PIXEL_FORMATS, BGR_PIXEL_FORMATS, \
                   BGRA_PIXEL_FORMATS, YUV_PIXEL_FORMATS, YCBCR_PIXEL_FORMATS, \
                   COLOR_PIXEL_FORMATS, OPENCV_PIXEL_FORMATS, FrameStatus, FeatureTypes, \
                   AllocationMode

from .error import VimbaSystemError, VimbaCameraError, VimbaInterfaceError, VimbaFeatureError, \
                   VimbaFrameError, VimbaTimeout

from .feature import IntFeature, FloatFeature, StringFeature, BoolFeature, EnumEntry, EnumFeature, \
                     CommandFeature, RawFeature

from .util import Log, LogLevel, LogConfig, LOG_CONFIG_TRACE_CONSOLE_ONLY, \
                  LOG_CONFIG_TRACE_FILE_ONLY, LOG_CONFIG_TRACE, LOG_CONFIG_INFO_CONSOLE_ONLY, \
                  LOG_CONFIG_INFO_FILE_ONLY, LOG_CONFIG_INFO, LOG_CONFIG_WARNING_CONSOLE_ONLY, \
                  LOG_CONFIG_WARNING_FILE_ONLY, LOG_CONFIG_WARNING, LOG_CONFIG_ERROR_CONSOLE_ONLY, \
                  LOG_CONFIG_ERROR_FILE_ONLY, LOG_CONFIG_ERROR, LOG_CONFIG_CRITICAL_CONSOLE_ONLY, \
                  LOG_CONFIG_CRITICAL_FILE_ONLY, LOG_CONFIG_CRITICAL, ScopedLogEnable, \
                  TraceEnable, RuntimeTypeCheckEnable
