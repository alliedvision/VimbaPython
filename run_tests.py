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

import os
import shutil
import subprocess
import docopt


def fprint(line):
    print(line, flush=True)


def stringify_list(l):
    list_str = ''
    for e in l:
        list_str += e + ' '

    return list_str


def static_test():
    fprint('Execute Static Test: flake8')
    subprocess.run('flake8 vimba', shell=True)
    subprocess.run('flake8 Examples --ignore=F405,F403', shell=True)
    subprocess.run('flake8 Tests --ignore=F405,F403', shell=True)
    fprint('')

    fprint('Execute Static Test: mypy')
    subprocess.run('mypy vimba', shell=True)
    fprint('')


def unit_test(testsuite, testcamera, blacklist):
    blacklist = " ".join(blacklist)

    fprint('Execute Unit tests and measure coverage:')
    if testsuite == 'basic':
        cmd = 'coverage run Tests/runner.py -s basic -o console {}'.format(blacklist)

    else:
        cmd = 'coverage run Tests/runner.py -s {} -c {} -o console {}'
        cmd = cmd.format(testsuite, testcamera, blacklist)

    subprocess.run(cmd, shell=True)
    fprint('')

    fprint('Coverage during test execution:')
    subprocess.run('coverage report -m', shell=True)
    fprint('')

    coverage_file = '.coverage'
    if os.path.exists(coverage_file):
        os.remove(coverage_file)


def setup_junit(report_dir):
    if os.path.exists(report_dir):
        shutil.rmtree(report_dir, ignore_errors=True)

    os.mkdir(report_dir)


def static_test_junit(report_dir):
    fprint('Execute Static Test: flake8')
    cmd = 'flake8 vimba --output-file=' + report_dir + '/flake8.txt'
    subprocess.run(cmd, shell=True)

    cmd = 'flake8_junit ' + report_dir + '/flake8.txt ' + report_dir + '/flake8_junit.xml'
    subprocess.run(cmd, shell=True)
    fprint('')

    fprint('Execute Static Test: mypy')
    cmd = 'mypy vimba --junit-xml ' + report_dir + '/mypy_junit.xml'
    subprocess.run(cmd, shell=True)
    fprint('')


def unit_test_junit(report_dir, testsuite, testcamera, blacklist):
    fprint('Execute Unit tests and measure coverage:')

    blacklist = " ".join(blacklist)
    if testsuite == 'basic':
        cmd = 'coverage run --branch Tests/runner.py -s basic -o junit_xml {} {}'
        cmd = cmd.format(report_dir, blacklist)

    else:
        cmd = 'coverage run --branch Tests/runner.py -s {} -c {} -o junit_xml {} {}'
        cmd = cmd.format(testsuite, testcamera, report_dir, blacklist)

    subprocess.run(cmd, shell=True)
    fprint('')

    fprint('Generate Coverage reports:')
    subprocess.run('coverage report -m', shell=True)
    subprocess.run('coverage xml -o ' + report_dir + '/coverage.xml', shell=True)
    fprint('')

    coverage_file = '.coverage'
    if os.path.exists(coverage_file):
        os.remove(coverage_file)


def test(testsuite, testcamera, blacklist):
    static_test()
    unit_test(testsuite, testcamera, blacklist)


def test_junit(report_dir, testsuite, testcamera, blacklist):
    setup_junit(report_dir)
    static_test_junit(report_dir)
    unit_test_junit(report_dir, testsuite, testcamera, blacklist)


def main():
    CLI = """VimbaPython tests script.
    Usage:
        run_tests.py -h
        run_tests.py test -s basic [BLACKLIST...]
        run_tests.py test -s (real_cam | all) -c CAMERA_ID [BLACKLIST...]
        run_tests.py test_junit -s basic [BLACKLIST...]
        run_tests.py test_junit -s (real_cam | all) -c CAMERA_ID [BLACKLIST...]

    Arguments:
        CAMERA_ID    Camera Id from Camera that shall be used during testing
        BLACKLIST    Optional sequence of unittest functions to skip.

    Options:
        -h   Show this screen.
        -s   Unittestsuite. Can be 'basic', 'real_cam' or 'all'. The last two require a
             Camera Id to test against.
        -c   Camera Id used in testing.
    """

    args = docopt.docopt(CLI)

    suite = 'basic' if args['basic'] else 'real_cam' if args['real_cam'] else 'all'

    if args['test']:
        test(suite, args['CAMERA_ID'], args['BLACKLIST'])

    elif args['test_junit']:
        report_dir = 'Test_Reports'
        test_junit(report_dir, suite, args['CAMERA_ID'], args['BLACKLIST'])


if __name__ == '__main__':
    main()
