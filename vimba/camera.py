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

THE SOFTWARE IS PRELIMINARY AND STILL IN TESTING AND VERIFICATION PHASE AND
IS PROVIDED ON AN “AS IS” AND “AS AVAILABLE” BASIS AND IS BELIEVED TO CONTAIN DEFECTS.
A PRIMARY PURPOSE OF THIS EARLY ACCESS IS TO OBTAIN FEEDBACK ON PERFORMANCE AND
THE IDENTIFICATION OF DEFECT SOFTWARE, HARDWARE AND DOCUMENTATION.
"""

import enum
import os
from threading import Lock

from typing import Tuple, List, Callable, cast, Optional, Union, Dict
from .c_binding import call_vimba_c, byref, sizeof, decode_cstr, decode_flags
from .c_binding import VmbCameraInfo, VmbHandle, VmbUint32, G_VIMBA_C_HANDLE, VmbAccessMode, \
                       VimbaCError, VmbError, VmbFrameFlags, VmbFrame, VmbFrameCallback, \
                       VmbFeaturePersist, VmbFeaturePersistSettings
from .feature import discover_features, discover_feature, FeatureTypes, FeaturesTuple
from .shared import filter_features_by_name, filter_features_by_type, filter_affected_features, \
                    filter_selected_features, filter_features_by_category, read_memory_impl, \
                    write_memory_impl, read_registers_impl, write_registers_impl
from .frame import Frame, FrameTuple, FormatTuple, PixelFormat
from .util import Log, TraceEnable, RuntimeTypeCheckEnable
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
    """Enum specifying all available access modes for camera access.

    Enum values:
        None_  - No access
        Full   - Read and write access
        Read   - Read-only access
        Config - Configuration access (GeV)
        Lite   - Read and write access without feature access (only addresses)
    """
    None_ = VmbAccessMode.None_
    Full = VmbAccessMode.Full
    Read = VmbAccessMode.Read
    Config = VmbAccessMode.Config
    Lite = VmbAccessMode.Lite


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
    """Persistence Type used for camera configuration storing and loading.
    Enum values:
        All        - Save all features including lookup tables
        Streamable - Save only Features tagged with Streamable
        NoLUT      - Save all features except lookup tables.
    """
    All = VmbFeaturePersist.All
    Streamable = VmbFeaturePersist.Streamable
    NoLUT = VmbFeaturePersist.NoLUT


class _Context:
    def __init__(self, cam: 'Camera', timeout_ms: int, frames: FrameTuple, handler: FrameHandler,
                 wrapper):
        self.cam: 'Camera' = cam
        self.cam_handle: VmbHandle = _cam_handle_accessor(cam)
        self.timeout_ms: int = timeout_ms
        self.frames: FrameTuple = frames
        self.frames_lock: Lock = Lock()
        self.frames_handler: FrameHandler = handler
        self.frames_wrapper = wrapper


class _State:
    def __init__(self, context: _Context):
        self.context = context


class _StateInit(_State):
    @TraceEnable()
    def forward(self) -> Union[_State, VimbaCameraError]:
        # Init -> Announced: Announce frames
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
        # Announced -> Capturing: Exec capture start
        try:
            call_vimba_c('VmbCaptureStart', self.context.cam_handle)

        except VimbaCError as e:
            return _build_camera_error(self.context.cam, e)

        return _StateCapturing(self.context)

    @TraceEnable()
    def backward(self) -> Union[_State, VimbaCameraError]:
        # Announced -> Init: Revoke all registered frames
        with self.context.frames_lock:
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
        # Capturing -> Queued: Enqueue all frames
        for frame in self.context.frames:
            frame_handle = _frame_handle_accessor(frame)

            try:
                call_vimba_c('VmbCaptureFrameQueue', self.context.cam_handle, byref(frame_handle),
                             self.context.frames_wrapper)

            except VimbaCError as e:
                return _build_camera_error(self.context.cam, e)

        return _StateQueued(self.context)

    @TraceEnable()
    def backward(self) -> Union[_State, VimbaCameraError]:
        # Capturing -> Announced: Revoke all frames
        try:
            call_vimba_c('VmbCaptureQueueFlush', self.context.cam_handle)

        except VimbaCError as e:
            return _build_camera_error(self.context.cam, e)

        return _StateAnnounced(self.context)


class _StateQueued(_State):
    @TraceEnable()
    def forward(self) -> Union[_State, VimbaCameraError]:
        # Queued -> Acquiring: Start acquiring
        try:
            self.context.cam.get_feature_by_name('AcquisitionStart').run()

        except BaseException as e:
            return cast(VimbaCameraError, e)

        return _StateAcquiring(self.context)

    @TraceEnable()
    def backward(self) -> Union[_State, VimbaCameraError]:
        # Queued -> Capturing: End Capturing
        try:
            call_vimba_c('VmbCaptureEnd', self.context.cam_handle)

        except VimbaCError as e:
            return _build_camera_error(self.context.cam, e)

        return _StateCapturing(self.context)


class _StateAcquiring(_State):
    @TraceEnable()
    def backward(self) -> Union[_State, VimbaCameraError]:
        # Acquiring -> Queued: Stop acquiring
        try:
            self.context.cam.get_feature_by_name('AcquisitionStop').run()

        except BaseException as e:
            return cast(VimbaCameraError, e)

        return _StateQueued(self.context)

    @TraceEnable()
    def wait_for_frames(self):
        for frame in self.context.frames:
            frame_handle = _frame_handle_accessor(frame)

            try:
                call_vimba_c('VmbCaptureFrameWait', self.context.cam_handle, byref(frame_handle),
                             self.context.timeout_ms)

            except VimbaCError as e:
                raise _build_camera_error(self.context.cam, e)

    @TraceEnable()
    def queue_frame(self, frame):
        frame_handle = _frame_handle_accessor(frame)

        try:
            call_vimba_c('VmbCaptureFrameQueue', self.context.cam_handle, byref(frame_handle),
                         self.context.frames_wrapper)

        except VimbaCError as e:
            raise _build_camera_error(self.context.cam, e)


class _CaptureFsm:
    def __init__(self, context: _Context):
        self.__context: _Context = context
        self.__state: _State = _StateInit(self.__context)

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

    def wait_for_frames(self):
        self.__state.wait_for_frames()

    def queue_frame(self, frame):
        # Swallow AttributeErrors: Those are caused by callback execution while leaving
        # capturing mode. Those are expected here.
        try:
            self.__state.queue_frame(frame)

        except AttributeError:
            pass


class FrameIter:
    @TraceEnable()
    def __init__(self, cam, limit: Optional[int], timeout_ms: int):
        self.__cam: 'Camera' = cam
        self.__limit: Optional[int] = limit
        self.__timeout_ms: int = timeout_ms
        self.__payload_size: int = self.__cam.get_feature_by_name('PayloadSize').get()
        self.__frame_id = 0

    @TraceEnable()
    def __iter__(self):
        self.__frame_id = 0
        return self

    @TraceEnable()
    def __next__(self):
        if self.__cam.is_streaming():
            raise VimbaCameraError('Operation not supported while streaming.')

        if self.__limit is not None:
            if self.__limit == 0:
                raise StopIteration

            else:
                self.__limit -= 1

        # Allocate Frame, run fsm, wait for frame capturing, rewind fsm
        frame = Frame(self.__payload_size)
        frames = (frame, )

        cap_fsm = _CaptureFsm(_Context(self.__cam, self.__timeout_ms, frames, None, None))

        # Try entering capturing mode. If an error occurs, try to report
        # the initial error and try to revert the damage done.
        exc = cap_fsm.enter_capturing_mode()
        if exc:
            cap_fsm.leave_capturing_mode()
            raise exc

        cap_fsm.wait_for_frames()

        # Leave capturing mode. Perform cleanup
        exc = cap_fsm.leave_capturing_mode()
        if exc:
            raise exc

        # Everything went well. Inject Frame No and return Frame.
        handle = _frame_handle_accessor(frame)
        handle.receiveFlags |= VmbFrameFlags.FrameID
        handle.frameID = self.__frame_id

        self.__frame_id += 1
        return frame


class Camera:
    """This class allows access a Camera detected by the Vimba System.
    Camera is meant be used in conjunction with the "with" - Statement. On entering a context
    all Camera features are detected and can be accessed within the context.
    Basic Camera properties like Name and Model can be access outside of the context.
    """
    @TraceEnable()
    def __init__(self, info: VmbCameraInfo):
        """Do not call directly. Access Cameras via vimba.System instead."""
        self.__handle: VmbHandle = VmbHandle(0)
        self.__info: VmbCameraInfo = info
        self.__access_mode: AccessMode = AccessMode.Full
        self.__feats: FeaturesTuple = ()
        self.__context_cnt: int = 0
        self.__capture_fsm: Optional[_CaptureFsm] = None

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

    @RuntimeTypeCheckEnable()
    def set_access_mode(self, access_mode: AccessMode):
        """Set camera access mode.

        Arguments:
            access_mode - AccessMode used on accessing a Camera. This method
                          must be used before entering the Context with the 'with' statement.

        Raises:
            TypeError if parameters do not match their type hint.
        """
        self.__access_mode = access_mode

    def get_access_mode(self) -> AccessMode:
        """Get current camera access mode"""
        return self.__access_mode

    def get_id(self) -> str:
        """Get Camera Id, e.g. DEV_1AB22C00041B"""
        return decode_cstr(self.__info.cameraIdString)

    def get_name(self) -> str:
        """Get Camera Name, e.g. Allied Vision 1800 U-500m"""
        return decode_cstr(self.__info.cameraName)

    def get_model(self) -> str:
        """Get Camera Model, e.g. 1800 U-500m"""
        return decode_cstr(self.__info.modelName)

    def get_serial(self) -> str:
        """Get Camera Serial, e.g. 000T7"""
        return decode_cstr(self.__info.serialString)

    def get_permitted_access_modes(self) -> Tuple[AccessMode, ...]:
        """Get a set of all access modes, the camera can be accessed with."""
        return decode_flags(AccessMode, self.__info.permittedAccess)

    def get_interface_id(self) -> str:
        """Get ID of the Interface this camera is connected to, e.g. VimbaUSBInterface_0x0"""
        return decode_cstr(self.__info.interfaceIdString)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def read_memory(self, addr: int, max_bytes: int) -> bytes:
        """Read a byte sequence from a given memory address.

        Arguments:
            addr: Starting address to read from.
            max_bytes: Maximum number of bytes to read from addr.

        Returns:
            Read memory contents as bytes.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if addr is negative
            ValueError if max_bytes is negative.
            ValueError if the memory access was invalid.
        """
        return read_memory_impl(self.__handle, addr, max_bytes)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def write_memory(self, addr: int, data: bytes):
        """ Write a byte sequence to a given memory address.

        Arguments:
            addr: Address to write the content of 'data' too.
            data: Byte sequence to write at address 'addr'.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if addr is negative.
        """
        return write_memory_impl(self.__handle, addr, data)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def read_registers(self, addrs: Tuple[int, ...]) -> Dict[int, int]:
        """Read contents of multiple registers.

        Arguments:
            addrs: Sequence of addresses that should be read iteratively.

        Return:
            Dictionary containing a mapping from given address to the read register values.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if any address in addrs is negative.
            ValueError if the register access was invalid.
        """
        return read_registers_impl(self.__handle, addrs)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def write_registers(self, addrs_values: Dict[int, int]):
        """Write data to multiple Registers.

        Arguments:
            addrs_values: Mapping between Register addresses and the data to write.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if any address in addrs_values is negative.
            ValueError if the register access was invalid.
        """
        return write_registers_impl(self.__handle, addrs_values)

    def get_all_features(self) -> FeaturesTuple:
        """Get access to all discovered features of this camera:

        Returns:
            A set of all currently detected features. Returns an empty set then called
            outside of 'with' - statement.
        """
        return self.__feats

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def get_features_affected_by(self, feat: FeatureTypes) -> FeaturesTuple:
        """Get all features affected by a specific camera feature.

        Arguments:
            feat - Feature used find features that are affected by 'feat'.

        Returns:
            A set of features affected by changes on 'feat'. Can be an empty set if 'feat'
            does not affect any features.

        Raises:
            TypeError if parameters do not match their type hint.
            VimbaFeatureError if 'feat' is not a feature of this camera.
        """
        return filter_affected_features(self.__feats, feat)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def get_features_selected_by(self, feat: FeatureTypes) -> FeaturesTuple:
        """Get all features selected by a specific camera feature.

        Arguments:
            feat - Feature used find features that are selected by 'feat'.

        Returns:
            A set of features selected by changes on 'feat'. Can be an empty set if 'feat'
            does not affect any features.

        Raises:
            TypeError if 'feat' is not of any feature type.
            VimbaFeatureError if 'feat' is not a feature of this camera.
        """
        return filter_selected_features(self.__feats, feat)

    @RuntimeTypeCheckEnable()
    def get_features_by_type(self, feat_type: FeatureTypes) -> FeaturesTuple:
        """Get all camera features of a specific feature type.

        Valid FeatureTypes are: IntFeature, FloatFeature, StringFeature, BoolFeature,
        EnumFeature, CommandFeature, RawFeature

        Arguments:
            feat_type - FeatureType used find features of that type.

        Returns:
            A set of features of type 'feat_type'. Can be an empty set if there is
            no camera feature with the given type available.

        Raises:
            TypeError if parameters do not match their type hint.
        """
        return filter_features_by_type(self.__feats, feat_type)

    @RuntimeTypeCheckEnable()
    def get_features_by_category(self, category: str) -> FeaturesTuple:
        """Get all camera features of a specific category.

        Arguments:
            category - Category that should be used for filtering.

        Returns:
            A set of features of category 'category'. Can be an empty set if there is
            no camera feature of that category.

        Raises:
            TypeError if parameters do not match their type hint.
        """
        return filter_features_by_category(self.__feats, category)

    @RuntimeTypeCheckEnable()
    def get_feature_by_name(self, feat_name: str) -> FeatureTypes:
        """Get a camera feature by its name.

        Arguments:
            feat_name - Name used to find a feature.

        Returns:
            Feature with the associated name.

        Raises:
            TypeError if parameters do not match their type hint.
            VimbaFeatureError if no feature is associated with 'feat_name'.
        """
        return filter_features_by_name(self.__feats, feat_name)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def get_frame_iter(self, limit: Optional[int] = None, timeout_ms: int = 2000) -> FrameIter:
        """Construct frame iterator, providing synchronous camera access.

        The Frame iterator acquires a new frame with each iteration.

        Arguments:
            limit - The number of images the iterator should acquire. If limit is None
                    the iterator will produce an unlimited amount of images and must be
                    stopped by the user supplied code.
            timeout_ms - Timeout in milliseconds of frame acquisition.

        Returns:
            frame_iter object

        Raises:
            ValueError if a limit is supplied and negative.
            ValueError if a timeout_ms is negative.
            VimbaCameraError if the camera is outside of its implemented context.
            VimbaTimeout if Frame acquisition timed out.
        """
        if limit and (limit < 0):
            raise ValueError('Given Limit {} is not >= 0'.format(limit))

        if timeout_ms <= 0:
            raise ValueError('Given Timeout {} is not > 0'.format(timeout_ms))

        if not self.__handle:
            msg = 'Camera \'{}\' not ready for frame acquisition. Open camera via \'with\' .'
            raise VimbaCameraError(msg)

        return FrameIter(self, limit, timeout_ms)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def get_frame(self, timeout_ms: int = 2000) -> Frame:
        """Get single frame from camera. Synchronous frame acquisition.

        Arguments:
            timeout_ms - Timeout in milliseconds of frame acquisition.

        Returns:
            Frame from camera

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if a timeout_ms is negative.
            VimbaCameraError if camera is outside of its context.
            VimbaTimeout if Frame acquisition timed out.
        """
        return self.get_frame_iter(1, timeout_ms).__iter__().__next__()

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def start_streaming(self, handler: FrameHandler, buffer_count: int = 5):
        """Enter streaming mode

        Enter streaming mode also known as asynchronous frame acquisition.
        While active the camera acquires and buffers frames continuously.
        With each acquired frame a given FrameHandler is called with new Frame.

        Arguments:
            handler - Callable that is executed on each acquired frame.
            buffer_count - Number of frames supplied as internal buffer.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if buffer is less or equal to zero.
            VimbaCameraError if the camera is already streaming
            VimbaCameraError if the anything gone wrong on entering streaming mode.
        """
        if buffer_count <= 0:
            raise ValueError('Given buffer_count {} must be positive'.format(buffer_count))

        if self.is_streaming():
            msg = 'Camera \'{}\' already streaming.'
            raise VimbaCameraError(msg)

        # Setup capturing fsm
        payload_size = self.get_feature_by_name('PayloadSize').get()
        frames = tuple([Frame(payload_size) for _ in range(buffer_count)])
        wrapper = VmbFrameCallback(self.__frame_cb_wrapper)

        self.__capture_fsm = _CaptureFsm(_Context(self, 0, frames, handler, wrapper))

        # Try to enter streaming mode. If this fails perform cleanup and raise error
        exc = self.__capture_fsm.enter_capturing_mode()
        if exc:
            self.__capture_fsm.leave_capturing_mode()
            self.__capture_fsm = None
            raise exc

    @TraceEnable()
    def stop_streaming(self):
        """Leave streaming mode.

        Leave asynchronous frame acquisition. If streaming mode was not activated before
        it just returns silently.

        Raises:
            VimbaCameraError if the anything gone wrong on leaving streaming mode.
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
        """Returns True if the camera is currently in streaming mode, if not False is returned"""
        return self.__capture_fsm is not None

    @TraceEnable()
    def queue_frame(self, frame: Frame):
        """Reuse acquired Frame in streaming mode.

        Add given frame back into the Frame queue used in streaming mode. This
        should be the last operation on a registered FrameHandler. If streaming mode is not
        active it returns silently.

        Arguments:
            frame - The frame to reuse.

        Raises:
            ValueError if the given frame is not from the internal buffer queue.
            VimbaCameraError if the anything gone wrong on reusing the frame.
        """
        if self.__capture_fsm is None:
            return

        if frame not in self.__capture_fsm.get_context().frames:
            raise ValueError

        self.__capture_fsm.queue_frame(frame)

    @TraceEnable()
    def get_pixel_formats(self) -> FormatTuple:
        """ Get supported pixel formats from Camera"""
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
    def get_pixel_format(self):
        """Get current pixel format."""
        enum_value = str(self.get_feature_by_name('PixelFormat').get()).upper()

        for k in PixelFormat.__members__:
            if k.upper() == enum_value:
                return PixelFormat[k]

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def set_pixel_format(self, fmt: PixelFormat):
        """ Set current pixel format.

        Arguments:
            fmt - Default pixel format to set.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError is given format in not in cameras supported PixelFormats.
        """
        if fmt not in self.get_pixel_formats():
            raise ValueError('Camera does not support PixelFormat \'{}\''.format(str(fmt)))

        feat = self.get_feature_by_name('PixelFormat')
        fmt_str = str(fmt).upper()

        for entry in feat.get_available_entries():
            if str(entry).upper() == fmt_str:
                feat.set(entry)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def save_settings(self, file: str, persist_type: PersistType):
        """Save camera settings to XML - File

        Arguments:
            file - The location used to store the current settings. The given
                   file must be a file ending with ".xml".
            persist_type - Parameter specifying which setting types to store.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if argument path is no ".xml"- File.
         """

        if not file.endswith('.xml'):
            raise ValueError('Given file \'{}\' must end with \'.xml\''.format(file))

        settings = VmbFeaturePersistSettings()
        settings.persistType = VmbFeaturePersist(persist_type)

        call_vimba_c('VmbCameraSettingsSave', self.__handle, file.encode('utf-8'), byref(settings),
                     sizeof(settings))

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def load_settings(self, file: str, persist_type: PersistType):
        """Load camera settings from XML - File

        Arguments:
            file - The location used to load current settings. The given
                   file must be a file ending with ".xml".
            persist_type - Parameter specifying which setting types to load.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if argument path is no ".xml"- File.
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
    def _open(self):
        exc = None

        try:
            call_vimba_c('VmbCameraOpen', self.__info.cameraIdString, self.__access_mode,
                         byref(self.__handle))

        except VimbaCError as e:
            exc = cast(VimbaCameraError, e)
            err = e.get_error_code()

            # In theory InvalidAccess should be thrown on using a non permitted access mode.
            # In reality VmbError.NotImplemented_ is sometimes returned.
            if (err == VmbError.InvalidAccess) or (err == VmbError.NotImplemented_):
                msg = 'Accessed Camera \'{}\' with invalid Mode \'{}\'. Valid modes are: {}'
                msg = msg.format(self.get_id(), str(self.__access_mode),
                                 self.get_permitted_access_modes())

                exc = VimbaCameraError(msg)

        if exc:
            raise exc

        self.__feats = discover_features(self.__handle)

        # Determine current PacketSize (GigE - only) is somewhere between 1500 bytes
        # add a log entry that
        try:
            min_ = 1400
            max_ = 1600
            size = filter_features_by_name(self.__feats, 'GVSPPacketSize').get()

            if (min_ < size) and (size < max_):
                msg = ('Camera {}: GVSPPacketSize not optimized for streaming GigE Vision. '
                       'Enable jumbo packets for improved performance.')
                Log.get_instance().info(msg.format(self.get_id()))

        except VimbaFeatureError:
            pass

    @TraceEnable()
    def _close(self):
        if self.is_streaming:
            self.stop_streaming()

        for feat in self.__feats:
            feat.unregister_all_change_handlers()

        call_vimba_c('VmbCameraClose', self.__handle)

        self.__feats = ()
        self.__handle = VmbHandle(0)

    def __frame_cb_wrapper(self, _: VmbHandle, raw_frame_ptr: VmbFrame):   # coverage: skip
        # Skip coverage because it can't be measured. This is called from C-Context.
        assert self.__capture_fsm is not None

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

    call_vimba_c('VmbCameraInfoQuery', id_.encode('utf-8'), byref(info), sizeof(info))

    return Camera(info)


def _cam_handle_accessor(cam: Camera) -> VmbHandle:
    # Supress mypi warning. This access is valid although mypi warns about it.
    # In this case it is okay to unmangle the name because the raw handle should not be
    # exposed.
    return cam._Camera__handle  # type: ignore


def _frame_handle_accessor(frame: Frame) -> VmbFrame:
    return frame._frame


def _build_camera_error(cam: Camera, orig_exc: VimbaCError) -> VimbaCameraError:
    exc = cast(VimbaCameraError, orig_exc)
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

    return exc
