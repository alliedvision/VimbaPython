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


class TracerTest(unittest.TestCase):
    def setUp(self):
        # Enable logging and setup hidden buffer
        self.log = Log.get_instance()
        self.log._test_buffer = []

        self.log.enable(LOG_CONFIG_CRITICAL_CONSOLE_ONLY)

    def tearDown(self):
        # Disable logging and clear hidden buffer
        self.log.disable()

        self.log._test_buffer = None

    def test_trace_inactive(self):
        # Expectation: A disabled log must not contain any trace entries.

        @TraceEnable()
        def test_func(arg):
            return str(arg)

        self.log.disable()

        self.assertEqual(test_func(1), '1')
        self.assertFalse(self.log._test_buffer)

        self.assertEqual(test_func('test'), 'test')
        self.assertFalse(self.log._test_buffer)

        self.assertEqual(test_func(2.0), '2.0')
        self.assertFalse(self.log._test_buffer)

    def test_trace_normal_exit(self):
        # Expectation: Must not throw on call normal func.
        # Each call traced call must add two Log entries:

        @TraceEnable()
        def test_func(arg):
            return str(arg)

        self.assertEqual(test_func(1), '1')
        self.assertEqual(len(self.log._test_buffer), 2)

        self.assertEqual(test_func('test'), 'test')
        self.assertEqual(len(self.log._test_buffer), 4)

        self.assertEqual(test_func(2.0), '2.0')
        self.assertEqual(len(self.log._test_buffer), 6)

    def test_trace_raised_exit(self):
        # Expectation: Throws internally thrown exception and adds two log entries
        # Each call traced call must add two Log entries:

        @TraceEnable()
        def test_func(arg):
            raise TypeError('my error')

        self.assertRaises(TypeError, test_func, 1)
        self.assertEqual(len(self.log._test_buffer), 2)

        self.assertRaises(TypeError, test_func, 'test')
        self.assertEqual(len(self.log._test_buffer), 4)

        self.assertRaises(TypeError, test_func, 2.0)
        self.assertEqual(len(self.log._test_buffer), 6)

    def test_trace_function(self):
        # Expectation: Normal functions must be traceable
        @TraceEnable()
        def test_func():
            pass

        test_func()
        self.assertEqual(len(self.log._test_buffer), 2)

        test_func()
        self.assertEqual(len(self.log._test_buffer), 4)

        test_func()
        self.assertEqual(len(self.log._test_buffer), 6)

    def test_trace_lambda(self):
        # Expectation: Lambdas must be traceable

        test_lambda = TraceEnable()(lambda: 0)

        test_lambda()
        self.assertEqual(len(self.log._test_buffer), 2)

        test_lambda()
        self.assertEqual(len(self.log._test_buffer), 4)

        test_lambda()
        self.assertEqual(len(self.log._test_buffer), 6)

    def test_trace_object(self):
        # Expectation: Objects must be traceable including constructors.
        class TestObj:
            @TraceEnable()
            def __init__(self, arg):
                self.arg = arg

            @TraceEnable()
            def __str__(self):
                return 'TestObj({})'.format(str(self.arg))

            @TraceEnable()
            def __repr__(self):
                return 'TestObj({})'.format(repr(self.arg))

            @TraceEnable()
            def __call__(self):
                pass

        test_obj = TestObj('test')
        self.assertEqual(len(self.log._test_buffer), 2)

        str(test_obj)
        self.assertEqual(len(self.log._test_buffer), 4)

        repr(test_obj)
        self.assertEqual(len(self.log._test_buffer), 6)

        test_obj()
        self.assertEqual(len(self.log._test_buffer), 8)
