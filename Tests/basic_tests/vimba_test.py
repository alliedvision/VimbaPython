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


class VimbaTest(unittest.TestCase):
    def setUp(self):
        self.vimba = Vimba.get_instance()

    def tearDown(self):
        pass

    def test_singleton(self):
        # Expected behavior: Multiple calls to Vimba.get_instance() return the same object.
        self.assertEqual(self.vimba, Vimba.get_instance())

    def test_get_version(self):
        # Expectation: Returned Version is not empty and does not raise any exceptions.
        self.assertNotEqual(self.vimba.get_version(), "")

    def test_get_camera_by_id_failure(self):
        # Expected behavior: Lookup of a currently unavailable camera must throw an
        # VimbaCameraError
        with self.vimba:
            self.assertRaises(VimbaCameraError, self.vimba.get_camera_by_id, 'Invalid ID')

    def test_get_interface_by_id_failure(self):
        # Expected behavior: Lookup of a currently unavailable interface must throw an
        # VimbaInterfaceError
        with self.vimba:
            self.assertRaises(VimbaInterfaceError, self.vimba.get_interface_by_id, 'Invalid ID')

    def test_get_feature_by_name_failure(self):
        # Expected behavior: Lookup of a currently unavailable feature must throw an
        # VimbaFeatureError
        with self.vimba:
            self.assertRaises(VimbaFeatureError, self.vimba.get_feature_by_name, 'Invalid ID')

    def test_runtime_check_failure(self):
        self.assertRaises(TypeError, self.vimba.set_network_discovery, 0.0)

        with self.vimba:
            # All functions with RuntimeTypeCheckEnable must return a TypeError on Failure
            self.assertRaises(TypeError, self.vimba.get_camera_by_id, 0)
            self.assertRaises(TypeError, self.vimba.get_interface_by_id, 1)
            self.assertRaises(TypeError, self.vimba.get_feature_by_name, 0)
            self.assertRaises(TypeError, self.vimba.enable_log, '-1')

            self.assertRaises(TypeError, self.vimba.get_features_affected_by, '-1')
            self.assertRaises(TypeError, self.vimba.get_features_selected_by, '-1')
            self.assertRaises(TypeError, self.vimba.get_features_by_type, [])
            self.assertRaises(TypeError, self.vimba.register_camera_change_handler, 0)
            self.assertRaises(TypeError, self.vimba.unregister_camera_change_handler, 0)
            self.assertRaises(TypeError, self.vimba.register_interface_change_handler, 0)
            self.assertRaises(TypeError, self.vimba.unregister_interface_change_handler, 0)

    def test_vimba_context_manager_reentrancy(self):
        # Expectation: Implemented Context Manager must be reentrant, not causing
        # multiple starts of the Vimba API (would cause C-Errors)

        with self.vimba:
            with self.vimba:
                with self.vimba:
                    pass

    def test_vimba_api_context_sensitity_outside_context(self):
        # Expectation: Vimba has functions that shall only be callable outside the Context and
        # calling within the context must cause a runtime error.

        self.assertNoRaise(self.vimba.set_network_discovery, True)

        with self.vimba:
            self.assertRaises(RuntimeError, self.vimba.set_network_discovery, True)

        self.assertNoRaise(self.vimba.set_network_discovery, True)

    def test_vimba_api_context_sensitity_inside_context(self):
        # Expectation: Vimba has functions that shall only be callable inside the Context and
        # calling outside must cause a runtime error. This test check only if the RuntimeErrors
        # are triggered then called Outside of the with block.
        self.assertRaises(RuntimeError, self.vimba.read_memory, 0, 0)
        self.assertRaises(RuntimeError, self.vimba.write_memory, 0, b'foo')
        self.assertRaises(RuntimeError, self.vimba.read_registers, ())
        self.assertRaises(RuntimeError, self.vimba.write_registers, {0: 0})
        self.assertRaises(RuntimeError, self.vimba.get_all_interfaces)
        self.assertRaises(RuntimeError, self.vimba.get_interface_by_id, 'id')
        self.assertRaises(RuntimeError, self.vimba.get_all_cameras)
        self.assertRaises(RuntimeError, self.vimba.get_camera_by_id, 'id')
        self.assertRaises(RuntimeError, self.vimba.get_all_features)

        # Enter scope to get handle on Features as valid parameters for the test:
        # Don't to this in production code because the feature will be invalid if use.
        with self.vimba:
            feat = self.vimba.get_all_features()[0]

        self.assertRaises(RuntimeError, self.vimba.get_features_affected_by, feat)
        self.assertRaises(RuntimeError, self.vimba.get_features_selected_by, feat)
        self.assertRaises(RuntimeError, self.vimba.get_features_by_type, IntFeature)
        self.assertRaises(RuntimeError, self.vimba.get_features_by_category, 'foo')
        self.assertRaises(RuntimeError, self.vimba.get_feature_by_name, 'foo')
