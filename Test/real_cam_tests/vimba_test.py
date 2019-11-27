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


class RealCamTestsVimbaTest(unittest.TestCase):
    def setUp(self):
        self.vimba = Vimba.get_instance()

    def tearDown(self):
        pass

    def test_context_entry_exit(self):
        """ Expected Behavior:
        Before context entry Vimba shall have no detected features, no detected cameras and
        no detected Interfaces. On entering the context features, cameras and interfaces shall
        be detected and after leaving the context, everything should be reverted.
        """
        self.assertEqual(self.vimba.get_all_features(), ())
        self.assertEqual(self.vimba.get_all_interfaces(), ())
        self.assertEqual(self.vimba.get_all_cameras(), ())

        with self.vimba:
            self.assertNotEqual(self.vimba.get_all_features(), ())
            self.assertNotEqual(self.vimba.get_all_interfaces(), ())
            self.assertNotEqual(self.vimba.get_all_cameras(), ())

        self.assertEqual(self.vimba.get_all_features(), ())
        self.assertEqual(self.vimba.get_all_interfaces(), ())
        self.assertEqual(self.vimba.get_all_cameras(), ())

    def test_get_all_interfaces(self):
        """Expected Behavior: get_all_interfaces() must be empty in closed state and
           non-empty then opened.
        """
        self.assertFalse(self.vimba.get_all_interfaces())

        with self.vimba:
            self.assertTrue(self.vimba.get_all_interfaces())

    def test_get_interface_by_id(self):
        """Expected Behavior: All detected Interfaces must be lookup able by their Id.
        If outside of given scope, an error must be returned
        """

        with self.vimba:
            ids = [inter.get_id() for inter in self.vimba.get_all_interfaces()]

            for id_ in ids:
                self.assertNoRaise(self.vimba.get_interface_by_id, id_)

        for id_ in ids:
            self.assertRaises(VimbaInterfaceError, self.vimba.get_interface_by_id, id_)

    def test_get_all_cameras(self):
        """Expected Behavior: get_all_cameras() must only return camera handles on a open camera.
        """
        self.assertFalse(self.vimba.get_all_cameras())

        with self.vimba:
            self.assertTrue(self.vimba.get_all_cameras())

    def test_get_camera_by_id(self):
        """Expected Behavior: Lookup of test camera must not fail after system opening """
        camera_id = self.get_test_camera_id()
        self.assertRaises(VimbaCameraError, self.vimba.get_camera_by_id, camera_id)

        with self.vimba:
            self.assertNoRaise(self.vimba.get_camera_by_id, camera_id)

        self.assertRaises(VimbaCameraError, self.vimba.get_camera_by_id, camera_id)
