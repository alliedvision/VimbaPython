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

import unittest

from vimba import *


class VimbaTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_singleton(self):
        """Expected behavior: Multiple calls to Vimba.get_instance() return the same object."""
        self.assertEqual(Vimba.get_instance(), Vimba.get_instance())

    def test_get_camera_by_id_failure(self):
        """Expected behavior: Lookup of a currently unavailable camera must throw an
        VimbaCameraError regardless of context.
        """
        vimba = Vimba.get_instance()

        self.assertRaises(VimbaCameraError, vimba.get_camera_by_id, 'Invalid ID')

        with vimba:
            self.assertRaises(VimbaCameraError, vimba.get_camera_by_id, 'Invalid ID')

        self.assertRaises(VimbaCameraError, vimba.get_camera_by_id, 'Invalid ID')

    def test_get_interface_by_id_failure(self):
        """Expected behavior: Lookup of a currently unavailable interface must throw an
        VimbaInterfaceError regardless of context.
        """
        vimba = Vimba.get_instance()

        self.assertRaises(VimbaInterfaceError, vimba.get_interface_by_id, 'Invalid ID')

        with vimba:
            self.assertRaises(VimbaInterfaceError, vimba.get_interface_by_id, 'Invalid ID')

        self.assertRaises(VimbaInterfaceError, vimba.get_interface_by_id, 'Invalid ID')

    def test_get_feature_by_name_failure(self):
        """Expected behavior: Lookup of a currently unavailable feature must throw an
        VimbaFeatureError regardless of context.
        """
        vimba = Vimba.get_instance()

        self.assertRaises(VimbaFeatureError, vimba.get_feature_by_name, 'Invalid ID')

        with vimba:
            self.assertRaises(VimbaFeatureError, vimba.get_feature_by_name, 'Invalid ID')

        self.assertRaises(VimbaFeatureError, vimba.get_feature_by_name, 'Invalid ID')

    def test_runtime_check_failure(self):
        """All functions with RuntimeTypeCheckEnable must return a TypeError on Failure"""
        vimba = Vimba.get_instance()

        self.assertRaises(TypeError, vimba.set_network_discovery, 0.0)
        self.assertRaises(TypeError, vimba.get_camera_by_id, 0)
        self.assertRaises(TypeError, vimba.get_interface_by_id, 1)
        self.assertRaises(TypeError, vimba.get_feature_by_name, 0)
        self.assertRaises(TypeError, vimba.enable_log, '-1')

        self.assertRaises(TypeError, vimba.get_features_affected_by, '-1')
        self.assertRaises(TypeError, vimba.get_features_selected_by, '-1')
        self.assertRaises(TypeError, vimba.get_features_by_type, [])
        self.assertRaises(TypeError, vimba.register_camera_change_handler, 0)
        self.assertRaises(TypeError, vimba.unregister_camera_change_handler, 0)
        self.assertRaises(TypeError, vimba.register_interface_change_handler, 0)
        self.assertRaises(TypeError, vimba.unregister_interface_change_handler, 0)
