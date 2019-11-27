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
import docopt


# Inject 'assertNotRaise' to default test module. Tests are derived from this class.
def _assertNoRaise(self, func, *args, **kwargs):
    try:
        func(*args, **kwargs)

    except BaseException as e:
        self.fail('Function raised: {}'.format(e))


# Inject shared test camera id into the base TestCase
def _get_test_camera_id(self) -> str:
    return unittest.TestCase.test_cam_id


def _set_test_camera_id(test_cam_id) -> str:
    unittest.TestCase.test_cam_id = test_cam_id


unittest.TestCase.assertNoRaise = _assertNoRaise
unittest.TestCase.set_test_camera_id = _set_test_camera_id
unittest.TestCase.get_test_camera_id = _get_test_camera_id


def main():
    CLI = """VimbaPython test runner.
    Usage:
        runner.py -h
        runner.py -s basic -o console
        runner.py -s basic -o junit_xml REPORT_DIR
        runner.py -s (real_cam | all) -c CAMERA_ID -o console
        runner.py -s (real_cam | all) -c CAMERA_ID -o junit_xml REPORT_DIR

    Arguments:
        CAMERA_ID    Camera Id from Camera that shall be used during testing
        REPORT_DIR   Directory used for junit_export.

    Options:
        -h   Show this screen.
        -s   Testsuite to execute. real_cam and all require a camera to
             run tests against, therefore -c is mandatory.
        -c   Camera Id used while testing.
        -o   Test output: Either console or junit_xml.
    """

    args = docopt.docopt(CLI)
    loader = unittest.TestLoader()

    if args['CAMERA_ID']:
        unittest.TestCase.set_test_camera_id(args['CAMERA_ID'])

    else:
        unittest.TestCase.set_test_camera_id(None)

    # Select TestRunner
    if args['console']:
        runner = unittest.TextTestRunner(verbosity=1)

    elif args['junit_xml']:
        import xmlrunner
        runner = xmlrunner.XMLTestRunner(output=args['REPORT_DIR'])

    # Import tests cases
    import tests.c_binding_test
    import tests.util_runtime_type_check_test
    import tests.util_tracer_test
    import tests.vimba_test

    import real_cam_tests.vimba_test
    import real_cam_tests.feature_test
    import real_cam_tests.camera_test
    import real_cam_tests.frame_test

    # Assign test cases to test suites
    BASIC_TEST_MODS = [
        tests.c_binding_test,
        tests.util_runtime_type_check_test,
        tests.util_tracer_test,
        tests.vimba_test
    ]

    REAL_CAM_TEST_MODS = [
        real_cam_tests.vimba_test,
        real_cam_tests.feature_test,
        real_cam_tests.camera_test,
        real_cam_tests.frame_test
    ]

    # Prepare TestSuites
    suite_basic = unittest.TestSuite()
    for mod in BASIC_TEST_MODS:
        suite_basic.addTests(loader.loadTestsFromModule(mod))

    suite_real_cam = unittest.TestSuite()
    for mod in REAL_CAM_TEST_MODS:
        suite_real_cam.addTests(loader.loadTestsFromModule(mod))

    # Execute TestSuites
    if args['basic']:
        runner.run(suite_basic)

    elif args['real_cam']:
        runner.run(suite_real_cam)

    elif args['all']:
        runner.run(suite_basic)
        runner.run(suite_real_cam)


if __name__ == '__main__':
    main()
