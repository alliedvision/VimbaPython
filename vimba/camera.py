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
import os
import copy
import threading

from ctypes import POINTER
from typing import Tuple, List, Callable, cast, Optional, Union, Dict
from .c_binding import call_vimba_c, build_callback_type, byref, sizeof, decode_cstr, decode_flags
from .c_binding import VmbCameraInfo, VmbHandle, VmbUint32, G_VIMBA_C_HANDLE, VmbAccessMode, \
                       VimbaCError, VmbError, VmbFrame, VmbFeaturePersist, VmbFeaturePersistSettings
from .feature import discover_features, discover_feature, FeatureTypes, FeaturesTuple, \
                     FeatureTypeTypes
from .shared import filter_features_by_name, filter_features_by_type, filter_affected_features, \
                    filter_selected_features, filter_features_by_category, \
                    attach_feature_accessors, remove_feature_accessors, read_memory, \
                    write_memory, read_registers, write_registers
from .frame import Frame, FormatTuple, PixelFormat
from .util import Log, TraceEnable, RuntimeTypeCheckEnable, EnterContextOnCall, \
                  LeaveContextOnCall, RaiseIfInsideContext, RaiseIfOutsideContext
from .error import VimbaSystemError, VimbaCameraError, VimbaTimeout, VimbaFeatureError


__all__ = [
    'AccessMode',
    'PersistType',
    'FrameHandler',
    'Camera',
    'CameraEvent',
    'CamerasTuple',
    'CamerasList',
    'CameraChangeHandler',
    'discover_cameras',
    'discover_camera'
]


# Type Forward declarations
CameraChangeHandler = Callable[['Camera', 'CameraEvent'], None]
CamerasTuple = Tuple['Camera', ...]
CamerasList = List['Camera']
FrameHandler = Callable[['Camera', Frame], None]


class AccessMode(enum.IntEnum):
    """Enum specifying all available camera access modes.

    Enum values:
        None_  - No access.
        Full   - Read and write access. Use this mode to configure the camera features and
                 to acquire images (Camera Link cameras: configuration only).
        Read   - Read-only access. Setting features is not possible.
        Config - Configuration access to configure the IP address of your GigE camera.
    """
    None_ = VmbAccessMode.None_
    Full = VmbAccessMode.Full
    Read = VmbAccessMode.Read
    Config = VmbAccessMode.Config


class CameraEvent(enum.IntEnum):
    """Enum specifying a Camera Event

    Enum values:
        Missing     - A known camera disappeared from the bus
        Detected    - A new camera was discovered
        Reachable   - A known camera can be accessed
        Unreachable - A known camera cannot be accessed anymore
    """
    Missing = 0
    Detected = 1
    Reachable = 2
    Unreachable = 3


class PersistType(enum.IntEnum):
    """Persistence Type for camera configuration storing and loading.
    Enum values:
        All        - Save all features including lookup tables
        Streamable - Save only features tagged with Streamable
        NoLUT      - Save all features except lookup tables.
    """
    All = VmbFeaturePersist.All
    Streamable = VmbFeaturePersist.Streamable
    NoLUT = VmbFeaturePersist.NoLUT


class _Context:
    def __init__(self, cam, frames, handler, callback):
        self.cam = cam
        self.cam_handle = _cam_handle_accessor(cam)
        self.frames = frames
        self.frames_lock = threading.Lock()
        self.frames_handler = handler
        self.frames_callback = callback


class _State:
    def __init__(self, context: _Context):
        self.context = context


class _StateInit(_State):
    @TraceEnable()
    def forward(self) -> Union[_State, VimbaCameraError]:
        for frame in self.context.frames:
            frame_handle = _frame_handle_accessor(frame)

            try:
                call_vimba_c('VmbFrameAnnounce', self.context.cam_handle, byref(frame_handle),
                             sizeof(frame_handle))

            except VimbaCError as e:
                return _build_camera_error(self.context.cam, e)

        return _StateAnnounced(self.context)


class _StateAnnounced(_State):
    @TraceEnable()
    def forward(self) -> Union[_State, VimbaCameraError]:
        try:
            call_vimba_c('VmbCaptureStart', self.context.cam_handle)

        except VimbaCError as e:
            return _build_camera_error(self.context.cam, e)

        return _StateCapturing(self.context)

    @TraceEnable()
    def backward(self) -> Union[_State, VimbaCameraError]:
        for frame in self.context.frames:
            frame_handle = _frame_handle_accessor(frame)

            try:
                call_vimba_c('VmbFrameRevoke', self.context.cam_handle, byref(frame_handle))

            except VimbaCError as e:
                return _build_camera_error(self.context.cam, e)

        return _StateInit(self.context)


class _StateCapturing(_State):
    @TraceEnable()
    def forward(self) -> Union[_State, VimbaCameraError]:
        try:
            # Skip Command execution on AccessMode.Read (required for Multicast Streaming)
            if self.context.cam.get_access_mode() != AccessMode.Read:
                self.context.cam.get_feature_by_name('AcquisitionStart').run()

        except BaseException as e:
            return VimbaCameraError(str(e))

        return _StateAcquiring(self.context)

    @TraceEnable()
    def backward(self) -> Union[_State, VimbaCameraError]:
        try:
            call_vimba_c('VmbCaptureQueueFlush', self.context.cam_handle)

        except VimbaCError as e:
            return _build_camera_error(self.context.cam, e)

        return _StateAnnounced(self.context)


class _StateNotAcquiring(_State):
    @TraceEnable()
    def backward(self) -> Union[_State, VimbaCameraError]:
        try:
            call_vimba_c('VmbCaptureEnd', self.context.cam_handle)

        except VimbaCError as e:
            return _build_camera_error(self.context.cam, e)

        return _StateCapturing(self.context)


class _StateAcquiring(_State):
    @TraceEnable()
    def backward(self) -> Union[_State, VimbaCameraError]:
        try:
            # Skip Command execution on AccessMode.Read (required for Multicast Streaming)
            cam = self.context.cam
            if cam.get_access_mode() != AccessMode.Read:
                cam.get_feature_by_name('AcquisitionStop').run()

        except BaseException as e:
            return VimbaCameraError(str(e))

        return _StateNotAcquiring(self.context)

    @TraceEnable()
    def wait_for_frames(self, timeout_ms: int):
        for frame in self.context.frames:
            self.queue_frame(frame)

        for frame in self.context.frames:
            frame_handle = _frame_handle_accessor(frame)

            try:
                call_vimba_c('VmbCaptureFrameWait', self.context.cam_handle, byref(frame_handle),
                             timeout_ms)

            except VimbaCError as e:
                raise _build_camera_error(self.context.cam, e) from e

    @TraceEnable()
    def queue_frame(self, frame):
        frame_handle = _frame_handle_accessor(frame)

        try:
            call_vimba_c('VmbCaptureFrameQueue', self.context.cam_handle, byref(frame_handle),
                         self.context.frames_callback)

        except VimbaCError as e:
            raise _build_camera_error(self.context.cam, e) from e


class _CaptureFsm:
    def __init__(self, context: _Context):
        self.__context = context
        self.__state = _StateInit(self.__context)

    def get_context(self) -> _Context:
        return self.__context

    def enter_capturing_mode(self):
        # Forward state machine until the end or an error occurs
        exc = None

        while not exc:
            try:
                state_or_exc = self.__state.forward()

            except AttributeError:
                break

            if isinstance(state_or_exc, _State):
                self.__state = state_or_exc

            else:
                exc = state_or_exc

        return exc

    def leave_capturing_mode(self):
        # Revert state machine until the initial state is reached or an error occurs
        exc = None

        while not exc:
            try:
                state_or_exc = self.__state.backward()

            except AttributeError:
                break

            if isinstance(state_or_exc, _State):
                self.__state = state_or_exc

            else:
                exc = state_or_exc

        return exc

    def wait_for_frames(self, timeout_ms: int):
        # Wait for Frames only in AcquiringMode
        if isinstance(self.__state, _StateAcquiring):
            self.__state.wait_for_frames(timeout_ms)

    def queue_frame(self, frame):
        # Queue Frame only in AcquiringMode
        if isinstance(self.__state, _StateAcquiring):
            self.__state.queue_frame(frame)


@TraceEnable()
def _frame_generator(cam, limit: Optional[int], timeout_ms: int):
    if cam.is_streaming():
        raise VimbaCameraError('Operation not supported while streaming.')

    frame_data_size = cam.get_feature_by_name('PayloadSize').get()
    frames = (Frame(frame_data_size), )
    fsm = _CaptureFsm(_Context(cam, frames, None, None))
    cnt = 0

    try:
        while True if limit is None else cnt < limit:
            # Enter Capturing mode
            exc = fsm.enter_capturing_mode()
            if exc:
                raise exc

            fsm.wait_for_frames(timeout_ms)

            # Return copy of internally used frame to keep them independent.
            frame_copy = copy.deepcopy(frames[0])
            fsm.leave_capturing_mode()
            frame_copy._frame.frameID = cnt
            cnt += 1

            yield frame_copy

    finally:
        # Leave Capturing mode
        exc = fsm.leave_capturing_mode()
        if exc:
            raise exc


class Camera:
    """This class allows access to a Camera detected by Vimba.
    Camera is meant be used in conjunction with the "with" - statement.
    On entering a context, all Camera features are detected and can be accessed within the context.
    Static Camera properties like Name and Model can be accessed outside the context.
    """
    @TraceEnable()
    @LeaveContextOnCall()
    def __init__(self, info: VmbCameraInfo):
        """Do not call directly. Access Cameras via vimba.Vimba instead."""
        self.__handle: VmbHandle = VmbHandle(0)
        self.__info: VmbCameraInfo = info
        self.__access_mode: AccessMode = AccessMode.Full
        self.__feats: FeaturesTuple = ()
        self.__context_cnt: int = 0
        self.__capture_fsm: Optional[_CaptureFsm] = None
        self._disconnected = False

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

    def __str__(self):
        return 'Camera(id={})'.format(self.get_id())

    @RaiseIfInsideContext()
    @RuntimeTypeCheckEnable()
    def set_access_mode(self, access_mode: AccessMode):
        """Set camera access mode.

        Arguments:
            access_mode - AccessMode for accessing a Camera.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called inside "with" - statement scope.
        """
        self.__access_mode = access_mode

    def get_access_mode(self) -> AccessMode:
        """Get current camera access mode"""
        return self.__access_mode

    def get_id(self) -> str:
        """Get Camera Id, for example, DEV_1AB22C00041B"""
        return decode_cstr(self.__info.cameraIdString)

    def get_name(self) -> str:
        """Get Camera Name, for example, Allied Vision 1800 U-500m"""
        return decode_cstr(self.__info.cameraName)

    def get_model(self) -> str:
        """Get Camera Model, for example, 1800 U-500m"""
        return decode_cstr(self.__info.modelName)

    def get_serial(self) -> str:
        """Get Camera serial number, for example, 50-0503328442"""
        return decode_cstr(self.__info.serialString)

    def get_permitted_access_modes(self) -> Tuple[AccessMode, ...]:
        """Get a set of all access modes the camera can be accessed with."""
        val = self.__info.permittedAccess

        # Clear VmbAccessMode.Lite Flag. It is offered by VimbaC, but it is not documented.
        val &= ~int(VmbAccessMode.Lite)

        return decode_flags(AccessMode, val)

    def get_interface_id(self) -> str:
        """Get ID of the Interface this camera is connected to, for example, VimbaUSBInterface_0x0
        """
        return decode_cstr(self.__info.interfaceIdString)

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def read_memory(self, addr: int, max_bytes: int) -> bytes:  # coverage: skip
        """Read a byte sequence from a given memory address.

        Arguments:
            addr: Starting address to read from.
            max_bytes: Maximum number of bytes to read from addr.

        Returns:
            Read memory contents as bytes.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            ValueError if addr is negative.
            ValueError if max_bytes is negative.
            ValueError if the memory access was invalid.
        """
        # Note: Coverage is skipped. Function is untestable in a generic way.
        return read_memory(self.__handle, addr, max_bytes)

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def write_memory(self, addr: int, data: bytes):  # coverage: skip
        """Write a byte sequence to a given memory address.

        Arguments:
            addr: Address to write the content of 'data' too.
            data: Byte sequence to write at address 'addr'.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            ValueError if addr is negative.
        """
        # Note: Coverage is skipped. Function is untestable in a generic way.
        return write_memory(self.__handle, addr, data)

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def read_registers(self, addrs: Tuple[int, ...]) -> Dict[int, int]:  # coverage: skip
        """Read contents of multiple registers.

        Arguments:
            addrs: Sequence of addresses to be read iteratively.

        Returns:
            Dictionary containing a mapping from given address to the read register values.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            ValueError if any address in addrs is negative.
            ValueError if the register access was invalid.
        """
        # Note: Coverage is skipped. Function is untestable in a generic way.
        return read_registers(self.__handle, addrs)

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def write_registers(self, addrs_values: Dict[int, int]):  # coverage: skip
        """Write data to multiple registers.

        Arguments:
            addrs_values: Mapping between register addresses and the data to write.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            ValueError if any address in addrs_values is negative.
            ValueError if the register access was invalid.
        """
        # Note: Coverage is skipped. Function is untestable in a generic way.
        return write_registers(self.__handle, addrs_values)

    @RaiseIfOutsideContext()
    def get_all_features(self) -> FeaturesTuple:
        """Get access to all discovered features of this camera.

        Returns:
            A set of all currently detected features.

        Raises:
            RuntimeError if called outside "with" - statement scope.
        """
        return self.__feats

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def get_features_affected_by(self, feat: FeatureTypes) -> FeaturesTuple:
        """Get all features affected by a specific camera feature.

        Arguments:
            feat - Feature used, find features that are affected by 'feat'.

        Returns:
            A set of features affected by changes on 'feat'.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            VimbaFeatureError if 'feat' is not a feature of this camera.
        """
        return filter_affected_features(self.__feats, feat)

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def get_features_selected_by(self, feat: FeatureTypes) -> FeaturesTuple:
        """Get all features selected by a specific camera feature.

        Arguments:
            feat - Feature to find features that are selected by 'feat'.

        Returns:
            A feature set selected by changes on 'feat'.

        Raises:
            TypeError if 'feat' is not of any feature type.
            RuntimeError if called outside "with" - statement scope.
            VimbaFeatureError if 'feat' is not a feature of this camera.
        """
        return filter_selected_features(self.__feats, feat)

    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def get_features_by_type(self, feat_type: FeatureTypeTypes) -> FeaturesTuple:
        """Get all camera features of a specific feature type.

        Valid FeatureTypes are: IntFeature, FloatFeature, StringFeature, BoolFeature,
        EnumFeature, CommandFeature, RawFeature

        Arguments:
            feat_type - FeatureType to find features of that type.

        Returns:
            A feature set of type 'feat_type'.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
        """
        return filter_features_by_type(self.__feats, feat_type)

    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def get_features_by_category(self, category: str) -> FeaturesTuple:
        """Get all camera features of a specific category.

        Arguments:
            category - Category for filtering features.

        Returns:
            A feature set of category 'category'. Can be an empty set if there is
            no camera feature of that category.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
        """
        return filter_features_by_category(self.__feats, category)

    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def get_feature_by_name(self, feat_name: str) -> FeatureTypes:
        """Get a camera feature by its name.

        Arguments:
            feat_name - Name to find a feature.

        Returns:
            Feature with the associated name.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            VimbaFeatureError if no feature is associated with 'feat_name'.
        """
        feat = filter_features_by_name(self.__feats, feat_name)

        if not feat:
            raise VimbaFeatureError('Feature \'{}\' not found.'.format(feat_name))

        return feat

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def get_frame_generator(self, limit: Optional[int] = None, timeout_ms: int = 2000):
        """Construct frame generator, providing synchronous image acquisition.

        The Frame generator acquires a new frame with each execution.

        Arguments:
            limit - The number of images the generator shall acquire. If limit is None,
                    the generator will produce an unlimited amount of images and must be
                    stopped by the user supplied code.
            timeout_ms - Timeout in milliseconds of frame acquisition.

        Returns:
            Frame generator expression

        Raises:
            RuntimeError if called outside "with" - statement scope.
            ValueError if a limit is supplied and negative.
            ValueError if a timeout_ms is negative.
            VimbaTimeout if Frame acquisition timed out.
            VimbaCameraError if Camera is streaming while executing the generator.
        """
        if limit and (limit < 0):
            raise ValueError('Given Limit {} is not >= 0'.format(limit))

        if timeout_ms <= 0:
            raise ValueError('Given Timeout {} is not > 0'.format(timeout_ms))

        return _frame_generator(self, limit, timeout_ms)

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def get_frame(self, timeout_ms: int = 2000) -> Frame:
        """Get single frame from camera. Synchronous frame acquisition.

        Arguments:
            timeout_ms - Timeout in milliseconds of frame acquisition.

        Returns:
            Frame from camera

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            ValueError if a timeout_ms is negative.
            VimbaTimeout if Frame acquisition timed out.
        """
        return next(self.get_frame_generator(1, timeout_ms))

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def start_streaming(self, handler: FrameHandler, buffer_count: int = 5):
        """Enter streaming mode

        Enter streaming mode is also known as asynchronous frame acquisition.
        While active, the camera acquires and buffers frames continuously.
        With each acquired frame, a given FrameHandler is called with a new Frame.

        Arguments:
            handler - Callable that is executed on each acquired frame.
            buffer_count - Number of frames supplied as internal buffer.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            ValueError if buffer is less or equal to zero.
            VimbaCameraError if the camera is already streaming.
            VimbaCameraError if anything went wrong on entering streaming mode.
        """
        if buffer_count <= 0:
            raise ValueError('Given buffer_count {} must be positive'.format(buffer_count))

        if self.is_streaming():
            raise VimbaCameraError('Camera \'{}\' already streaming.'.format(self.get_id()))

        # Setup capturing fsm
        payload_size = self.get_feature_by_name('PayloadSize').get()
        frames = tuple([Frame(payload_size) for _ in range(buffer_count)])
        callback = build_callback_type(None, VmbHandle, POINTER(VmbFrame))(self.__frame_cb_wrapper)

        self.__capture_fsm = _CaptureFsm(_Context(self, frames, handler, callback))

        # Try to enter streaming mode. If this fails perform cleanup and raise error
        exc = self.__capture_fsm.enter_capturing_mode()
        if exc:
            self.__capture_fsm.leave_capturing_mode()
            self.__capture_fsm = None
            raise exc

        else:
            for frame in frames:
                self.__capture_fsm.queue_frame(frame)

    @TraceEnable()
    @RaiseIfOutsideContext()
    def stop_streaming(self):
        """Leave streaming mode.

        Leave asynchronous frame acquisition. If streaming mode was not activated before,
        it just returns silently.

        Raises:
            RuntimeError if called outside "with" - statement scope.
            VimbaCameraError if anything went wrong on leaving streaming mode.
        """
        if not self.is_streaming():
            return

        # Leave Capturing mode. If any error occurs, report it and cleanup
        try:
            exc = self.__capture_fsm.leave_capturing_mode()
            if exc:
                raise exc

        finally:
            self.__capture_fsm = None

    @TraceEnable()
    def is_streaming(self) -> bool:
        """Returns True if the camera is currently in streaming mode. If not, returns False."""
        return self.__capture_fsm is not None and not self._disconnected

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def queue_frame(self, frame: Frame):
        """Reuse acquired frame in streaming mode.

        Add given frame back into the frame queue used in streaming mode. This
        should be the last operation on a registered FrameHandler. If streaming mode is not
        active, it returns silently.

        Arguments:
            frame - The frame to reuse.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if the given frame is not from the internal buffer queue.
            RuntimeError if called outside "with" - statement scope.
            VimbaCameraError if reusing the frame was unsuccessful.
        """
        if self.__capture_fsm is None:
            return

        if frame not in self.__capture_fsm.get_context().frames:
            raise ValueError('Given Frame is not from Queue')

        self.__capture_fsm.queue_frame(frame)

    @TraceEnable()
    @RaiseIfOutsideContext()
    def get_pixel_formats(self) -> FormatTuple:
        """Get supported pixel formats from Camera.

        Returns:
            All pixel formats the camera supports

        Raises:
            RuntimeError if called outside "with" - statement scope.
        """
        result = []
        feat = self.get_feature_by_name('PixelFormat')

        # Build intersection between PixelFormat Enum Values and PixelFormat
        # Note: The Mapping is a bit complicated due to different writing styles within
        #       Feature EnumEntries and PixelFormats
        all_fmts = set([k.upper() for k in PixelFormat.__members__])
        all_enum_fmts = set([str(k).upper() for k in feat.get_available_entries()])
        fmts = all_fmts.intersection(all_enum_fmts)

        for k in PixelFormat.__members__:
            if k.upper() in fmts:
                result.append(PixelFormat[k])

        return tuple(result)

    @TraceEnable()
    @RaiseIfOutsideContext()
    def get_pixel_format(self):
        """Get current pixel format.

        Raises:
            RuntimeError if called outside "with" - statement scope.
        """
        enum_value = str(self.get_feature_by_name('PixelFormat').get()).upper()

        for k in PixelFormat.__members__:
            if k.upper() == enum_value:
                return PixelFormat[k]

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def set_pixel_format(self, fmt: PixelFormat):
        """Set current pixel format.

        Arguments:
            fmt - Default pixel format to set.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            ValueError if the given pixel format is not supported by the cameras.
        """
        if fmt not in self.get_pixel_formats():
            raise ValueError('Camera does not support PixelFormat \'{}\''.format(str(fmt)))

        feat = self.get_feature_by_name('PixelFormat')
        fmt_str = str(fmt).upper()

        for entry in feat.get_available_entries():
            if str(entry).upper() == fmt_str:
                feat.set(entry)

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def save_settings(self, file: str, persist_type: PersistType):
        """Save camera settings to XML - File

        Arguments:
            file - The location for storing the current settings. The given
                   file must be a file ending with ".xml".
            persist_type - Parameter specifying which setting types to store.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            ValueError if argument path is no ".xml"- File.
         """

        if not file.endswith('.xml'):
            raise ValueError('Given file \'{}\' must end with \'.xml\''.format(file))

        settings = VmbFeaturePersistSettings()
        settings.persistType = VmbFeaturePersist(persist_type)

        call_vimba_c('VmbCameraSettingsSave', self.__handle, file.encode('utf-8'), byref(settings),
                     sizeof(settings))

    @TraceEnable()
    @RaiseIfOutsideContext()
    @RuntimeTypeCheckEnable()
    def load_settings(self, file: str, persist_type: PersistType):
        """Load camera settings from XML file

        Arguments:
            file - The location for loading current settings. The given
                   file must be a file ending with ".xml".
            persist_type - Parameter specifying which setting types to load.

        Raises:
            TypeError if parameters do not match their type hint.
            RuntimeError if called outside "with" - statement scope.
            ValueError if argument path is no ".xml" file.
         """

        if not file.endswith('.xml'):
            raise ValueError('Given file \'{}\' must end with \'.xml\''.format(file))

        if not os.path.exists(file):
            raise ValueError('Given file \'{}\' does not exist.'.format(file))

        settings = VmbFeaturePersistSettings()
        settings.persistType = VmbFeaturePersist(persist_type)

        call_vimba_c('VmbCameraSettingsLoad', self.__handle, file.encode('utf-8'), byref(settings),
                     sizeof(settings))

    @TraceEnable()
    @EnterContextOnCall()
    def _open(self):
        try:
            call_vimba_c('VmbCameraOpen', self.__info.cameraIdString, self.__access_mode,
                         byref(self.__handle))

        except VimbaCError as e:
            err = e.get_error_code()

            # In theory InvalidAccess should be thrown on using a non permitted access mode.
            # In reality VmbError.NotImplemented_ is sometimes returned.
            if (err == VmbError.InvalidAccess) or (err == VmbError.NotImplemented_):
                msg = 'Accessed Camera \'{}\' with invalid Mode \'{}\'. Valid modes are: {}'
                msg = msg.format(self.get_id(), str(self.__access_mode),
                                 self.get_permitted_access_modes())
                exc = VimbaCameraError(msg)

            else:
                exc = VimbaCameraError(repr(err))

            raise exc from e

        self.__feats = discover_features(self.__handle)
        attach_feature_accessors(self, self.__feats)

        # Determine current PacketSize (GigE - only) is somewhere between 1500 bytes
        feat = filter_features_by_name(self.__feats, 'GVSPPacketSize')
        if feat:
            try:
                min_ = 1400
                max_ = 1600
                size = feat.get()

                if (min_ < size) and (size < max_):
                    msg = ('Camera {}: GVSPPacketSize not optimized for streaming GigE Vision. '
                           'Enable jumbo packets for improved performance.')
                    Log.get_instance().info(msg.format(self.get_id()))

            except VimbaFeatureError:
                pass

    @TraceEnable()
    @LeaveContextOnCall()
    def _close(self):
        if self.is_streaming():
            self.stop_streaming()

        for feat in self.__feats:
            feat.unregister_all_change_handlers()

        remove_feature_accessors(self, self.__feats)
        self.__feats = ()

        call_vimba_c('VmbCameraClose', self.__handle)
        self.__handle = VmbHandle(0)

    def __frame_cb_wrapper(self, _: VmbHandle, raw_frame_ptr: VmbFrame):   # coverage: skip
        # Skip coverage because it can't be measured. This is called from C-Context.

        # ignore callback if camera has been disconnected
        if self.__capture_fsm is None:
            return

        context = self.__capture_fsm.get_context()

        with context.frames_lock:
            raw_frame = raw_frame_ptr.contents
            frame = None

            for f in context.frames:
                # Access Frame internals to compare if both point to the same buffer
                if raw_frame.buffer == _frame_handle_accessor(f).buffer:
                    frame = f
                    break

            # Execute registered handler
            assert frame is not None

            try:
                context.frames_handler(self, frame)

            except Exception as e:
                msg = 'Caught Exception in handler: '
                msg += 'Type: {}, '.format(type(e))
                msg += 'Value: {}, '.format(e)
                msg += 'raised by: {}'.format(context.frames_handler)
                Log.get_instance().error(msg)
                raise e


def _setup_network_discovery():
    if discover_feature(G_VIMBA_C_HANDLE, 'GeVTLIsPresent').get():
        discover_feature(G_VIMBA_C_HANDLE, 'GeVDiscoveryAllDuration').set(250)
        discover_feature(G_VIMBA_C_HANDLE, 'GeVDiscoveryAllOnce').run()


@TraceEnable()
def discover_cameras(network_discovery: bool) -> CamerasList:
    """Do not call directly. Access Cameras via vimba.Vimba instead."""

    if network_discovery:
        _setup_network_discovery()

    result = []
    cams_count = VmbUint32(0)

    call_vimba_c('VmbCamerasList', None, 0, byref(cams_count), 0)

    if cams_count:
        cams_found = VmbUint32(0)
        cams_infos = (VmbCameraInfo * cams_count.value)()

        call_vimba_c('VmbCamerasList', cams_infos, cams_count, byref(cams_found),
                     sizeof(VmbCameraInfo))

        for info in cams_infos[:cams_found.value]:
            result.append(Camera(info))

    return result


@TraceEnable()
def discover_camera(id_: str) -> Camera:
    """Do not call directly. Access Cameras via vimba.Vimba instead."""

    info = VmbCameraInfo()

    # Try to lookup Camera with given ID. If this function
    try:
        call_vimba_c('VmbCameraInfoQuery', id_.encode('utf-8'), byref(info), sizeof(info))

    except VimbaCError as e:
        raise VimbaCameraError(str(e.get_error_code())) from e

    return Camera(info)


def _cam_handle_accessor(cam: Camera) -> VmbHandle:
    # Supress mypi warning. This access is valid although mypi warns about it.
    # In this case it is okay to unmangle the name because the raw handle should not be
    # exposed.
    return cam._Camera__handle  # type: ignore


def _frame_handle_accessor(frame: Frame) -> VmbFrame:
    return frame._frame


def _build_camera_error(cam: Camera, orig_exc: VimbaCError) -> VimbaCameraError:
    err = orig_exc.get_error_code()

    if err == VmbError.ApiNotStarted:
        msg = 'System not ready. \'{}\' accessed outside of system context. Abort.'
        exc = cast(VimbaCameraError, VimbaSystemError(msg.format(cam.get_id())))

    elif err == VmbError.DeviceNotOpen:
        msg = 'Camera \'{}\' accessed outside of context. Abort.'
        exc = VimbaCameraError(msg.format(cam.get_id()))

    elif err == VmbError.BadHandle:
        msg = 'Invalid Camera. \'{}\' might be disconnected. Abort.'
        exc = VimbaCameraError(msg.format(cam.get_id()))

    elif err == VmbError.InvalidAccess:
        msg = 'Invalid Access Mode on camera \'{}\'. Abort.'
        exc = VimbaCameraError(msg.format(cam.get_id()))

    elif err == VmbError.Timeout:
        msg = 'Frame capturing on Camera \'{}\' timed out.'
        exc = cast(VimbaCameraError, VimbaTimeout(msg.format(cam.get_id())))

    else:
        exc = VimbaCameraError(repr(err))

    return exc
