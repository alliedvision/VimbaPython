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
import pickle
import copy
import ctypes

from vimba import *
from vimba.frame import *


class CamFrameTest(unittest.TestCase):
    def setUp(self):
        self.vimba = Vimba.get_instance()
        self.vimba._startup()

        try:
            self.cam = self.vimba.get_camera_by_id(self.get_test_camera_id())

        except VimbaCameraError as e:
            self.vimba._shutdown()
            raise Exception('Failed to lookup Camera.') from e

    def tearDown(self):
        self.vimba._shutdown()

    def test_verify_buffer(self):
        # Expectation: A Frame buffer shall have exactly the specified size on construction.
        self.assertEqual(Frame(0).get_buffer_size(), 0)
        self.assertEqual(Frame(1024).get_buffer_size(), 1024)
        self.assertEqual(Frame(1024 * 1024).get_buffer_size(), 1024 * 1024)

    def test_verify_no_copy_buffer_access(self):
        # Expectation: Accessing the internal buffer must not create a copy
        frame = Frame(10)
        self.assertEqual(id(frame._buffer), id(frame.get_buffer()))

    def test_get_id(self):
        # Expectation: get_id() must return None if Its locally constructed
        # else it must return the frame id.
        self.assertIsNone(Frame(0).get_id())

        with self.cam:
            self.assertIsNotNone(self.cam.get_frame().get_id())

    def test_get_timestamp(self):
        # Expectation: get_timestamp() must return None if Its locally constructed
        # else it must return the timestamp.
        self.assertIsNone(Frame(0).get_timestamp())

        with self.cam:
            self.assertIsNotNone(self.cam.get_frame().get_timestamp())

    def test_get_offset(self):
        # Expectation: get_offset_x() must return None if Its locally constructed
        # else it must return the offset as int. Same goes for get_offset_y()

        self.assertIsNone(Frame(0).get_offset_x())
        self.assertIsNone(Frame(0).get_offset_y())

    def test_get_dimension(self):
        # Expectation: get_width() must return None if Its locally constructed
        # else it must return the offset as int. Same goes for get_height()

        self.assertIsNone(Frame(0).get_width())
        self.assertIsNone(Frame(0).get_height())

        with self.cam:
            frame = self.cam.get_frame()
            self.assertIsNotNone(frame.get_width())
            self.assertIsNotNone(frame.get_height())

    def test_get_image_size(self):
        # Expectation: get_image_size() must return 0 if locally constructed
        # else it must return the image_size as int.

        self.assertEquals(Frame(0).get_image_size(), 0)

        with self.cam:
            self.assertNotEquals(self.cam.get_frame().get_image_size(), 0)

    def test_deepcopy(self):
        # Expectation: a deepcopy must clone the frame buffer with its contents an
        # update the internally store pointer in VmbFrame struct.

        with self.cam:
            frame = self.cam.get_frame()

        frame_cpy = copy.deepcopy(frame)

        # Ensure frames and their members are not the same object
        self.assertNotEquals(id(frame), id(frame_cpy))
        self.assertNotEquals(id(frame._buffer), id(frame_cpy._buffer))
        self.assertNotEquals(id(frame._frame), id(frame_cpy._frame))

        # Ensure that both buffers have the same size and contain the same data.
        self.assertEquals(frame.get_buffer_size(), frame_cpy.get_buffer_size())
        self.assertEquals(frame.get_buffer().raw, frame_cpy.get_buffer().raw)

        # Ensure that internal Frame Pointer points to correct buffer.
        self.assertEquals(frame._frame.buffer,
                          ctypes.cast(frame._buffer, ctypes.c_void_p).value)

        self.assertEquals(frame_cpy._frame.buffer,
                          ctypes.cast(frame_cpy._buffer, ctypes.c_void_p).value)

        self.assertEquals(frame._frame.bufferSize, frame_cpy._frame.bufferSize)

    def test_get_pixel_format(self):
        # Expectation: Frames have an image format set after acquisition
        with self.cam:
            self.assertNotEquals(self.cam.get_frame().get_pixel_format(), 0)

    def test_incompatible_formats_value_error(self):
        # Expectation: Conversion into incompatible formats must lead to an value error
        with self.cam:
            frame = self.cam.get_frame()

        current_fmt = frame.get_pixel_format()
        convertable_fmt = current_fmt.get_convertible_formats()

        for fmt in PixelFormat.__members__.values():
            if (fmt != current_fmt) and (fmt not in convertable_fmt):
                self.assertRaises(ValueError, frame.convert_pixel_format, fmt)

    def test_convert_to_all_given_formats(self):
        # Expectation: A Series of Frame, each acquired with a different Pixel format
        # Must be convertible to all formats the given format claims its convertible to without any
        # errors.

        test_frames = []

        with self.cam:
            for fmt in self.cam.get_pixel_formats():
                self.cam.set_pixel_format(fmt)

                frame = self.cam.get_frame()

                self.assertEqual(fmt, frame.get_pixel_format())
                test_frames.append(frame)

        for frame in test_frames:

            # The test shall work on a copy to keep the original Frame untouched
            for expected_fmt in frame.get_pixel_format().get_convertible_formats():
                cpy_frame = copy.deepcopy(frame)
                cpy_frame.convert_pixel_format(expected_fmt)

                self.assertEquals(expected_fmt, cpy_frame.get_pixel_format())
