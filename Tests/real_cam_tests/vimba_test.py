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
import ipaddress
import struct

from vimba import *


class CamVimbaTest(unittest.TestCase):
    def setUp(self):
        self.vimba = Vimba.get_instance()

    def tearDown(self):
        pass

    def test_context_entry_exit(self):
        # Expected Behavior:
        # On entering the context features, cameras and interfaces shall
        # be detected and after leaving the context, everything should be reverted.

        self.assertRaises(RuntimeError, self.vimba.get_all_features)
        self.assertRaises(RuntimeError, self.vimba.get_all_interfaces)
        self.assertRaises(RuntimeError, self.vimba.get_all_cameras)

        with self.vimba:
            self.assertNotEqual(self.vimba.get_all_features(), ())
            self.assertNotEqual(self.vimba.get_all_interfaces(), ())
            self.assertNotEqual(self.vimba.get_all_cameras(), ())

        self.assertRaises(RuntimeError, self.vimba.get_all_features)
        self.assertRaises(RuntimeError, self.vimba.get_all_interfaces)
        self.assertRaises(RuntimeError, self.vimba.get_all_cameras)

    def test_get_all_interfaces(self):
        # Expected Behavior: get_all_interfaces() must raise an RuntimeError in closed state and
        # be non-empty then opened.
        self.assertRaises(RuntimeError, self.vimba.get_all_interfaces)

        with self.vimba:
            self.assertTrue(self.vimba.get_all_interfaces())

    def test_get_interface_by_id(self):
        # Expected Behavior: All detected Interfaces must be lookup able by their Id.
        # If outside of given scope, an error must be returned
        with self.vimba:
            ids = [inter.get_id() for inter in self.vimba.get_all_interfaces()]

            for id_ in ids:
                self.assertNoRaise(self.vimba.get_interface_by_id, id_)

        for id_ in ids:
            self.assertRaises(RuntimeError, self.vimba.get_interface_by_id, id_)

    def test_get_all_cameras(self):
        # Expected Behavior: get_all_cameras() must only return camera handles on a open camera.
        self.assertRaises(RuntimeError, self.vimba.get_all_cameras)

        with self.vimba:
            self.assertTrue(self.vimba.get_all_cameras())

    def test_get_camera_by_id(self):
        # Expected Behavior: Lookup of test camera must not fail after system opening
        camera_id = self.get_test_camera_id()

        with self.vimba:
            self.assertNoRaise(self.vimba.get_camera_by_id, camera_id)

    def test_get_camera_by_ip(self):
        # Expected Behavior: get_camera_by_id() must work with a valid ipv4 address.
        # A with lookup of an invalid ipv4 address (no Camera attached)
        # must raise a VimbaCameraError, a lookup with an ipv6 address must raise a
        # VimbaCameraError in general (VimbaC doesn't support ipv6)
        with self.vimba:
            # Verify that the Test Camera is a GigE - Camera
            cam = self.vimba.get_camera_by_id(self.get_test_camera_id())
            inter = self.vimba.get_interface_by_id(cam.get_interface_id())

            if inter.get_type() != InterfaceType.Ethernet:
                raise self.skipTest('Test requires GigE - Camera.')

            # Lookup test cameras IP address.
            with cam:
                ip_as_number = cam.get_feature_by_name('GevCurrentIPAddress').get()

            # Swap byte order, the raw value does not seem to follow network byte order.
            ip_as_number = struct.pack('<L', ip_as_number)

            # Verify that lookup with IPv4 Address returns the same Camera Object
            ip_addr = str(ipaddress.IPv4Address(ip_as_number))
            self.assertEqual(self.vimba.get_camera_by_id(ip_addr), cam)

            # Verify that a lookup with an invalid IPv4 Address raises a VimbaCameraError
            ip_addr = str(ipaddress.IPv4Address('127.0.0.1'))
            self.assertRaises(VimbaCameraError, self.vimba.get_camera_by_id, ip_addr)

            # Verify that a lookup with an IPv6 Address raises a VimbaCameraError
            ip_addr = str(ipaddress.IPv6Address('FD00::DEAD:BEEF'))
            self.assertRaises(VimbaCameraError, self.vimba.get_camera_by_id, ip_addr)

    def test_get_camera_by_mac(self):
        # Expected Behavior: get_feature_by_id must be usable with a given MAC Address.
        with self.vimba:
            # Verify that the Test Camera is a GigE - Camera
            cam = self.vimba.get_camera_by_id(self.get_test_camera_id())
            inter = self.vimba.get_interface_by_id(cam.get_interface_id())

            if inter.get_type() != InterfaceType.Ethernet:
                raise self.skipTest('Test requires GigE - Camera.')

            # Lookup test cameras MAC Address.
            with cam:
                # Construct MAC Address from raw value.
                mac_as_number = cam.get_feature_by_name('GevDeviceMACAddress').get()

            mac_as_bytes = mac_as_number.to_bytes(6, byteorder='big')
            mac_as_str = ''.join(format(s, '02x') for s in mac_as_bytes).upper()

            # Verify that lookup with MAC Address returns the same Camera Object
            self.assertEqual(self.vimba.get_camera_by_id(mac_as_str), cam)

            # Verify that a lookup with an invalid MAC Address raises a VimbaCameraError
            invalid_mac = 'ffffffff'
            self.assertRaises(VimbaCameraError, self.vimba.get_camera_by_id, invalid_mac)
