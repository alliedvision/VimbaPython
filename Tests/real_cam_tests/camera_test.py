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

import unittest
import threading
import os

from vimba import *
from vimba.frame import *


def dummy_frame_handler(cam: Camera, frame: Frame):
    pass


class CamCameraTest(unittest.TestCase):
    def setUp(self):
        self.vimba = Vimba.get_instance()
        self.vimba._startup()

        try:
            self.cam = self.vimba.get_camera_by_id(self.get_test_camera_id())

        except VimbaCameraError as e:
            self.vimba._shutdown()
            raise Exception('Failed to lookup Camera.') from e

        self.cam.set_access_mode(AccessMode.Full)

    def tearDown(self):
        self.cam.set_access_mode(AccessMode.Full)
        self.vimba._shutdown()

    def test_camera_context_manager_access_mode(self):
        # Expectation: Entering Context must not throw in cases where the current access mode is
        # within get_permitted_access_modes()

        permitted_modes = self.cam.get_permitted_access_modes()

        for mode in permitted_modes:
            self.cam.set_access_mode(mode)

            try:
                with self.cam:
                    pass

            except BaseException:
                self.fail()

    def test_camera_context_manager_feature_discovery(self):
        # Expectation: Outside of context, all features must be cleared,
        # inside of context all features must be detected.
        with self.cam:
            self.assertNotEqual(self.cam.get_all_features(), ())

    def test_camera_access_mode(self):
        # Expectation: set/get access mode
        self.cam.set_access_mode(AccessMode.None_)
        self.assertEqual(self.cam.get_access_mode(), AccessMode.None_)
        self.cam.set_access_mode(AccessMode.Full)
        self.assertEqual(self.cam.get_access_mode(), AccessMode.Full)
        self.cam.set_access_mode(AccessMode.Read)
        self.assertEqual(self.cam.get_access_mode(), AccessMode.Read)

    def test_camera_get_id(self):
        # Expectation: get decoded camera id
        self.assertTrue(self.cam.get_id())

    def test_camera_get_name(self):
        # Expectation: get decoded camera name
        self.assertTrue(self.cam.get_name())

    def test_camera_get_model(self):
        # Expectation: get decoded camera model
        self.assertTrue(self.cam.get_model())

    def test_camera_get_serial(self):
        # Expectation: get decoded camera serial
        self.assertTrue(self.cam.get_serial())

    def test_camera_get_permitted_access_modes(self):
        # Expectation: get currently permitted access modes
        expected = (AccessMode.None_, AccessMode.Full, AccessMode.Read, AccessMode.Config)

        for mode in self.cam.get_permitted_access_modes():
            self.assertIn(mode, expected)

    def test_camera_get_interface_id(self):
        # Expectation: get interface Id this camera is connected to
        self.assertTrue(self.cam.get_interface_id())

    def test_camera_get_features_affected(self):
        # Expectation: Features that affect other features shall return a set of affected feature
        # Features that don't affect other features shall return (). If a Feature is supplied that
        # is not associated with that camera, a TypeError must be raised.

        with self.cam:
            try:
                affect = self.cam.get_feature_by_name('Height')

            except VimbaFeatureError as e:
                raise unittest.SkipTest('Failed to lookup Feature Height') from e

            try:
                not_affect = self.cam.get_feature_by_name('AcquisitionFrameCount')

            except VimbaFeatureError as e:
                raise unittest.SkipTest('Failed to lookup Feature AcquisitionFrameCount') from e

            self.assertEqual(self.cam.get_features_affected_by(not_affect), ())

            try:
                payload_size = self.cam.get_feature_by_name('PayloadSize')

            except VimbaFeatureError as e:
                raise unittest.SkipTest('Failed to lookup Feature PayloadSize') from e

            self.assertIn(payload_size, self.cam.get_features_affected_by(affect))

    def test_camera_frame_generator_limit_set(self):
        # Expectation: The Frame generator fetches the given number of images.
        with self.cam:
            self.assertEqual(len([i for i in self.cam.get_frame_generator(0)]), 0)
            self.assertEqual(len([i for i in self.cam.get_frame_generator(1)]), 1)
            self.assertEqual(len([i for i in self.cam.get_frame_generator(7)]), 7)
            self.assertEqual(len([i for i in self.cam.get_frame_generator(11)]), 11)

    def test_camera_frame_generator_error(self):
        # Expectation: The Frame generator raises a ValueError on a
        # negative limit and the camera raises an ValueError
        # if the camera is not opened.

        # generator execution must throw if streaming is enabled
        with self.cam:
            # Check limits
            self.assertRaises(ValueError, self.cam.get_frame_generator, -1)
            self.assertRaises(ValueError, self.cam.get_frame_generator, 1, 0)
            self.assertRaises(ValueError, self.cam.get_frame_generator, 1, -1)

            self.cam.start_streaming(dummy_frame_handler, 5)

            self.assertRaises(VimbaCameraError, self.cam.get_frame)
            self.assertRaises(VimbaCameraError, next, self.cam.get_frame_generator(1))

            # Stop Streaming: Everything should be fine.
            self.cam.stop_streaming()
            self.assertNoRaise(self.cam.get_frame)
            self.assertNoRaise(next, self.cam.get_frame_generator(1))

    def test_camera_get_frame(self):
        # Expectation: Gets single Frame without any exception. Image data must be set.
        # If a zero or negative timeouts must lead to a ValueError.
        with self.cam:
            self.assertRaises(ValueError, self.cam.get_frame, 0)
            self.assertRaises(ValueError, self.cam.get_frame, -1)

            self.assertNoRaise(self.cam.get_frame)
            self.assertEqual(type(self.cam.get_frame()), Frame)

    def test_camera_capture_error_outside_vimba_scope(self):
        # Expectation: Camera access outside of Vimba scope must lead to a RuntimeError
        gener = None

        with self.cam:
            gener = self.cam.get_frame_generator(1)

        # Shutdown API
        self.vimba._shutdown()

        # Access invalid Iterator
        self.assertRaises(RuntimeError, next, gener)

    def test_camera_capture_error_outside_camera_scope(self):
        # Expectation: Camera access outside of Camera scope must lead to a RuntimeError
        gener = None

        with self.cam:
            gener = self.cam.get_frame_generator(1)

        self.assertRaises(RuntimeError, next, gener)

    def test_camera_capture_timeout(self):
        # Expectation: Camera access outside of Camera scope must lead to a VimbaTimeout
        with self.cam:
            self.assertRaises(VimbaTimeout, self.cam.get_frame, 1)

    def test_camera_is_streaming(self):
        # Expectation: After start_streaming() is_streaming() must return true. After stop it must
        # return false. If the camera context is left without stop_streaming(), leaving
        # the context must stop streaming.

        # Normal Operation
        self.assertEqual(self.cam.is_streaming(), False)
        with self.cam:
            self.cam.start_streaming(dummy_frame_handler)
            self.assertEqual(self.cam.is_streaming(), True)

            self.cam.stop_streaming()
            self.assertEqual(self.cam.is_streaming(), False)

        # Missing the stream stop. Close must stop streaming
        with self.cam:
            self.cam.start_streaming(dummy_frame_handler, 5)
            self.assertEqual(self.cam.is_streaming(), True)

        self.assertEqual(self.cam.is_streaming(), False)

    def test_camera_streaming_error_frame_count(self):
        # Expectation: A negative or zero frame_count must lead to an value error
        with self.cam:
            self.assertRaises(ValueError, self.cam.start_streaming, dummy_frame_handler, 0)
            self.assertRaises(ValueError, self.cam.start_streaming, dummy_frame_handler, -1)

    def test_camera_streaming(self):
        # Expectation: A given frame_handler must be executed for each buffered frame.

        class FrameHandler:
            def __init__(self, frame_count):
                self.cnt = 0
                self.frame_count = frame_count
                self.event = threading.Event()

            def __call__(self, cam: Camera, frame: Frame):
                self.cnt += 1

                if self.cnt == self.frame_count:
                    self.event.set()

        timeout = 5.0
        frame_count = 10
        handler = FrameHandler(frame_count)

        with self.cam:
            try:
                self.cam.start_streaming(handler, frame_count)

                # Wait until the FrameHandler has been executed for each queued frame
                self.assertTrue(handler.event.wait(timeout))

            finally:
                self.cam.stop_streaming()

    def test_camera_streaming_queue(self):
        # Expectation: A given frame must be reused if it is enqueued again.

        class FrameHandler:
            def __init__(self, frame_count):
                self.cnt = 0
                self.frame_count = frame_count
                self.event = threading.Event()

            def __call__(self, cam: Camera, frame: Frame):
                self.cnt += 1

                if self.cnt == self.frame_count:
                    self.event.set()

                cam.queue_frame(frame)

        timeout = 5.0
        frame_count = 5
        frame_reuse = 2
        handler = FrameHandler(frame_count * frame_reuse)

        with self.cam:
            try:
                self.cam.start_streaming(handler, frame_count)

                # Wait until the FrameHandler has been executed for each queued frame
                self.assertTrue(handler.event.wait(timeout))

            finally:
                self.cam.stop_streaming()

    def test_camera_runtime_type_check(self):
        def valid_handler(cam, frame):
            pass

        def invalid_handler_1(cam):
            pass

        def invalid_handler_2(cam, frame, extra):
            pass

        self.assertRaises(TypeError, self.cam.set_access_mode, -1)

        with self.cam:
            # Expectation: raise TypeError on passing invalid parameters
            self.assertRaises(TypeError, self.cam.get_frame, 'hi')
            self.assertRaises(TypeError, self.cam.get_features_affected_by, 'No Feature')
            self.assertRaises(TypeError, self.cam.get_features_selected_by, 'No Feature')
            self.assertRaises(TypeError, self.cam.get_features_by_type, 0.0)
            self.assertRaises(TypeError, self.cam.get_feature_by_name, 0)
            self.assertRaises(TypeError, self.cam.get_frame_generator, '3')
            self.assertRaises(TypeError, self.cam.get_frame_generator, 0, 'foo')
            self.assertRaises(TypeError, self.cam.start_streaming, valid_handler, 'no int')
            self.assertRaises(TypeError, self.cam.start_streaming, invalid_handler_1)
            self.assertRaises(TypeError, self.cam.start_streaming, invalid_handler_2)
            self.assertRaises(TypeError, self.cam.save_settings, 0, PersistType.All)
            self.assertRaises(TypeError, self.cam.save_settings, 'foo.xml', 'false type')

    def test_camera_save_load_settings(self):
        # Expectation: After settings export a settings change must be reverted by loading a
        # Previously saved configuration.

        file_name = 'test_save_load_settings.xml'

        with self.cam:
            feat_height = self.cam.get_feature_by_name('Height')
            old_val = feat_height.get()

            self.cam.save_settings(file_name, PersistType.All)

            min_, max_ = feat_height.get_range()
            inc = feat_height.get_increment()

            feat_height.set(max_ - min_ - inc)

            self.cam.load_settings(file_name, PersistType.All)
            os.remove(file_name)

            self.assertEqual(old_val, feat_height.get())

    def test_camera_save_settings_verify_path(self):
        # Expectation: Valid files end with .xml and can be either a absolute path or relative
        # path to the given File. Everything else is a ValueError.

        valid_paths = (
            'valid1.xml',
            os.path.join('.', 'valid2.xml'),
            os.path.join('Tests', 'valid3.xml'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'valid4.xml'),
        )

        with self.cam:
            self.assertRaises(ValueError, self.cam.save_settings, 'inval.xm', PersistType.All)

            for path in valid_paths:
                self.assertNoRaise(self.cam.save_settings, path, PersistType.All)
                os.remove(path)

    def test_camera_load_settings_verify_path(self):
        # Expectation: Valid files end with .xml and must exist before before any execution.
        valid_paths = (
            'valid1.xml',
            os.path.join('.', 'valid2.xml'),
            os.path.join('Tests', 'valid3.xml'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'valid4.xml'),
        )

        with self.cam:
            self.assertRaises(ValueError, self.cam.load_settings, 'inval.xm', PersistType.All)

            for path in valid_paths:
                self.assertRaises(ValueError, self.cam.load_settings, path, PersistType.All)

            for path in valid_paths:
                self.cam.save_settings(path, PersistType.All)

                self.assertNoRaise(self.cam.load_settings, path, PersistType.All)
                os.remove(path)

    def test_camera_context_manager_reentrancy(self):
        # Expectation: Camera Context Manager must be reentrant. Multiple calls to _open
        # must be prevented (would cause VimbaC - Error)
        with self.cam:
            with self.cam:
                with self.cam:
                    pass

    def test_camera_api_context_sensitity_outside_context(self):
        # Expectation: Call set_access_mode withing with scope must raise a RuntimeError
        with self.cam:
            self.assertRaises(RuntimeError, self.cam.set_access_mode)

    def test_camera_api_context_sensitity_inside_context(self):
        # Expectation: Most Camera related functions are only valid then called within the given
        # Context. If called from Outside a runtime error must be raised.
        self.assertRaises(RuntimeError, self.cam.read_memory)
        self.assertRaises(RuntimeError, self.cam.write_memory)
        self.assertRaises(RuntimeError, self.cam.read_registers)
        self.assertRaises(RuntimeError, self.cam.write_registers)
        self.assertRaises(RuntimeError, self.cam.get_all_features)
        self.assertRaises(RuntimeError, self.cam.get_features_affected_by)
        self.assertRaises(RuntimeError, self.cam.get_features_selected_by)
        self.assertRaises(RuntimeError, self.cam.get_features_by_type)
        self.assertRaises(RuntimeError, self.cam.get_features_by_category)
        self.assertRaises(RuntimeError, self.cam.get_feature_by_name)
        self.assertRaises(RuntimeError, self.cam.get_frame_generator)
        self.assertRaises(RuntimeError, self.cam.get_frame)
        self.assertRaises(RuntimeError, self.cam.start_streaming)
        self.assertRaises(RuntimeError, self.cam.stop_streaming)
        self.assertRaises(RuntimeError, self.cam.queue_frame)
        self.assertRaises(RuntimeError, self.cam.get_pixel_formats)
        self.assertRaises(RuntimeError, self.cam.get_pixel_format)
        self.assertRaises(RuntimeError, self.cam.set_pixel_format)
        self.assertRaises(RuntimeError, self.cam.save_settings)
        self.assertRaises(RuntimeError, self.cam.load_settings)
