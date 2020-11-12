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


class InterfaceTest(unittest.TestCase):
    def setUp(self):
        self.vimba = Vimba.get_instance()
        self.vimba._startup()

        inters = self.vimba.get_all_interfaces()

        if not inters:
            self.vimba._shutdown()
            self.skipTest('No Interface available to test against. Abort.')

    def tearDown(self):
        self.vimba._shutdown()

    def test_interface_decode_id(self):
        # Expectation all interface ids can be decoded in something not ''
        for i in self.vimba.get_all_interfaces():
            self.assertNotEqual(i.get_id(), '')

    def test_interface_decode_type(self):
        # Expectation all interface types be in interface types
        excpected = (
            InterfaceType.Firewire,
            InterfaceType.Ethernet,
            InterfaceType.Usb,
            InterfaceType.CL,
            InterfaceType.CSI2,
        )

        for i in self.vimba.get_all_interfaces():
            self.assertIn(i.get_type(), excpected)

    def test_interface_decode_name(self):
        # Expectation all interface names  can be decoded in something not ''
        for i in self.vimba.get_all_interfaces():
            self.assertNotEqual(i.get_name(), '')

    def test_interface_decode_serial(self):
        # Expectation: Serials can be '' on some interfaces. This test success
        # if get serial does not raise
        for i in self.vimba.get_all_interfaces():
            self.assertNoRaise(i.get_serial)

    def test_interface_get_all_features(self):
        # Expectation: Call get_all_features raises RuntimeError outside of with
        # Inside of with return a non empty set
        with self.vimba.get_all_interfaces()[0] as inter:
            self.assertNotEqual(inter.get_all_features(), ())

    def test_interface_get_features_affected_by(self):
        # Expectation: Call get_features_affected_by raises RuntimeError outside of with.
        # Inside with it must either return and empty set if the given feature has no affected
        # Feature or a set off affected features
        with self.vimba.get_all_interfaces()[0] as inter:
            try:
                affects_feats = inter.get_feature_by_name('DeviceUpdateList')

            except VimbaFeatureError:
                self.skipTest('Test requires Feature \'DeviceUpdateList\'.')

            try:
                not_affects_feats = inter.get_feature_by_name('DeviceCount')

            except VimbaFeatureError:
                self.skipTest('Test requires Feature \'DeviceCount\'.')

            self.assertTrue(affects_feats.has_affected_features())
            self.assertNotEquals(inter.get_features_affected_by(affects_feats), ())

            self.assertFalse(not_affects_feats.has_affected_features())
            self.assertEquals(inter.get_features_affected_by(not_affects_feats), ())

    def test_interface_get_features_selected_by(self):
        # Expectation: Call get_features_selected_by raises RuntimeError outside of with.
        # Inside with it must either return and empty set if the given feature has no selected
        # Feature or a set off affected features
        with self.vimba.get_all_interfaces()[0] as inter:
            try:
                selects_feats = inter.get_feature_by_name('DeviceSelector')

            except VimbaFeatureError:
                self.skipTest('Test requires Feature \'DeviceSelector\'.')

            try:
                not_selects_feats = inter.get_feature_by_name('DeviceCount')

            except VimbaFeatureError:
                self.skipTest('Test requires Feature \'DeviceCount\'.')

            self.assertTrue(selects_feats.has_selected_features())
            self.assertNotEquals(inter.get_features_selected_by(selects_feats), ())

            self.assertFalse(not_selects_feats.has_selected_features())
            self.assertEquals(inter.get_features_selected_by(not_selects_feats), ())

    def test_interface_get_features_by_type(self):
        # Expectation: Call get_features_by_type raises RuntimeError outside of with
        # Inside of with return a non empty set for IntFeature (DeviceCount is IntFeature)
        with self.vimba.get_all_interfaces()[0] as inter:
            self.assertNotEqual(inter.get_features_by_type(IntFeature), ())

    def test_interface_get_features_by_category(self):
        # Expectation: Call get_features_by_category raises RuntimeError outside of with
        # Inside of with return a non empty set for /DeviceEnumeration)
        with self.vimba.get_all_interfaces()[0] as inter:
            self.assertNotEqual(inter.get_features_by_category('/DeviceEnumeration'), ())

    def test_interface_get_feature_by_name(self):
        # Expectation: Call get_feature_by_name raises RuntimeError outside of with
        # Inside of with return dont raise VimbaFeatureError for 'DeviceCount'
        # A invalid name must raise VimbaFeatureError
        with self.vimba.get_all_interfaces()[0] as inter:
            self.assertNoRaise(inter.get_feature_by_name, 'DeviceCount')
            self.assertRaises(VimbaFeatureError, inter.get_feature_by_name, 'Invalid Name')

    def test_interface_context_manager_reentrancy(self):
        # Expectation: Implemented Context Manager must be reentrant, not causing
        # multiple interface openings (would cause C-Errors)
        with self.vimba.get_all_interfaces()[0] as inter:
            with inter:
                with inter:
                    pass

    def test_interface_api_context_sensitivity_inside_context(self):
        # Expectation: Interface has functions that shall only be callable inside the Context,
        # calling outside must cause a runtime error. This test check only if the RuntimeErrors
        # are triggered then called Outside of the with block.
        inter = self.vimba.get_all_interfaces()[0]

        self.assertRaises(RuntimeError, inter.read_memory, 0, 0)
        self.assertRaises(RuntimeError, inter.write_memory, 0, b'foo')
        self.assertRaises(RuntimeError, inter.read_registers, ())
        self.assertRaises(RuntimeError, inter.write_registers, {0: 0})
        self.assertRaises(RuntimeError, inter.get_all_features)

        # Enter scope to get handle on Features as valid parameters for the test:
        # Don't to this in production code because the features will be invalid if used.
        with inter:
            feat = inter.get_all_features()[0]

        self.assertRaises(RuntimeError, inter.get_features_affected_by, feat)
        self.assertRaises(RuntimeError, inter.get_features_selected_by, feat)
        self.assertRaises(RuntimeError, inter.get_features_by_type, IntFeature)
        self.assertRaises(RuntimeError, inter.get_features_by_category, 'foo')
        self.assertRaises(RuntimeError, inter.get_feature_by_name, 'foo')
