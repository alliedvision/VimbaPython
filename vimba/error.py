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

from .util import Log

__all__ = [
    'VimbaSystemError',
    'VimbaCameraError',
    'VimbaInterfaceError',
    'VimbaFeatureError',
    'VimbaFrameError',
    'VimbaTimeout'
]


class _LoggedError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
        Log.get_instance().error(msg)


class VimbaSystemError(_LoggedError):
    """Errors related to the underlying Vimba System

    Error type to indicate system-wide errors like:
    - Incomplete Vimba installation
    - Incompatible version of the underlying C-Layer
    - An unsupported OS
    """
    pass


class VimbaCameraError(_LoggedError):
    """Errors related to cameras

    Error Type to indicated camera-related errors like:
    - Access of a disconnected Camera object
    - Lookup of non-existing cameras
    """
    pass


class VimbaInterfaceError(_LoggedError):
    """Errors related to Interfaces

    Error Type to indicated interface-related errors like:
    - Access on a disconnected Interface object
    - Lookup of a non-existing Interface
    """
    pass


class VimbaFeatureError(_LoggedError):
    """Error related to Feature access.

    Error type to indicate invalid Feature access like:
    - Invalid access mode on Feature access.
    - Out of range values upon setting a value.
    - Failed lookup of features.
    """
    pass


class VimbaFrameError(_LoggedError):
    """Error related to Frame data"""
    pass


class VimbaTimeout(_LoggedError):
    """Indicates that an operation timed out."""
    pass
