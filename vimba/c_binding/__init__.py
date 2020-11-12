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

-------------------------------------------------------------------------

NOTE: Vimba/Vmb naming convention.
VimbaPython is based heavily on VimbaC, this submodule contains all wrapped types and functions
of VimbaC. All VimbaC Types and Functions are prefixed with 'Vmb', this convention is kept for
all python types interfacing with the C - Layer. VimbaC developers should be able to understand
the interface to VimbaC and keeping the name convention helps a lot in that regard.

However prefixing everything with 'Vmb' is not required in VimbaPython, therefore most Types
of the public API have no prefix.
"""

# Suppress 'imported but unused' - Error from static style checker.
# flake8: noqa: F401

__all__ = [
    # Exports from vimba_common
    'VmbInt8',
    'VmbUint8',
    'VmbInt16',
    'VmbUint16',
    'VmbInt32',
    'VmbUint32',
    'VmbInt64',
    'VmbUint64',
    'VmbHandle',
    'VmbBool',
    'VmbUchar',
    'VmbDouble',
    'VmbError',
    'VimbaCError',
    'VmbPixelFormat',
    'decode_cstr',
    'decode_flags',

    # Exports from vimba_c
    'VmbInterface',
    'VmbAccessMode',
    'VmbFeatureData',
    'VmbFeaturePersist',
    'VmbFeatureVisibility',
    'VmbFeatureFlags',
    'VmbFrameStatus',
    'VmbFrameFlags',
    'VmbVersionInfo',
    'VmbInterfaceInfo',
    'VmbCameraInfo',
    'VmbFeatureInfo',
    'VmbFeatureEnumEntry',
    'VmbFrame',
    'VmbFeaturePersistSettings',
    'G_VIMBA_C_HANDLE',
    'VIMBA_C_VERSION',
    'EXPECTED_VIMBA_C_VERSION',
    'call_vimba_c',
    'build_callback_type',

    # Exports from vimba_image_transform
    'VmbImage',
    'VmbImageInfo',
    'VmbDebayerMode',
    'VmbTransformInfo',
    'VIMBA_IMAGE_TRANSFORM_VERSION',
    'EXPECTED_VIMBA_IMAGE_TRANSFORM_VERSION',
    'call_vimba_image_transform',
    'PIXEL_FORMAT_TO_LAYOUT',
    'LAYOUT_TO_PIXEL_FORMAT',
    'PIXEL_FORMAT_CONVERTIBILITY_MAP',

    # Exports from ctypes
    'byref',
    'sizeof',
    'create_string_buffer'
]

from .vimba_common import VmbInt8, VmbUint8, VmbInt16, VmbUint16, VmbInt32, VmbUint32, \
                          VmbInt64, VmbUint64, VmbHandle, VmbBool, VmbUchar, VmbDouble, VmbError, \
                          VimbaCError, VmbPixelFormat, decode_cstr, decode_flags, \
                          _select_vimba_home

from .vimba_c import VmbInterface, VmbAccessMode, VmbFeatureData, \
                   VmbFeaturePersist, VmbFeatureVisibility, VmbFeatureFlags, VmbFrameStatus, \
                   VmbFrameFlags, VmbVersionInfo, VmbInterfaceInfo, VmbCameraInfo, VmbFeatureInfo, \
                   VmbFeatureEnumEntry, VmbFrame, VmbFeaturePersistSettings, \
                   G_VIMBA_C_HANDLE, EXPECTED_VIMBA_C_VERSION, VIMBA_C_VERSION, call_vimba_c, \
                   build_callback_type

from .vimba_image_transform import VmbImage, VmbImageInfo, VmbDebayerMode, \
                                   VIMBA_IMAGE_TRANSFORM_VERSION, \
                                   EXPECTED_VIMBA_IMAGE_TRANSFORM_VERSION, VmbTransformInfo, \
                                   call_vimba_image_transform, PIXEL_FORMAT_TO_LAYOUT, \
                                   LAYOUT_TO_PIXEL_FORMAT, PIXEL_FORMAT_CONVERTIBILITY_MAP

from ctypes import byref, sizeof, create_string_buffer
