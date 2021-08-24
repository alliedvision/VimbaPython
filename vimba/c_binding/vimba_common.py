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

import ctypes
import enum
import os
import sys
import platform
import functools
from typing import Tuple, List
from ..error import VimbaSystemError


__all__ = [
    'Int32Enum',
    'Uint32Enum',
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
    'VmbFloat',
    'VmbDouble',
    'VmbError',
    'VimbaCError',
    'VmbPixelFormat',
    'decode_cstr',
    'decode_flags',
    'fmt_repr',
    'fmt_enum_repr',
    'fmt_flags_repr',
    'load_vimba_lib'
]


# Types
class Int32Enum(enum.IntEnum):
    @classmethod
    def from_param(cls, obj):
        return ctypes.c_int(obj)


class Uint32Enum(enum.IntEnum):
    @classmethod
    def from_param(cls, obj):
        return ctypes.c_uint(obj)


# Aliases for vmb base types
VmbInt8 = ctypes.c_byte
VmbUint8 = ctypes.c_ubyte
VmbInt16 = ctypes.c_short
VmbUint16 = ctypes.c_ushort
VmbInt32 = ctypes.c_int
VmbUint32 = ctypes.c_uint
VmbInt64 = ctypes.c_longlong
VmbUint64 = ctypes.c_ulonglong
VmbHandle = ctypes.c_void_p
VmbBool = ctypes.c_bool
VmbUchar = ctypes.c_char
VmbFloat = ctypes.c_float
VmbDouble = ctypes.c_double


class VmbError(Int32Enum):
    """
    Enum containing error types returned
        Success         - No error
        InternalFault   - Unexpected fault in VimbaC or driver
        ApiNotStarted   - VmbStartup() was not called before the current
                          command
        NotFound        - The designated instance (camera, feature etc.)
                          cannot be found
        BadHandle       - The given handle is not valid
        DeviceNotOpen   - Device was not opened for usage
        InvalidAccess   - Operation is invalid with the current access mode
        BadParameter    - One of the parameters is invalid (usually an illegal
                          pointer)
        StructSize      - The given struct size is not valid for this version
                          of the API
        MoreData        - More data available in a string/list than space is
                          provided
        WrongType       - Wrong feature type for this access function
        InvalidValue    - The value is not valid; Either out of bounds or not
                          an increment of the minimum
        Timeout         - Timeout during wait
        Other           - Other error
        Resources       - Resources not available (e.g. memory)
        InvalidCall     - Call is invalid in the current context (callback)
        NoTL            - No transport layers are found
        NotImplemented_ - API feature is not implemented
        NotSupported    - API feature is not supported
        Incomplete      - A multiple registers read or write is partially
                          completed
        IO              - low level IO error in transport layer
    """
    Success = 0
    InternalFault = -1
    ApiNotStarted = -2
    NotFound = -3
    BadHandle = -4
    DeviceNotOpen = -5
    InvalidAccess = -6
    BadParameter = -7
    StructSize = -8
    MoreData = -9
    WrongType = -10
    InvalidValue = -11
    Timeout = -12
    Other = -13
    Resources = -14
    InvalidCall = -15
    NoTL = -16
    NotImplemented_ = -17
    NotSupported = -18
    Incomplete = -19
    IO = -20

    def __str__(self):
        return self._name_


class _VmbPixel(Uint32Enum):
    Mono = 0x01000000
    Color = 0x02000000


class _VmbPixelOccupy(Uint32Enum):
    Bit8 = 0x00080000
    Bit10 = 0x000A0000
    Bit12 = 0x000C0000
    Bit14 = 0x000E0000
    Bit16 = 0x00100000
    Bit24 = 0x00180000
    Bit32 = 0x00200000
    Bit48 = 0x00300000
    Bit64 = 0x00400000


class VmbPixelFormat(Uint32Enum):
    """
    Enum containing Pixelformats
    Mono formats:
        Mono8        - Monochrome, 8 bits (PFNC:Mono8)
        Mono10       - Monochrome, 10 bits in 16 bits (PFNC:Mono10)
        Mono10p      - Monochrome, 4x10 bits continuously packed in 40 bits
                       (PFNC:Mono10p)
        Mono12       - Monochrome, 12 bits in 16 bits (PFNC:Mono12)
        Mono12Packed - Monochrome, 2x12 bits in 24 bits (GEV:Mono12Packed)
        Mono12p      - Monochrome, 2x12 bits continuously packed in 24 bits
                       (PFNC:Mono12p)
        Mono14       - Monochrome, 14 bits in 16 bits (PFNC:Mono14)
        Mono16       - Monochrome, 16 bits (PFNC:Mono16)

    Bayer formats:
        BayerGR8        - Bayer-color, 8 bits, starting with GR line
                          (PFNC:BayerGR8)
        BayerRG8        - Bayer-color, 8 bits, starting with RG line
                          (PFNC:BayerRG8)
        BayerGB8        - Bayer-color, 8 bits, starting with GB line
                          (PFNC:BayerGB8)
        BayerBG8        - Bayer-color, 8 bits, starting with BG line
                          (PFNC:BayerBG8)
        BayerGR10       - Bayer-color, 10 bits in 16 bits, starting with GR
                          line (PFNC:BayerGR10)
        BayerRG10       - Bayer-color, 10 bits in 16 bits, starting with RG
                          line (PFNC:BayerRG10)
        BayerGB10       - Bayer-color, 10 bits in 16 bits, starting with GB
                          line (PFNC:BayerGB10)
        BayerBG10       - Bayer-color, 10 bits in 16 bits, starting with BG
                          line (PFNC:BayerBG10)
        BayerGR12       - Bayer-color, 12 bits in 16 bits, starting with GR
                          line (PFNC:BayerGR12)
        BayerRG12       - Bayer-color, 12 bits in 16 bits, starting with RG
                          line (PFNC:BayerRG12)
        BayerGB12       - Bayer-color, 12 bits in 16 bits, starting with GB
                          line (PFNC:BayerGB12)
        BayerBG12       - Bayer-color, 12 bits in 16 bits, starting with BG
                          line (PFNC:BayerBG12)
        BayerGR12Packed - Bayer-color, 2x12 bits in 24 bits, starting with GR
                          line (GEV:BayerGR12Packed)
        BayerRG12Packed - Bayer-color, 2x12 bits in 24 bits, starting with RG
                          line (GEV:BayerRG12Packed)
        BayerGB12Packed - Bayer-color, 2x12 bits in 24 bits, starting with GB
                          line (GEV:BayerGB12Packed)
        BayerBG12Packed - Bayer-color, 2x12 bits in 24 bits, starting with BG
                          line (GEV:BayerBG12Packed)
        BayerGR10p      - Bayer-color, 4x10 bits continuously packed in 40
                          bits, starting with GR line (PFNC:BayerGR10p)
        BayerRG10p      - Bayer-color, 4x10 bits continuously packed in 40
                          bits, starting with RG line (PFNC:BayerRG10p)
        BayerGB10p      - Bayer-color, 4x10 bits continuously packed in 40
                          bits, starting with GB line (PFNC:BayerGB10p)
        BayerBG10p      - Bayer-color, 4x10 bits continuously packed in 40
                          bits, starting with BG line (PFNC:BayerBG10p)
        BayerGR12p      - Bayer-color, 2x12 bits continuously packed in 24
                          bits, starting with GR line (PFNC:BayerGR12p)
        BayerRG12p      - Bayer-color, 2x12 bits continuously packed in 24
                          bits, starting with RG line (PFNC:BayerRG12p)
        BayerGB12p      - Bayer-color, 2x12 bits continuously packed in 24
                          bits, starting with GB line (PFNC:BayerGB12p)
        BayerBG12p      - Bayer-color, 2x12 bits continuously packed in 24
                          bits, starting with BG line (PFNC:BayerBG12p)
        BayerGR16       - Bayer-color, 16 bits, starting with GR line
                          (PFNC:BayerGR16)
        BayerRG16       - Bayer-color, 16 bits, starting with RG line
                          (PFNC:BayerRG16)
        BayerGB16       - Bayer-color, 16 bits, starting with GB line
                          (PFNC:BayerGB16)
        BayerBG16       - Bayer-color, 16 bits, starting with BG line
                          (PFNC:BayerBG16)

    RGB formats:
        Rgb8  - RGB, 8 bits x 3 (PFNC:RGB8)
        Bgr8  - BGR, 8 bits x 3 (PFNC:Bgr8)
        Rgb10 - RGB, 10 bits in 16 bits x 3 (PFNC:RGB10)
        Bgr10 - BGR, 10 bits in 16 bits x 3 (PFNC:BGR10)
        Rgb12 - RGB, 12 bits in 16 bits x 3 (PFNC:RGB12)
        Bgr12 - BGR, 12 bits in 16 bits x 3 (PFNC:BGR12)
        Rgb14 - RGB, 14 bits in 16 bits x 3 (PFNC:RGB14)
        Bgr14 - BGR, 14 bits in 16 bits x 3 (PFNC:BGR14)
        Rgb16 - RGB, 16 bits x 3 (PFNC:RGB16)
        Bgr16 - BGR, 16 bits x 3 (PFNC:BGR16)

    RGBA formats:
        Argb8  - ARGB, 8 bits x 4 (PFNC:RGBa8)
        Rgba8  - RGBA, 8 bits x 4, legacy name
        Bgra8  - BGRA, 8 bits x 4 (PFNC:BGRa8)
        Rgba10 - RGBA, 10 bits in 16 bits x 4
        Bgra10 - BGRA, 10 bits in 16 bits x 4
        Rgba12 - RGBA, 12 bits in 16 bits x 4
        Bgra12 - BGRA, 12 bits in 16 bits x 4
        Rgba14 - RGBA, 14 bits in 16 bits x 4
        Bgra14 - BGRA, 14 bits in 16 bits x 4
        Rgba16 - RGBA, 16 bits x 4
        Bgra16 - BGRA, 16 bits x 4

    YUV/YCbCr formats:
        Yuv411              -  YUV 411 with 8 bits (GEV:YUV411Packed)
        Yuv422              -  YUV 422 with 8 bits (GEV:YUV422Packed)
        Yuv444              -  YUV 444 with 8 bits (GEV:YUV444Packed)
        YCbCr411_8_CbYYCrYY -  Y´CbCr 411 with 8 bits
                               (PFNC:YCbCr411_8_CbYYCrYY) - identical to Yuv411
        YCbCr422_8_CbYCrY   -  Y´CbCr 422 with 8 bits
                               (PFNC:YCbCr422_8_CbYCrY) - identical to Yuv422
        YCbCr8_CbYCr        -  Y´CbCr 444 with 8 bits
                               (PFNC:YCbCr8_CbYCr) - identical to Yuv444
    """
    None_ = 0
    Mono8 = _VmbPixel.Mono | _VmbPixelOccupy.Bit8 | 0x0001
    Mono10 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x0003
    Mono10p = _VmbPixel.Mono | _VmbPixelOccupy.Bit10 | 0x0046
    Mono12 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x0005
    Mono12Packed = _VmbPixel.Mono | _VmbPixelOccupy.Bit12 | 0x0006
    Mono12p = _VmbPixel.Mono | _VmbPixelOccupy.Bit12 | 0x0047
    Mono14 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x0025
    Mono16 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x0007
    BayerGR8 = _VmbPixel.Mono | _VmbPixelOccupy.Bit8 | 0x0008
    BayerRG8 = _VmbPixel.Mono | _VmbPixelOccupy.Bit8 | 0x0009
    BayerGB8 = _VmbPixel.Mono | _VmbPixelOccupy.Bit8 | 0x000A
    BayerBG8 = _VmbPixel.Mono | _VmbPixelOccupy.Bit8 | 0x000B
    BayerGR10 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x000C
    BayerRG10 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x000D
    BayerGB10 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x000E
    BayerBG10 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x000F
    BayerGR12 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x0010
    BayerRG12 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x0011
    BayerGB12 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x0012
    BayerBG12 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x0013
    BayerGR12Packed = _VmbPixel.Mono | _VmbPixelOccupy.Bit12 | 0x002A
    BayerRG12Packed = _VmbPixel.Mono | _VmbPixelOccupy.Bit12 | 0x002B
    BayerGB12Packed = _VmbPixel.Mono | _VmbPixelOccupy.Bit12 | 0x002C
    BayerBG12Packed = _VmbPixel.Mono | _VmbPixelOccupy.Bit12 | 0x002D
    BayerGR10p = _VmbPixel.Mono | _VmbPixelOccupy.Bit10 | 0x0056
    BayerRG10p = _VmbPixel.Mono | _VmbPixelOccupy.Bit10 | 0x0058
    BayerGB10p = _VmbPixel.Mono | _VmbPixelOccupy.Bit10 | 0x0054
    BayerBG10p = _VmbPixel.Mono | _VmbPixelOccupy.Bit10 | 0x0052
    BayerGR12p = _VmbPixel.Mono | _VmbPixelOccupy.Bit12 | 0x0057
    BayerRG12p = _VmbPixel.Mono | _VmbPixelOccupy.Bit12 | 0x0059
    BayerGB12p = _VmbPixel.Mono | _VmbPixelOccupy.Bit12 | 0x0055
    BayerBG12p = _VmbPixel.Mono | _VmbPixelOccupy.Bit12 | 0x0053
    BayerGR16 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x002E
    BayerRG16 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x002F
    BayerGB16 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x0030
    BayerBG16 = _VmbPixel.Mono | _VmbPixelOccupy.Bit16 | 0x0031
    Rgb8 = _VmbPixel.Color | _VmbPixelOccupy.Bit24 | 0x0014
    Bgr8 = _VmbPixel.Color | _VmbPixelOccupy.Bit24 | 0x0015
    Rgb10 = _VmbPixel.Color | _VmbPixelOccupy.Bit48 | 0x0018
    Bgr10 = _VmbPixel.Color | _VmbPixelOccupy.Bit48 | 0x0019
    Rgb12 = _VmbPixel.Color | _VmbPixelOccupy.Bit48 | 0x001A
    Bgr12 = _VmbPixel.Color | _VmbPixelOccupy.Bit48 | 0x001B
    Rgb14 = _VmbPixel.Color | _VmbPixelOccupy.Bit48 | 0x005E
    Bgr14 = _VmbPixel.Color | _VmbPixelOccupy.Bit48 | 0x004A
    Rgb16 = _VmbPixel.Color | _VmbPixelOccupy.Bit48 | 0x0033
    Bgr16 = _VmbPixel.Color | _VmbPixelOccupy.Bit48 | 0x004B
    Argb8 = _VmbPixel.Color | _VmbPixelOccupy.Bit32 | 0x0016
    Rgba8 = Argb8
    Bgra8 = _VmbPixel.Color | _VmbPixelOccupy.Bit32 | 0x0017
    Rgba10 = _VmbPixel.Color | _VmbPixelOccupy.Bit64 | 0x005F
    Bgra10 = _VmbPixel.Color | _VmbPixelOccupy.Bit64 | 0x004C
    Rgba12 = _VmbPixel.Color | _VmbPixelOccupy.Bit64 | 0x0061
    Bgra12 = _VmbPixel.Color | _VmbPixelOccupy.Bit64 | 0x004E
    Rgba14 = _VmbPixel.Color | _VmbPixelOccupy.Bit64 | 0x0063
    Bgra14 = _VmbPixel.Color | _VmbPixelOccupy.Bit64 | 0x0050
    Rgba16 = _VmbPixel.Color | _VmbPixelOccupy.Bit64 | 0x0064
    Bgra16 = _VmbPixel.Color | _VmbPixelOccupy.Bit64 | 0x0051
    Yuv411 = _VmbPixel.Color | _VmbPixelOccupy.Bit12 | 0x001E
    Yuv422 = _VmbPixel.Color | _VmbPixelOccupy.Bit16 | 0x001F
    Yuv444 = _VmbPixel.Color | _VmbPixelOccupy.Bit24 | 0x0020
    YCbCr411_8_CbYYCrYY = _VmbPixel.Color | _VmbPixelOccupy.Bit12 | 0x003C
    YCbCr422_8_CbYCrY = _VmbPixel.Color | _VmbPixelOccupy.Bit16 | 0x0043
    YCbCr8_CbYCr = _VmbPixel.Color | _VmbPixelOccupy.Bit24 | 0x003A

    def __str__(self):
        return self._name_


class VimbaCError(Exception):
    """Error Type containing an error code from the C-Layer. This error code is highly context
       sensitive. All wrapped C-Functions that do not return VmbError.Success or None must
       raise a VimbaCError and the surrounding code must deal if the Error is possible.
    """

    def __init__(self, c_error: VmbError):
        super().__init__(repr(c_error))
        self.__c_error = c_error

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return 'VimbaCError({})'.format(repr(self.__c_error))

    def get_error_code(self) -> VmbError:
        """ Get contained Error Code """
        return self.__c_error


# Utility Functions
def _split_into_powers_of_two(num: int) -> Tuple[int, ...]:
    result = []
    for mask in [1 << i for i in range(32)]:
        if mask & num:
            result.append(mask)

    if not result:
        result.append(0)

    return tuple(result)


def _split_flags_into_enum(num: int, enum_type):
    return [enum_type(val) for val in _split_into_powers_of_two(num)]


def _repr_flags_list(enum_type, flag_val: int):
    values = _split_flags_into_enum(flag_val, enum_type)

    if values:
        def fold_func(acc, arg):
            return '{} {}'.format(acc, repr(arg))

        return functools.reduce(fold_func, values, '')

    else:
        return '{}'.format(repr(enum_type(0)))


def decode_cstr(val: bytes) -> str:
    """Converts c_char_p stored in interface structures to a str.

    Arguments:
        val - Byte sequence to convert into str.

    Returns:
        str represented by 'val'
    """
    return val.decode() if val else ''


def decode_flags(enum_type, enum_val: int):
    """Splits C-styled bit mask into a set of flags from a given Enumeration.

    Arguments:
        enum_val - Bit mask to decode.
        enum_type - Enum Type represented within 'enum_val'

    Returns:
        A set of all values of enum_type occurring in enum_val.

    Raises:
        Attribute error a set value is not within the given 'enum_type'.
    """

    return tuple(_split_flags_into_enum(enum_val, enum_type))


def fmt_repr(fmt: str, val):
    """Append repr to a format string."""
    return fmt.format(repr(val))


def fmt_enum_repr(fmt: str, enum_type, enum_val):
    """Append repr of a given enum type to a format string.

    Arguments:
        fmt - Format string
        enum_type - Enum Type to construct.
        enum_val - Enum value.

    Returns:
        formatted string
    """
    return fmt.format(repr(enum_type(enum_val)))


def fmt_flags_repr(fmt: str, enum_type, enum_val):
    """Append repr of a c-style flag value in the form of a set containing
       all bits set from a given enum_type.

    Arguments:
        fmt - Format string
        enum_type - Enum Type to construct.
        enum_val - Enum value.

    Returns:
        formatted string
    """
    return fmt.format(_repr_flags_list(enum_type, enum_val))


def load_vimba_lib(vimba_project: str):
    """ Load shared library shipped with the Vimba installation

    Arguments:
        vimba_project - Library name without prefix or extension

    Return:
        CDLL or WinDLL Handle on loaded library

    Raises:
        VimbaSystemError if given library could not be loaded.
    """

    platform_handlers = {
        'linux': _load_under_linux,
        'win32': _load_under_windows
    }

    if sys.platform not in platform_handlers:
        msg = 'Abort. Unsupported Platform ({}) detected.'
        raise VimbaSystemError(msg.format(sys.platform))

    return platform_handlers[sys.platform](vimba_project)


def _load_under_linux(vimba_project: str):
    # Construct VimbaHome based on TL installation paths
    path_list: List[str] = []
    tl32_path = os.environ.get('GENICAM_GENTL32_PATH', "")
    if tl32_path:
        path_list += tl32_path.split(':')
    tl64_path = os.environ.get('GENICAM_GENTL64_PATH', "")
    if tl64_path:
        path_list += tl64_path.split(':')

    # Remove empty strings from path_list if there are any.
    # Necessary because the GENICAM_GENTLXX_PATH variable might start with a :
    path_list = [path for path in path_list if path]

    # Early return if required variables are not set.
    if not path_list:
        raise VimbaSystemError('No TL detected. Please verify Vimba installation.')

    vimba_home_candidates: List[str] = []
    for path in path_list:
        vimba_home = os.path.dirname(os.path.dirname(os.path.dirname(path)))

        if vimba_home not in vimba_home_candidates:
            vimba_home_candidates.append(vimba_home)

    # Select the most likely directory from the candidates
    vimba_home = _select_vimba_home(vimba_home_candidates)

    arch = platform.machine()

    # Linux x86 64 Bit (Requires additional interpreter version check)
    if arch == 'x86_64':
        dir_ = 'x86_64bit' if _is_python_64_bit() else 'x86_32bit'

    # Linux x86 32 Bit
    elif arch in ('i386', 'i686'):
        dir_ = 'x86_32bit'

    # Linux arm 64 Bit (Requires additional interpreter version check)
    elif arch == 'aarch64':
        dir_ = 'arm_64bit' if _is_python_64_bit() else 'arm_32bit'

    # Linux arm 32 Bit:
    elif arch == 'armv7l':
        dir_ = 'arm_32bit'

    else:
        raise VimbaSystemError('Unknown Architecture \'{}\'. Abort'.format(arch))

    lib_name = 'lib{}.so'.format(vimba_project)
    lib_path = os.path.join(vimba_home, vimba_project, 'DynamicLib', dir_, lib_name)

    try:
        lib = ctypes.cdll.LoadLibrary(lib_path)

    except OSError as e:
        msg = 'Failed to load library \'{}\'. Please verify Vimba installation.'
        raise VimbaSystemError(msg.format(lib_path)) from e

    return lib


def _load_under_windows(vimba_project: str):
    vimba_home = os.environ.get('VIMBA_HOME')

    if vimba_home is None:
        raise VimbaSystemError('Variable VIMBA_HOME not set. Please verify Vimba installation.')

    load_64bit = True if (platform.machine() == 'AMD64') and _is_python_64_bit() else False
    lib_name = '{}.dll'.format(vimba_project)
    lib_path = os.path.join(vimba_home, vimba_project, 'Bin', 'Win64' if load_64bit else 'Win32',
                            lib_name)

    try:
        # Load Library with 64 Bit and use cdecl call convention
        if load_64bit:
            lib = ctypes.cdll.LoadLibrary(lib_path)

        # Load Library with 32 Bit and use stdcall call convention
        else:
            # Tell mypy to ignore this line to allow type checking on both windows and linux as
            # windll is not available on linux and would therefore produce an error there
            lib = ctypes.windll.LoadLibrary(lib_path)  # type: ignore

    except OSError as e:
        msg = 'Failed to load library \'{}\'. Please verify Vimba installation.'
        raise VimbaSystemError(msg.format(lib_path)) from e

    return lib


def _select_vimba_home(candidates: List[str]) -> str:
    """
    Select the most likely candidate for VIMBA_HOME from the given list of
    candidates

    Arguments:
        candidates - List of strings pointing to possible vimba home directories

    Return:
        Path that represents the most likely VIMBA_HOME directory

    Raises:
        VimbaSystemError if multiple VIMBA_HOME directories were found in candidates
    """
    most_likely_candidates = []
    for candidate in candidates:
        if 'vimba' in candidate.lower():
            most_likely_candidates.append(candidate)

    if len(most_likely_candidates) == 0:
        raise VimbaSystemError('No suitable Vimba installation found. The following paths '
                               'were considered: {}'.format(candidates))
    elif len(most_likely_candidates) > 1:
        raise VimbaSystemError('Multiple Vimba installations found. Can\'t decide which to select: '
                               '{}'.format(most_likely_candidates))

    return most_likely_candidates[0]


def _is_python_64_bit() -> bool:
    # Query if the currently running python interpreter is build as 64 bit binary.
    # The default method of getting this information seems to be rather hacky
    # (check if maxint > 2^32) but it seems to be the way to do this....
    return True if sys.maxsize > 2**32 else False
