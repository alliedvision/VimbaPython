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

from vimba.util import *


class TestObj:
    @LeaveContextOnCall()
    def __init__(self):
        pass

    @EnterContextOnCall()
    def __enter__(self):
        pass

    @LeaveContextOnCall()
    def __exit__(self, _1, _2, _3):
        pass

    @RaiseIfOutsideContext()
    def works_inside_context(self):
        pass

    @RaiseIfInsideContext()
    def works_outside_context(self):
        pass


class ContextDecoratorTest(unittest.TestCase):
    def setUp(self):
        self.test_obj = TestObj()

    def tearDown(self):
        pass

    def test_raise_if_inside_context(self):
        # Expectation: a decorated method must raise a RuntimeError if a
        # Decorated function is called within a with - statement and
        # run properly outside of the context.

        self.assertNoRaise(self.test_obj.works_outside_context)

        with self.test_obj:
            self.assertRaises(RuntimeError, self.test_obj.works_outside_context)

        self.assertNoRaise(self.test_obj.works_outside_context)

    def test_raise_if_outside_context(self):
        # Expectation: a decorated method must raise a RuntimeError if a
        # Decorated function is called outside a with - statement and
        # run properly inside of the context.

        self.assertRaises(RuntimeError, self.test_obj.works_inside_context)

        with self.test_obj:
            self.assertNoRaise(self.test_obj.works_inside_context)

        self.assertRaises(RuntimeError, self.test_obj.works_inside_context)
