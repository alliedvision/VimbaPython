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

from vimba.c_binding import _select_vimba_home
from vimba.error import VimbaSystemError


class RankVimbaHomeCandidatesTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_empty_gentl_path(self):
        candidates = []
        with self.assertRaises(VimbaSystemError):
            _select_vimba_home(candidates)

    def test_empty_string(self):
        candidates = ['']
        with self.assertRaises(VimbaSystemError):
            _select_vimba_home(candidates)

    def test_single_bad_vimba_home_candidate(self):
        candidates = ['/some/path']
        with self.assertRaises(VimbaSystemError):
            _select_vimba_home(candidates)

    def test_single_good_vimba_home_candidate(self):
        candidates = ['/opt/Vimba_3_1']
        expected = '/opt/Vimba_3_1'
        self.assertEquals(expected, _select_vimba_home(candidates))

    def test_presorted_vimba_home_candidates(self):
        candidates = ['/home/username/Vimba_4_0', '/opt/some/other/gentl/provider']
        expected = '/home/username/Vimba_4_0'
        self.assertEqual(expected, _select_vimba_home(candidates))

    def test_unsorted_vimba_home_candidates(self):
        candidates = ['/opt/some/other/gentl/provider', '/home/username/Vimba_4_0']
        expected = '/home/username/Vimba_4_0'
        self.assertEqual(expected, _select_vimba_home(candidates))

    def test_many_vimba_home_candidates(self):
        candidates = ['/some/random/path',
                      '/opt/some/gentl/provider',
                      '/opt/Vimba_4_0',  # This should be selected
                      '/opt/another/gentl/provider',
                      '/another/incorrect/path']
        expected = '/opt/Vimba_4_0'
        self.assertEqual(expected, _select_vimba_home(candidates))

    def test_multiple_vimba_home_directories(self):
        # If multiple VIMBA_HOME directories are found an error should be raised
        candidates = ['/some/random/path',
                      '/opt/some/gentl/provider',
                      '/opt/Vimba_4_0',  # first installation
                      '/home/username/Vimba_4_0',  # second installation
                      '/opt/another/gentl/provider',
                      '/another/incorrect/path']
        with self.assertRaises(VimbaSystemError):
            _select_vimba_home(candidates)
