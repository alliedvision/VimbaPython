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

import enum
import ctypes
import copy
import functools

from typing import Optional, Tuple
from .c_binding import create_string_buffer, byref, sizeof, decode_flags
from .c_binding import call_vimba_c, call_vimba_image_transform, VmbFrameStatus, VmbFrameFlags, \
                       VmbFrame, VmbHandle, VmbPixelFormat, VmbImage, VmbDebayerMode, \
                       VmbTransformInfo, PIXEL_FORMAT_CONVERTIBILITY_MAP, PIXEL_FORMAT_TO_LAYOUT
from .feature import FeaturesTuple, FeatureTypes, FeatureTypeTypes, discover_features
from .shared import filter_features_by_name, filter_features_by_type, filter_features_by_category, \
                    attach_feature_accessors, remove_feature_accessors
from .util import TraceEnable, RuntimeTypeCheckEnable, EnterContextOnCall, LeaveContextOnCall, \
                  RaiseIfOutsideContext
from .error import VimbaFrameError, VimbaFeatureError

try:
    import numpy  # type: ignore

except ModuleNotFoundError:
    numpy = None


__all__ = [
    'PixelFormat',
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
    'FrameStatus',
    'Debayer',
    'Frame',
    'FrameTuple',
    'FormatTuple',
    'intersect_pixel_formats'
]


# Forward declarations
FrameTuple = Tuple['Frame', ...]
FormatTuple = Tuple['PixelFormat', ...]


class PixelFormat(enum.IntEnum):
    """Enum specifying all PixelFormats. Note: Not all Cameras support all Pixelformats.

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
    # Mono Formats
    Mono8 = VmbPixelFormat.Mono8
    Mono10 = VmbPixelFormat.Mono10
    Mono10p = VmbPixelFormat.Mono10p
    Mono12 = VmbPixelFormat.Mono12
    Mono12Packed = VmbPixelFormat.Mono12Packed
    Mono12p = VmbPixelFormat.Mono12p
    Mono14 = VmbPixelFormat.Mono14
    Mono16 = VmbPixelFormat.Mono16

    # Bayer Formats
    BayerGR8 = VmbPixelFormat.BayerGR8
    BayerRG8 = VmbPixelFormat.BayerRG8
    BayerGB8 = VmbPixelFormat.BayerGB8
    BayerBG8 = VmbPixelFormat.BayerBG8
    BayerGR10 = VmbPixelFormat.BayerGR10
    BayerRG10 = VmbPixelFormat.BayerRG10
    BayerGB10 = VmbPixelFormat.BayerGB10
    BayerBG10 = VmbPixelFormat.BayerBG10
    BayerGR12 = VmbPixelFormat.BayerGR12
    BayerRG12 = VmbPixelFormat.BayerRG12
    BayerGB12 = VmbPixelFormat.BayerGB12
    BayerBG12 = VmbPixelFormat.BayerBG12
    BayerGR12Packed = VmbPixelFormat.BayerGR12Packed
    BayerRG12Packed = VmbPixelFormat.BayerRG12Packed
    BayerGB12Packed = VmbPixelFormat.BayerGB12Packed
    BayerBG12Packed = VmbPixelFormat.BayerBG12Packed
    BayerGR10p = VmbPixelFormat.BayerGR10p
    BayerRG10p = VmbPixelFormat.BayerRG10p
    BayerGB10p = VmbPixelFormat.BayerGB10p
    BayerBG10p = VmbPixelFormat.BayerBG10p
    BayerGR12p = VmbPixelFormat.BayerGR12p
    BayerRG12p = VmbPixelFormat.BayerRG12p
    BayerGB12p = VmbPixelFormat.BayerGB12p
    BayerBG12p = VmbPixelFormat.BayerBG12p
    BayerGR16 = VmbPixelFormat.BayerGR16
    BayerRG16 = VmbPixelFormat.BayerRG16
    BayerGB16 = VmbPixelFormat.BayerGB16
    BayerBG16 = VmbPixelFormat.BayerBG16

    # RGB Formats
    Rgb8 = VmbPixelFormat.Rgb8
    Bgr8 = VmbPixelFormat.Bgr8
    Rgb10 = VmbPixelFormat.Rgb10
    Bgr10 = VmbPixelFormat.Bgr10
    Rgb12 = VmbPixelFormat.Rgb12
    Bgr12 = VmbPixelFormat.Bgr12
    Rgb14 = VmbPixelFormat.Rgb14
    Bgr14 = VmbPixelFormat.Bgr14
    Rgb16 = VmbPixelFormat.Rgb16
    Bgr16 = VmbPixelFormat.Bgr16

    # RGBA Formats
    Rgba8 = VmbPixelFormat.Rgba8
    Bgra8 = VmbPixelFormat.Bgra8
    Argb8 = VmbPixelFormat.Argb8
    Rgba10 = VmbPixelFormat.Rgba10
    Bgra10 = VmbPixelFormat.Bgra10
    Rgba12 = VmbPixelFormat.Rgba12
    Bgra12 = VmbPixelFormat.Bgra12
    Rgba14 = VmbPixelFormat.Rgba14
    Bgra14 = VmbPixelFormat.Bgra14
    Rgba16 = VmbPixelFormat.Rgba16
    Bgra16 = VmbPixelFormat.Bgra16
    Yuv411 = VmbPixelFormat.Yuv411
    Yuv422 = VmbPixelFormat.Yuv422
    Yuv444 = VmbPixelFormat.Yuv444

    # YCbCr Formats
    YCbCr411_8_CbYYCrYY = VmbPixelFormat.YCbCr411_8_CbYYCrYY
    YCbCr422_8_CbYCrY = VmbPixelFormat.YCbCr422_8_CbYCrY
    YCbCr8_CbYCr = VmbPixelFormat.YCbCr8_CbYCr

    def __str__(self):
        return self._name_

    def __repr__(self):
        return 'PixelFormat.{}'.format(str(self))

    def get_convertible_formats(self) -> Tuple['PixelFormat', ...]:
        formats = PIXEL_FORMAT_CONVERTIBILITY_MAP[VmbPixelFormat(self)]
        return tuple([PixelFormat(fmt) for fmt in formats])


MONO_PIXEL_FORMATS = (
    PixelFormat.Mono8,
    PixelFormat.Mono10,
    PixelFormat.Mono10p,
    PixelFormat.Mono12,
    PixelFormat.Mono12Packed,
    PixelFormat.Mono12p,
    PixelFormat.Mono14,
    PixelFormat.Mono16
)


BAYER_PIXEL_FORMATS = (
    PixelFormat.BayerGR8,
    PixelFormat.BayerRG8,
    PixelFormat.BayerGB8,
    PixelFormat.BayerBG8,
    PixelFormat.BayerGR10,
    PixelFormat.BayerRG10,
    PixelFormat.BayerGB10,
    PixelFormat.BayerBG10,
    PixelFormat.BayerGR12,
    PixelFormat.BayerRG12,
    PixelFormat.BayerGB12,
    PixelFormat.BayerBG12,
    PixelFormat.BayerGR12Packed,
    PixelFormat.BayerRG12Packed,
    PixelFormat.BayerGB12Packed,
    PixelFormat.BayerBG12Packed,
    PixelFormat.BayerGR10p,
    PixelFormat.BayerRG10p,
    PixelFormat.BayerGB10p,
    PixelFormat.BayerBG10p,
    PixelFormat.BayerGR12p,
    PixelFormat.BayerRG12p,
    PixelFormat.BayerGB12p,
    PixelFormat.BayerBG12p,
    PixelFormat.BayerGR16,
    PixelFormat.BayerRG16,
    PixelFormat.BayerGB16,
    PixelFormat.BayerBG16
)


RGB_PIXEL_FORMATS = (
    PixelFormat.Rgb8,
    PixelFormat.Rgb10,
    PixelFormat.Rgb12,
    PixelFormat.Rgb14,
    PixelFormat.Rgb16
)


RGBA_PIXEL_FORMATS = (
    PixelFormat.Rgba8,
    PixelFormat.Argb8,
    PixelFormat.Rgba10,
    PixelFormat.Rgba12,
    PixelFormat.Rgba14,
    PixelFormat.Rgba16
)


BGR_PIXEL_FORMATS = (
    PixelFormat.Bgr8,
    PixelFormat.Bgr10,
    PixelFormat.Bgr12,
    PixelFormat.Bgr14,
    PixelFormat.Bgr16
)


BGRA_PIXEL_FORMATS = (
    PixelFormat.Bgra8,
    PixelFormat.Bgra10,
    PixelFormat.Bgra12,
    PixelFormat.Bgra14,
    PixelFormat.Bgra16
)


YUV_PIXEL_FORMATS = (
    PixelFormat.Yuv411,
    PixelFormat.Yuv422,
    PixelFormat.Yuv444
)


YCBCR_PIXEL_FORMATS = (
    PixelFormat.YCbCr411_8_CbYYCrYY,
    PixelFormat.YCbCr422_8_CbYCrY,
    PixelFormat.YCbCr8_CbYCr
)


COLOR_PIXEL_FORMATS = BAYER_PIXEL_FORMATS + RGB_PIXEL_FORMATS + RGBA_PIXEL_FORMATS + \
                      BGR_PIXEL_FORMATS + BGRA_PIXEL_FORMATS + YUV_PIXEL_FORMATS + \
                      YCBCR_PIXEL_FORMATS


OPENCV_PIXEL_FORMATS = (
    PixelFormat.Mono8,
    PixelFormat.Bgr8,
    PixelFormat.Bgra8,
    PixelFormat.Mono16,
    PixelFormat.Bgr16,
    PixelFormat.Bgra16
)


class Debayer(enum.IntEnum):
    """Enum specifying debayer modes.

    Enum values:
        Mode2x2    - 2x2 with green averaging (this is the default if no debayering algorithm
                     is added as transformation option).
        Mode3x3    - 3x3 with equal green weighting per line (8-bit images only).
        ModeLCAA   - Debayering with horizontal local color anti-aliasing (8-bit images only).
        ModeLCAAV  - Debayering with horizontal and vertical local color anti-aliasing
        (            8-bit images only).
        ModeYuv422 - Debayering with YUV422-alike sub-sampling (8-bit images only).
    """
    Mode2x2 = VmbDebayerMode.Mode_2x2
    Mode3x3 = VmbDebayerMode.Mode_3x3
    ModeLCAA = VmbDebayerMode.Mode_LCAA
    ModeLCAAV = VmbDebayerMode.Mode_LCAAV
    ModeYuv422 = VmbDebayerMode.Mode_YUV422

    def __str__(self):
        return 'DebayerMode.{}'.format(self._name_)

    def __repr__(self):
        return str(self)


class FrameStatus(enum.IntEnum):
    """Enum specifying the current status of internal Frame data.

    Enum values:
        Complete   - Frame data is complete without errors.
        Incomplete - Frame could not be filled to the end.
        TooSmall   - Frame buffer was too small.
        Invalid    - Frame buffer was invalid.
    """

    Complete = VmbFrameStatus.Complete
    Incomplete = VmbFrameStatus.Incomplete
    TooSmall = VmbFrameStatus.TooSmall
    Invalid = VmbFrameStatus.Invalid


class AncillaryData:
    """Ancillary Data are created after enabling a Cameras 'ChunkModeActive' Feature.
    Ancillary Data are Features stored within a Frame.
    """
    @TraceEnable()
    @LeaveContextOnCall()
    def __init__(self, handle: VmbFrame):
        """Do not call directly. Get Object via Frame access method"""
        self.__handle: VmbFrame = handle
        self.__data_handle: VmbHandle = VmbHandle()
        self.__feats: FeaturesTuple = ()
        self.__context_cnt: int = 0

    @TraceEnable()
    def __enter__(self):
        if not self.__context_cnt:
            self._open()

        self.__context_cnt += 1
        return self

    @TraceEnable()
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__context_cnt -= 1

        if not self.__context_cnt:
            self._close()

    @RaiseIfOutsideContext()
    def get_all_features(self) -> FeaturesTuple:
        """Get all features in ancillary data.

        Returns:
            A set of all currently features stored in Ancillary Data.

        Raises:
            RuntimeError then called outside of "with" - statement.
        """
        return self.__feats

    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def get_features_by_type(self, feat_type: FeatureTypeTypes) -> FeaturesTuple:
        """Get all features in ancillary data of a specific type.

        Valid FeatureTypes are: IntFeature, FloatFeature, StringFeature, BoolFeature,
        EnumFeature, CommandFeature, RawFeature

        Arguments:
            feat_type - FeatureType used find features of that type.

        Returns:
            A all features of type 'feat_type'.

        Raises:
            RuntimeError then called outside of "with" - statement.
            TypeError if parameters do not match their type hint.
        """
        return filter_features_by_type(self.__feats, feat_type)

    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def get_features_by_category(self, category: str) -> FeaturesTuple:
        """Get all features in ancillary data of a specific category.

        Arguments:
            category - Category that should be used for filtering.

        Returns:
            A all features of category 'category'.

        Raises:
            RuntimeError then called outside of "with" - statement.
            TypeError if parameters do not match their type hint.
        """
        return filter_features_by_category(self.__feats, category)

    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def get_feature_by_name(self, feat_name: str) -> FeatureTypes:
        """Get a features in ancillary data by its name.

        Arguments:
            feat_name - Name used to find a feature.

        Returns:
            Feature with the associated name.

        Raises:
            RuntimeError then called outside of "with" - statement.
            TypeError if parameters do not match their type hint.
            VimbaFeatureError if no feature is associated with 'feat_name'.
        """
        feat = filter_features_by_name(self.__feats, feat_name)

        if not feat:
            raise VimbaFeatureError('Feature \'{}\' not found.'.format(feat_name))

        return feat

    @TraceEnable()
    @EnterContextOnCall()
    def _open(self):
        call_vimba_c('VmbAncillaryDataOpen', byref(self.__handle), byref(self.__data_handle))

        self.__feats = _replace_invalid_feature_calls(discover_features(self.__data_handle))
        attach_feature_accessors(self, self.__feats)

    @TraceEnable()
    @LeaveContextOnCall()
    def _close(self):
        remove_feature_accessors(self, self.__feats)
        self.__feats = ()

        call_vimba_c('VmbAncillaryDataClose', self.__data_handle)
        self.__data_handle = VmbHandle()


def _replace_invalid_feature_calls(feats: FeaturesTuple) -> FeaturesTuple:
    # AncillaryData are basically "lightweight" features. Calling most feature related
    # Functions with a AncillaryData - Handle leads to VimbaC Errors. This method decorates
    # all Methods that are unsafe to call with a decorator raising a RuntimeError.
    to_wrap = [
        'get_access_mode',
        'is_readable',
        'is_writeable',
        'register_change_handler',
        'get_increment',
        'get_range',
        'set'
    ]

    # Decorator raising a RuntimeError instead of delegating call to inner function.
    def invalid_call(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = 'Calling \'{}\' is invalid for AncillaryData Features.'
            raise RuntimeError(msg.format(func.__name__))

        return wrapper

    # Replace original implementation by injecting a surrounding decorator and
    # binding the resulting function as a method to the Feature instance.
    for f, a in [(f, a) for f in feats for a in to_wrap]:
        try:
            fn = invalid_call(getattr(f, a))
            setattr(f, a, fn.__get__(f))

        except AttributeError:
            pass

    return feats


class Frame:
    """This class allows access to Frames acquired by a camera. The Frame is basically
    a buffer that wraps image data and some metadata.
    """
    def __init__(self, buffer_size: int):
        """Do not call directly. Create Frames via Camera methods instead."""
        self._buffer = create_string_buffer(buffer_size)
        self._frame: VmbFrame = VmbFrame()

        # Setup underlaying Frame
        self._frame.buffer = ctypes.cast(self._buffer, ctypes.c_void_p)
        self._frame.bufferSize = sizeof(self._buffer)

    def __str__(self):
        msg = 'Frame(id={}, status={}, buffer={})'
        return msg.format(self._frame.frameID, str(FrameStatus(self._frame.receiveStatus)),
                          hex(self._frame.buffer))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        # VmbFrame contains Pointers and ctypes.Structure with Pointers can't be copied.
        # As a workaround VmbFrame contains a deepcopy-like Method performing deep copy of all
        # Attributes except PointerTypes. Those must be set manually after the copy operation.
        setattr(result, '_buffer', copy.deepcopy(self._buffer, memo))
        setattr(result, '_frame', self._frame.deepcopy_skip_ptr(memo))

        result._frame.buffer = ctypes.cast(result._buffer, ctypes.c_void_p)
        result._frame.bufferSize = sizeof(result._buffer)

        return result

    def get_buffer(self) -> ctypes.Array:
        """Get internal buffer object containing image data."""
        return self._buffer

    def get_buffer_size(self) -> int:
        """Get byte size of internal buffer."""
        return self._frame.bufferSize

    def get_image_size(self) -> int:
        """Get byte size of image data stored in buffer."""
        return self._frame.imageSize

    def get_ancillary_data(self) -> Optional[AncillaryData]:
        """Get AncillaryData.

        Frames acquired with cameras where Feature ChunkModeActive is enabled can contain
        ancillary data within the image data.

        Returns:
            None if Frame contains no ancillary data.
            AncillaryData if Frame contains ancillary data.
        """
        if not self._frame.ancillarySize:
            return None

        return AncillaryData(self._frame)

    def get_status(self) -> FrameStatus:
        """Returns current frame status."""
        return FrameStatus(self._frame.receiveStatus)

    def get_pixel_format(self) -> PixelFormat:
        """Get format of the acquired image data"""
        return PixelFormat(self._frame.pixelFormat)

    def get_height(self) -> Optional[int]:
        """Get image height in pixels.

        Returns:
            Image height in pixels if dimension data is provided by the camera.
            None if dimension data is not provided by the camera.
        """
        flags = decode_flags(VmbFrameFlags, self._frame.receiveFlags)

        if VmbFrameFlags.Dimension not in flags:
            return None

        return self._frame.height

    def get_width(self) -> Optional[int]:
        """Get image width in pixels.

        Returns:
            Image width in pixels if dimension data is provided by the camera.
            None if dimension data is not provided by the camera.
        """
        flags = decode_flags(VmbFrameFlags, self._frame.receiveFlags)

        if VmbFrameFlags.Dimension not in flags:
            return None

        return self._frame.width

    def get_offset_x(self) -> Optional[int]:
        """Get horizontal offset in pixels.

        Returns:
            Horizontal offset in pixel if offset data is provided by the camera.
            None if offset data is not provided by the camera.
        """
        flags = decode_flags(VmbFrameFlags, self._frame.receiveFlags)

        if VmbFrameFlags.Offset not in flags:
            return None

        return self._frame.offsetX

    def get_offset_y(self) -> Optional[int]:
        """Get vertical offset in pixels.

        Returns:
            Vertical offset in pixels if offset data is provided by the camera.
            None if offset data is not provided by the camera.
        """
        flags = decode_flags(VmbFrameFlags, self._frame.receiveFlags)

        if VmbFrameFlags.Offset not in flags:
            return None

        return self._frame.offsetY

    def get_id(self) -> Optional[int]:
        """Get Frame ID.

        Returns:
            Frame ID if the id is provided by the camera.
            None if frame id is not provided by the camera.
        """
        flags = decode_flags(VmbFrameFlags, self._frame.receiveFlags)

        if VmbFrameFlags.FrameID not in flags:
            return None

        return self._frame.frameID

    def get_timestamp(self) -> Optional[int]:
        """Get Frame timestamp.

        Returns:
            Timestamp if provided by the camera.
            None if timestamp is not provided by the camera.
        """
        flags = decode_flags(VmbFrameFlags, self._frame.receiveFlags)

        if VmbFrameFlags.Timestamp not in flags:
            return None

        return self._frame.timestamp

    @RuntimeTypeCheckEnable()
    def convert_pixel_format(self, target_fmt: PixelFormat,
                             debayer_mode: Optional[Debayer] = None):
        """Convert internal pixel format to given format.

        Note: This method allocates a new buffer for internal image data leading to some
        runtime overhead. For performance reasons, it might be better to set the value
        of the camera's 'PixelFormat' feature instead. In addition, a non-default debayer mode
        can be specified.

        Arguments:
            target_fmt - PixelFormat to convert to.
            debayer_mode - Non-default algorithm used to debayer images in Bayer Formats. If
                           no mode is specified, default debayering mode 'Mode2x2' is applied. If
                           the current format is no Bayer format, this parameter is silently
                           ignored.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if the current format can't be converted into 'target_fmt'. Convertible
                Formats can be queried via get_convertible_formats() of PixelFormat.
            AssertionError if image width or height can't be determined.
        """

        global BAYER_PIXEL_FORMATS

        # 1) Perform sanity checking
        fmt = self.get_pixel_format()

        if fmt == target_fmt:
            return

        if target_fmt not in fmt.get_convertible_formats():
            raise ValueError('Current PixelFormat can\'t be converted into given format.')

        # 2) Specify Transformation Input Image
        height = self._frame.height
        width = self._frame.width

        c_src_image = VmbImage()
        c_src_image.Size = sizeof(c_src_image)
        c_src_image.Data = ctypes.cast(self._buffer, ctypes.c_void_p)

        call_vimba_image_transform('VmbSetImageInfoFromPixelFormat', fmt, width, height,
                                   byref(c_src_image))

        # 3) Specify Transformation Output Image
        c_dst_image = VmbImage()
        c_dst_image.Size = sizeof(c_dst_image)

        layout, bits = PIXEL_FORMAT_TO_LAYOUT[VmbPixelFormat(target_fmt)]

        call_vimba_image_transform('VmbSetImageInfoFromInputImage', byref(c_src_image), layout,
                                   bits, byref(c_dst_image))

        # 4) Allocate Buffer and perform transformation
        img_size = int(height * width * c_dst_image.ImageInfo.PixelInfo.BitsPerPixel / 8)
        anc_size = self._frame.ancillarySize

        buf = create_string_buffer(img_size + anc_size)
        c_dst_image.Data = ctypes.cast(buf, ctypes.c_void_p)

        # 5) Setup Debayering mode if given.
        transform_info = VmbTransformInfo()
        if debayer_mode and (fmt in BAYER_PIXEL_FORMATS):
            call_vimba_image_transform('VmbSetDebayerMode', VmbDebayerMode(debayer_mode),
                                       byref(transform_info))

        # 6) Perform Transformation
        call_vimba_image_transform('VmbImageTransform', byref(c_src_image), byref(c_dst_image),
                                   byref(transform_info), 1)

        # 7) Copy ancillary data if existing
        if anc_size:
            src = ctypes.addressof(self._buffer) + self._frame.imageSize
            dst = ctypes.addressof(buf) + img_size

            ctypes.memmove(dst, src, anc_size)

        # 8) Update frame metadata
        self._buffer = buf
        self._frame.buffer = ctypes.cast(self._buffer, ctypes.c_void_p)
        self._frame.bufferSize = sizeof(self._buffer)
        self._frame.imageSize = img_size
        self._frame.pixelFormat = target_fmt

    def as_numpy_ndarray(self) -> 'numpy.ndarray':
        """Construct numpy.ndarray view on VimbaFrame.

        Returns:
            numpy.ndarray on internal image buffer.

        Raises:
            ImportError if numpy is not installed.
            VimbaFrameError if current PixelFormat can't be converted to a numpy.ndarray.
        """
        if numpy is None:
            raise ImportError('\'Frame.as_opencv_image()\' requires module \'numpy\'.')

        # Construct numpy overlay on underlaying image buffer
        height = self._frame.height
        width = self._frame.width
        fmt = self._frame.pixelFormat

        c_image = VmbImage()
        c_image.Size = sizeof(c_image)

        call_vimba_image_transform('VmbSetImageInfoFromPixelFormat', fmt, width, height,
                                   byref(c_image))

        layout = PIXEL_FORMAT_TO_LAYOUT.get(fmt)

        if not layout:
            msg = 'Can\'t construct numpy.ndarray for Pixelformat {}. ' \
                  'Use \'frame.convert_pixel_format()\' to convert to a different Pixelformat.'
            raise VimbaFrameError(msg.format(str(self.get_pixel_format())))

        bits_per_channel = layout[1]
        channels_per_pixel = c_image.ImageInfo.PixelInfo.BitsPerPixel // bits_per_channel

        return numpy.ndarray(shape=(height, width, channels_per_pixel), buffer=self._buffer,
                             dtype=numpy.uint8 if bits_per_channel == 8 else numpy.uint16)

    def as_opencv_image(self) -> 'numpy.ndarray':
        """Construct OpenCV compatible view on VimbaFrame.

        Returns:
            OpenCV compatible numpy.ndarray

        Raises:
            ImportError if numpy is not installed.
            ValueError if current pixel format is not compatible with opencv. Compatible
                       formats are in OPENCV_PIXEL_FORMATS.
        """
        global OPENCV_PIXEL_FORMATS

        if numpy is None:
            raise ImportError('\'Frame.as_opencv_image()\' requires module \'numpy\'.')

        fmt = self._frame.pixelFormat

        if fmt not in OPENCV_PIXEL_FORMATS:
            raise ValueError('Current Format \'{}\' is not in OPENCV_PIXEL_FORMATS'.format(
                             str(PixelFormat(self._frame.pixelFormat))))

        return self.as_numpy_ndarray()


@TraceEnable()
@RuntimeTypeCheckEnable()
def intersect_pixel_formats(fmts1: FormatTuple, fmts2: FormatTuple) -> FormatTuple:
    """Build intersection of two sets containing PixelFormat.

    Arguments:
        fmts1 - PixelFormats to intersect with fmts2
        fmts2 - PixelFormats to intersect with fmts1

    Returns:
        Set of PixelFormats that occur in fmts1 and fmts2

    Raises:
            TypeError if parameters do not match their type hint.
    """
    return tuple(set(fmts1).intersection(set(fmts2)))
