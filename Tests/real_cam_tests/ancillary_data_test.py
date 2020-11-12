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

from vimba import *


class CamAncillaryDataTest(unittest.TestCase):
    def setUp(self):
        self.vimba = Vimba.get_instance()
        self.vimba._startup()

        try:
            self.cam = self.vimba.get_camera_by_id(self.get_test_camera_id())

        except VimbaCameraError as e:
            self.vimba._shutdown()
            raise Exception('Failed to lookup Camera.') from e

        try:
            self.cam._open()

        except VimbaCameraError as e:
            self.vimba._shutdown()
            raise Exception('Failed to open Camera.') from e

        try:
            self.chunk_mode = self.cam.get_feature_by_name('ChunkModeActive')

        except VimbaFeatureError:
            self.cam._close()
            self.vimba._shutdown()
            self.skipTest('Required Feature \'ChunkModeActive\' not available.')

    def tearDown(self):
        self.cam._close()
        self.vimba._shutdown()

    def test_ancillary_data_access(self):
        # Expectation: Ancillary Data is None if ChunkMode is disable.
        # If ChunkMode is enabled Ancillary Data shall not be None.

        old_state = self.chunk_mode.get()

        try:
            # Disable ChunkMode, acquire frame: Ancillary Data must be None
            self.chunk_mode.set(False)
            self.assertIsNone(self.cam.get_frame().get_ancillary_data())

            # Enable ChunkMode, acquire frame: Ancillary Data must not be None
            self.chunk_mode.set(True)
            self.assertIsNotNone(self.cam.get_frame().get_ancillary_data())

        finally:
            self.chunk_mode.set(old_state)

    def test_ancillary_data_context_manager_reentrancy(self):
        # Expectation: Ancillary Data Context Manager must be reentrant.
        old_state = self.chunk_mode.get()

        try:
            self.chunk_mode.set(True)
            frame = self.cam.get_frame()
            anc_data = frame.get_ancillary_data()

            with anc_data:
                with anc_data:
                    with anc_data:
                        pass

        finally:
            self.chunk_mode.set(old_state)

    def test_ancillary_data_api_context_sensitity(self):
        # Expectation: Ancillary Data implements a Context Manager, outside of with-scope
        # a runtime error should be raised on all feature related methods accessed outside of the
        # context.

        old_state = self.chunk_mode.get()

        try:
            self.chunk_mode.set(True)
            frame = self.cam.get_frame()
            anc_data = frame.get_ancillary_data()

            # Check Access Outside Context
            self.assertRaises(RuntimeError, anc_data.get_all_features)
            self.assertRaises(RuntimeError, anc_data.get_features_by_type, IntFeature)
            self.assertRaises(RuntimeError, anc_data.get_features_by_category, '/ChunkData')
            self.assertRaises(RuntimeError, anc_data.get_feature_by_name, 'ChunkExposureTime')

            with anc_data:
                # Check Access after Context entry
                self.assertNoRaise(anc_data.get_all_features)
                self.assertNoRaise(anc_data.get_features_by_type, IntFeature)
                self.assertNoRaise(anc_data.get_features_by_category, '/ChunkData')
                self.assertNoRaise(anc_data.get_feature_by_name, 'ChunkExposureTime')

            # Check Access after Context leaving
            self.assertRaises(RuntimeError, anc_data.get_all_features)
            self.assertRaises(RuntimeError, anc_data.get_features_by_type, IntFeature)
            self.assertRaises(RuntimeError, anc_data.get_features_by_category, '/ChunkData')
            self.assertRaises(RuntimeError, anc_data.get_feature_by_name, 'ChunkExposureTime')

        finally:
            self.chunk_mode.set(old_state)

    def test_ancillary_data_removed_attrs(self):
        # Expectation: Ancillary Data are lightweight features. Calling most Feature-Methods that
        # call VimbaC Features would cause an internal error. Those error prone methods
        # shall raise a RuntimeError on call.

        old_state = self.chunk_mode.get()

        try:
            self.chunk_mode.set(True)
            frame = self.cam.get_frame()
            anc_data = frame.get_ancillary_data()

            with anc_data:
                for feat in anc_data.get_all_features():
                    self.assertRaises(RuntimeError, feat.get_access_mode)
                    self.assertRaises(RuntimeError, feat.is_readable)
                    self.assertRaises(RuntimeError, feat.is_writeable)
                    self.assertRaises(RuntimeError, feat.register_change_handler)
                    self.assertRaises(RuntimeError, feat.get_range)
                    self.assertRaises(RuntimeError, feat.get_increment)
                    self.assertRaises(RuntimeError, feat.set)
        finally:
            self.chunk_mode.set(old_state)
