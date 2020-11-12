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

import threading
from typing import List, Dict, Tuple
from .c_binding import call_vimba_c, VIMBA_C_VERSION, VIMBA_IMAGE_TRANSFORM_VERSION, \
                       G_VIMBA_C_HANDLE
from .feature import discover_features, FeatureTypes, FeaturesTuple, FeatureTypeTypes, EnumFeature
from .shared import filter_features_by_name, filter_features_by_type, filter_affected_features, \
                    filter_selected_features, filter_features_by_category, \
                    attach_feature_accessors, remove_feature_accessors, read_memory, \
                    write_memory, read_registers, write_registers
from .interface import Interface, InterfaceChangeHandler, InterfaceEvent, InterfacesTuple, \
                       InterfacesList, discover_interfaces, discover_interface
from .camera import Camera, CamerasList, CameraChangeHandler, CameraEvent, CamerasTuple, \
                    discover_cameras, discover_camera
from .util import Log, LogConfig, TraceEnable, RuntimeTypeCheckEnable, EnterContextOnCall, \
                  LeaveContextOnCall, RaiseIfInsideContext, RaiseIfOutsideContext
from .error import VimbaCameraError, VimbaInterfaceError, VimbaFeatureError
from . import __version__ as VIMBA_PYTHON_VERSION


__all__ = [
    'Vimba',
]


class Vimba:
    class __Impl:
        """This class allows access to the entire Vimba System.
        Vimba is meant be used in conjunction with the "with" - Statement, upon
        entering the context, all system features, connected cameras and interfaces are detected
        and can be used.
        """

        @TraceEnable()
        @LeaveContextOnCall()
        def __init__(self):
            """Do not call directly. Use Vimba.get_instance() instead."""
            self.__feats: FeaturesTuple = ()

            self.__inters: InterfacesList = ()
            self.__inters_lock: threading.Lock = threading.Lock()
            self.__inters_handlers: List[InterfaceChangeHandler] = []
            self.__inters_handlers_lock: threading.Lock = threading.Lock()

            self.__cams: CamerasList = ()
            self.__cams_lock: threading.Lock = threading.Lock()
            self.__cams_handlers: List[CameraChangeHandler] = []
            self.__cams_handlers_lock: threading.Lock = threading.Lock()

            self.__nw_discover: bool = True
            self.__context_cnt: int = 0

        @TraceEnable()
        def __enter__(self):
            if not self.__context_cnt:
                self._startup()

            self.__context_cnt += 1
            return self

        @TraceEnable()
        def __exit__(self, exc_type, exc_value, exc_traceback):
            self.__context_cnt -= 1

            if not self.__context_cnt:
                self._shutdown()

        def get_version(self) -> str:
            """ Returns version string of VimbaPython and underlaying dependencies."""
            msg = 'VimbaPython: {} (using VimbaC: {}, VimbaImageTransform: {})'
            return msg.format(VIMBA_PYTHON_VERSION, VIMBA_C_VERSION, VIMBA_IMAGE_TRANSFORM_VERSION)

        @RaiseIfInsideContext()
        @RuntimeTypeCheckEnable()
        def set_network_discovery(self, enable: bool):
            """Enable/Disable network camera discovery.

            Arguments:
                enable - If 'True' VimbaPython tries to detect cameras connected via Ethernet
                         on entering the 'with' statement. If set to 'False', no network
                         discover occurs.

            Raises:
                TypeError if parameters do not match their type hint.
                RuntimeError if called inside with-statement.
            """
            self.__nw_discover = enable

        @RuntimeTypeCheckEnable()
        def enable_log(self, config: LogConfig):
            """Enable VimbaPython's logging mechanism.

            Arguments:
                config - Configuration for the logging mechanism.

            Raises:
                TypeError if parameters do not match their type hint.
            """
            Log.get_instance().enable(config)

        def disable_log(self):
            """Disable VimbaPython's logging mechanism."""
            Log.get_instance().disable()

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
                RuntimeError then called outside of "with" - statement.
                ValueError if addr is negative
                ValueError if max_bytes is negative.
                ValueError if the memory access was invalid.
            """
            # Note: Coverage is skipped. Function is untestable in a generic way.
            return read_memory(G_VIMBA_C_HANDLE, addr, max_bytes)

        @TraceEnable()
        @RaiseIfOutsideContext()
        @RuntimeTypeCheckEnable()
        def write_memory(self, addr: int, data: bytes):  # coverage: skip
            """ Write a byte sequence to a given memory address.

            Arguments:
                addr: Address to write the content of 'data' too.
                data: Byte sequence to write at address 'addr'.

            Raises:
                TypeError if parameters do not match their type hint.
                RuntimeError then called outside of "with" - statement.
                ValueError if addr is negative.
            """
            # Note: Coverage is skipped. Function is untestable in a generic way.
            return write_memory(G_VIMBA_C_HANDLE, addr, data)

        @TraceEnable()
        @RaiseIfOutsideContext()
        @RuntimeTypeCheckEnable()
        def read_registers(self, addrs: Tuple[int, ...]) -> Dict[int, int]:  # coverage: skip
            """Read contents of multiple registers.

            Arguments:
                addrs: Sequence of addresses that should be read iteratively.

            Return:
                Dictionary containing a mapping from given address to the read register values.

            Raises:
                TypeError if parameters do not match their type hint.
                RuntimeError then called outside of "with" - statement.
                ValueError if any address in addrs_values is negative.
                ValueError if the register access was invalid.
            """
            # Note: Coverage is skipped. Function is untestable in a generic way.
            return read_registers(G_VIMBA_C_HANDLE, addrs)

        @TraceEnable()
        @RaiseIfOutsideContext()
        @RuntimeTypeCheckEnable()
        def write_registers(self, addrs_values: Dict[int, int]):  # coverage: skip
            """Write data to multiple Registers.

            Arguments:
                addrs_values: Mapping between Register addresses and the data to write.

            Raises:
                TypeError if parameters do not match their type hint.
                RuntimeError then called outside of "with" - statement.
                ValueError if any address in addrs is negative.
                ValueError if the register access was invalid.
            """
            # Note: Coverage is skipped. Function is untestable in a generic way.
            return write_registers(G_VIMBA_C_HANDLE, addrs_values)

        @RaiseIfOutsideContext()
        def get_all_interfaces(self) -> InterfacesTuple:
            """Get access to all discovered Interfaces:

            Returns:
                A set of all currently detected Interfaces.

            Raises:
                RuntimeError then called outside of "with" - statement.
            """
            with self.__inters_lock:
                return tuple(self.__inters)

        @RaiseIfOutsideContext()
        @RuntimeTypeCheckEnable()
        def get_interface_by_id(self, id_: str) -> Interface:
            """Lookup Interface with given ID.

            Arguments:
                id_ - Interface Id to search for.

            Returns:
                Interface associated with given Id.

            Raises:
                TypeError if parameters do not match their type hint.
                RuntimeError then called outside of "with" - statement.
                VimbaInterfaceError if interface with id_ can't be found.
            """
            with self.__inters_lock:
                inter = [inter for inter in self.__inters if id_ == inter.get_id()]

            if not inter:
                raise VimbaInterfaceError('Interface with ID \'{}\' not found.'.format(id_))

            return inter.pop()

        @RaiseIfOutsideContext()
        def get_all_cameras(self) -> CamerasTuple:
            """Get access to all discovered Cameras.

            Returns:
                A set of all currently detected Cameras.

            Raises:
                RuntimeError then called outside of "with" - statement.
            """
            with self.__cams_lock:
                return tuple(self.__cams)

        @RaiseIfOutsideContext()
        @RuntimeTypeCheckEnable()
        def get_camera_by_id(self, id_: str) -> Camera:
            """Lookup Camera with given ID.

            Arguments:
                id_ - Camera Id to search for. For GigE - Cameras, the IP and MAC-Address
                      can be used to Camera lookup

            Returns:
                Camera associated with given Id.

            Raises:
                TypeError if parameters do not match their type hint.
                RuntimeError then called outside of "with" - statement.
                VimbaCameraError if camera with id_ can't be found.
            """
            with self.__cams_lock:
                # Search for given Camera Id in all currently detected cameras.
                for cam in self.__cams:
                    if id_ == cam.get_id():
                        return cam

                # If a search by ID fails, the given id_ is almost certain an IP or MAC - Address.
                # Try to query this Camera.
                try:
                    cam_info = discover_camera(id_)

                    # Since cam_info is newly constructed, search in existing cameras for a Camera
                    for cam in self.__cams:
                        if cam_info.get_id() == cam.get_id():
                            return cam

                except VimbaCameraError:
                    pass

            raise VimbaCameraError('No Camera with Id \'{}\' available.'.format(id_))

        @RaiseIfOutsideContext()
        def get_all_features(self) -> FeaturesTuple:
            """Get access to all discovered system features:

            Returns:
                A set of all currently detected Features.

            Raises:
                RuntimeError then called outside of "with" - statement.
            """
            return self.__feats

        @TraceEnable()
        @RaiseIfOutsideContext()
        @RuntimeTypeCheckEnable()
        def get_features_affected_by(self, feat: FeatureTypes) -> FeaturesTuple:
            """Get all system features affected by a specific system feature.

            Arguments:
                feat - Feature used find features that are affected by feat.

            Returns:
                A set of features affected by changes on 'feat'.

            Raises:
                TypeError if parameters do not match their type hint.
                RuntimeError then called outside of "with" - statement.
                VimbaFeatureError if 'feat' is not a system feature.
            """
            return filter_affected_features(self.__feats, feat)

        @TraceEnable()
        @RaiseIfOutsideContext()
        @RuntimeTypeCheckEnable()
        def get_features_selected_by(self, feat: FeatureTypes) -> FeaturesTuple:
            """Get all system features selected by a specific system feature.

            Arguments:
                feat - Feature used find features that are selected by feat.

            Returns:
                A set of features selected by 'feat'.

            Raises:
                TypeError if parameters do not match their type hint.
                RuntimeError then called outside of "with" - statement.
                VimbaFeatureError if 'feat' is not a system feature.
            """
            return filter_selected_features(self.__feats, feat)

        @RaiseIfOutsideContext()
        @RuntimeTypeCheckEnable()
        def get_features_by_type(self, feat_type: FeatureTypeTypes) -> FeaturesTuple:
            """Get all system features of a specific feature type.

            Valid FeatureTypes are: IntFeature, FloatFeature, StringFeature, BoolFeature,
            EnumFeature, CommandFeature, RawFeature

            Arguments:
                feat_type - FeatureType used find features of that type.

            Returns:
                A set of features of type 'feat_type'.

            Raises:
                TypeError if parameters do not match their type hint.
                RuntimeError then called outside of "with" - statement.
            """
            return filter_features_by_type(self.__feats, feat_type)

        @RaiseIfOutsideContext()
        @RuntimeTypeCheckEnable()
        def get_features_by_category(self, category: str) -> FeaturesTuple:
            """Get all system features of a specific category.

            Arguments:
                category - Category that should be used for filtering.

            Returns:
                A set of features of category 'category'.

            Returns:
                TypeError if parameters do not match their type hint.
                RuntimeError then called outside of "with" - statement.
            """
            return filter_features_by_category(self.__feats, category)

        @RaiseIfOutsideContext()
        @RuntimeTypeCheckEnable()
        def get_feature_by_name(self, feat_name: str) -> FeatureTypes:
            """Get a system feature by its name.

            Arguments:
                feat_name - Name used to find a feature.

            Returns:
                Feature with the associated name.

            Raises:
                TypeError if parameters do not match their type hint.
                RuntimeError then called outside of "with" - statement.
                VimbaFeatureError if no feature is associated with 'feat_name'.
            """
            feat = filter_features_by_name(self.__feats, feat_name)

            if not feat:
                raise VimbaFeatureError('Feature \'{}\' not found.'.format(feat_name))

            return feat

        @RuntimeTypeCheckEnable()
        def register_camera_change_handler(self, handler: CameraChangeHandler):
            """Add Callable what is executed on camera connect/disconnect

            Arguments:
                handler - The change handler that shall be added.

            Raises:
                TypeError if parameters do not match their type hint.
            """
            with self.__cams_handlers_lock:
                if handler not in self.__cams_handlers:
                    self.__cams_handlers.append(handler)

        def unregister_all_camera_change_handlers(self):
            """Remove all currently registered camera change handlers"""
            with self.__cams_handlers_lock:
                if self.__cams_handlers:
                    self.__cams_handlers.clear()

        @RuntimeTypeCheckEnable()
        def unregister_camera_change_handler(self, handler: CameraChangeHandler):
            """Remove previously registered camera change handler

            Arguments:
                handler - The change handler that shall be removed.

            Raises:
                TypeError if parameters do not match their type hint.
            """
            with self.__cams_handlers_lock:
                if handler in self.__cams_handlers:
                    self.__cams_handlers.remove(handler)

        @RuntimeTypeCheckEnable()
        def register_interface_change_handler(self, handler: InterfaceChangeHandler):
            """Add Callable what is executed on interface connect/disconnect

            Arguments:
                handler - The change handler that shall be added.

            Raises:
                TypeError if parameters do not match their type hint.
            """
            with self.__inters_handlers_lock:
                if handler not in self.__inters_handlers:
                    self.__inters_handlers.append(handler)

        def unregister_all_interface_change_handlers(self):
            """Remove all currently registered interface change handlers"""
            with self.__inters_handlers_lock:
                if self.__inters_handlers:
                    self.__inters_handlers.clear()

        @RuntimeTypeCheckEnable()
        def unregister_interface_change_handler(self, handler: InterfaceChangeHandler):
            """Remove previously registered interface change handler

            Arguments:
                handler - The change handler that shall be removed.

            Raises:
                TypeError if parameters do not match their type hint.
            """
            with self.__inters_handlers_lock:
                if handler in self.__inters_handlers:
                    self.__inters_handlers.remove(handler)

        @TraceEnable()
        @EnterContextOnCall()
        def _startup(self):
            Log.get_instance().info('Starting {}'.format(self.get_version()))

            call_vimba_c('VmbStartup')

            self.__inters = discover_interfaces()
            self.__cams = discover_cameras(self.__nw_discover)
            self.__feats = discover_features(G_VIMBA_C_HANDLE)
            attach_feature_accessors(self, self.__feats)

            feat = self.get_feature_by_name('DiscoveryInterfaceEvent')
            feat.register_change_handler(self.__inter_cb_wrapper)

            feat = self.get_feature_by_name('DiscoveryCameraEvent')
            feat.register_change_handler(self.__cam_cb_wrapper)

        @TraceEnable()
        @LeaveContextOnCall()
        def _shutdown(self):
            self.unregister_all_camera_change_handlers()
            self.unregister_all_interface_change_handlers()

            for feat in self.__feats:
                feat.unregister_all_change_handlers()

            remove_feature_accessors(self, self.__feats)
            self.__feats = ()
            self.__cams_handlers = []
            self.__cams = ()
            self.__inters_handlers = []
            self.__inters = ()

            call_vimba_c('VmbShutdown')

        def __cam_cb_wrapper(self, cam_event: EnumFeature):   # coverage: skip
            # Skip coverage because it can't be measured. This is called from C-Context
            event = CameraEvent(int(cam_event.get()))
            cam = None
            cam_id = self.get_feature_by_name('DiscoveryCameraIdent').get()
            log = Log.get_instance()

            # New camera found: Add it to camera list
            if event == CameraEvent.Detected:
                cam = discover_camera(cam_id)

                with self.__cams_lock:
                    self.__cams.append(cam)

                log.info('Added camera \"{}\" to active cameras'.format(cam_id))

            # Existing camera lost. Remove it from active cameras
            elif event == CameraEvent.Missing:
                with self.__cams_lock:
                    cam = [c for c in self.__cams if cam_id == c.get_id()].pop()
                    cam._disconnected = True
                    self.__cams.remove(cam)

                log.info('Removed camera \"{}\" from active cameras'.format(cam_id))

            else:
                cam = self.get_camera_by_id(cam_id)

            with self.__cams_handlers_lock:
                for handler in self.__cams_handlers:
                    try:
                        handler(cam, event)

                    except Exception as e:
                        msg = 'Caught Exception in handler: '
                        msg += 'Type: {}, '.format(type(e))
                        msg += 'Value: {}, '.format(e)
                        msg += 'raised by: {}'.format(handler)
                        Log.get_instance().error(msg)
                        raise e

        def __inter_cb_wrapper(self, inter_event: EnumFeature):   # coverage: skip
            # Skip coverage because it can't be measured. This is called from C-Context
            event = InterfaceEvent(int(inter_event.get()))
            inter = None
            inter_id = self.get_feature_by_name('DiscoveryInterfaceIdent').get()
            log = Log.get_instance()

            # New interface found: Add it to interface list
            if event == InterfaceEvent.Detected:
                inter = discover_interface(inter_id)

                with self.__inters_lock:
                    self.__inters.append(inter)

                log.info('Added interface \"{}\" to active interfaces'.format(inter_id))

            # Existing interface lost. Remove it from active interfaces
            elif event == InterfaceEvent.Missing:
                with self.__inters_lock:
                    inter = [i for i in self.__inters if inter_id == i.get_id()].pop()
                    self.__inters.remove(inter)

                log.info('Removed interface \"{}\" from active interfaces'.format(inter_id))

            else:
                inter = self.get_interface_by_id(inter_id)

            with self.__inters_handlers_lock:
                for handler in self.__inters_handlers:
                    try:
                        handler(inter, event)

                    except Exception as e:
                        msg = 'Caught Exception in handler: '
                        msg += 'Type: {}, '.format(type(e))
                        msg += 'Value: {}, '.format(e)
                        msg += 'raised by: {}'.format(handler)
                        Log.get_instance().error(msg)
                        raise e

    __instance = __Impl()

    @staticmethod
    @TraceEnable()
    def get_instance() -> '__Impl':
        """Get VimbaSystem Singleton."""
        return Vimba.__instance
