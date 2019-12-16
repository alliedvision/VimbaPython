Vimba Python API - Beta version for testing purposes only
===============

***Beta version for testing purposes only ***

You are welcome to give feedback on the beta version of our new Vimba Python API!
Please note that the usage of beta software is at your own risk.

In addition to the API's source code, this repository also contains unit tests for VimbaPython.
If you encounter any issues, feel free to run the test script and create an issue on github.com.
This helps us improve the Vimba Python API.

NEW - we have updated VimbaPython with the following improvements:

* Multi-threading example
* Improved usability by raising an exception if a function that is only valid inside a with – statement is called outside with – scope.
* Method get_camera_by_id() supports camera lookup via IP or MAC address for GigE cameras
* Method get_version() outputs the version of VimbaPython, VimbaC, and Vimba Image Transform
* Improved test support for using several different cameras

Before using the updated VimbaPython version, please deinstall VimbaPython:

        python -m pip uninstall VimbaPython

For installing VimbaPython, we recommend using -e with your VimbaPython installation path:

        python -m pip install -e .



Prerequisites
===============
To use this software, you need:

1. Python version 3.7 or higher
2. An Allied Vision camera
3. [VimbaSDK](https://www.alliedvision.com/en/products/software.html) version 3.1. (contains C API version 1.8.1).
If you choose Custom Installation, make sure the Vimba C API, Vimba Image Transform, and the transport layers for your cameras are installed.

Installing Python - Windows
---------------
The following instructions describe how to install and update Python on Windows. If your system requires
multiple, coexisting Python versions, consider using [pyenv-win](https://github.com/pyenv-win/pyenv-win)
to install and maintain multiple Python installations.

1. Download the latest Python release from [python.org](https://www.python.org/downloads/windows/)
2. Execute the downloaded installer and ensure that pip is installed.
3. To verify the installation, open the command prompt and enter:

        python --version
        python -m pip --version

    Please ensure that the Python version is 3.7 or higher and pip uses this Python version.


Installing Python - Linux
---------------
On Linux systems, the Python installation process depends heavily on the distribution. If python3.7
is not available for your distribution or your system requires multiple python versions
to coexist, use [pyenv](https://realpython.com/intro-to-pyenv/) instead.

1. Install or update python3.7 with the packet manager of your distribution.
2. Install or update pip with the packet manager of your distribution.
3. To verify the installation, open a console and enter:

        python --version
        python -m pip --version


Installing the Vimba Python API
===============
All operating systems:

1. Download the latest version of [VimbaPython](https://github.com/alliedvision/VimbaPython).
2. Open a terminal and navigate to the download location of VimbaPython (contains setup.py)

Basic Installation
---------------
Execute the following command:

        python -m pip install .


Installation with optional NumPy and OpenCV export
---------------
Execute the following command:

        python -m pip install .[numpy-export,opencv-export]

ARM users only: If installation of "opencv-export" fails, pip is not able to install
"opencv-python" for ARM boards. This is a known issue on ARM boards.
If you are affected by this, install VimbaPython without optional dependencies and try to install
OpenCV in a different way (for example, with your operating system's packet manager). The OpenCV installation
can be verified by running the example "Examples/asychronous_grab_opencv.py".

Installation with optional test support
---------------
Execute the following command:

        python -m pip install .[test]

Running the examples
===============
After installing VimbaPython, all examples can be directly executed. The
following example prints a list of all connected cameras:

        python Examples/list_cameras.py

Running tests
===============
VimbaPython's tests are divided into unit tests and multiple static test tools.
These tests are configured and executed by the script 'run_tests.py' in the VimbaPython root
directory.

The unit tests are divided into three test suites:
1. The test suite 'basic' does not require a connected camera. It can be run on any system.
2. The test suite 'real_cam' contains tests that require a connected camera.
   To execute these tests, specify a camera ID. You can use the list_cameras example or Vimba Viewer to obtain
   the Camera ID of any connected Allied Vision camera.
3. The testsuite 'all' contains all tests from 'basic' and 'real_cam'. Since 'real_cam' is used,
   a camera ID must be specified.

The test results are either printed to the command line or can be exported in junit format.
If the test results are exported in junit format, the results are stored in 'Test_Reports'
after test execution. The following examples show how to run all possible test configurations.

Running test suite 'basic' with console output:

        python run_tests.py test -s basic

Running test suite 'basic' with junit export:

        python run_tests.py test_junit -s basic

Running test suite 'real_cam' with console output:

        python run_tests.py test -s real_cam -c <CAMERA_ID>

Running test suite 'real_cam' with junit export:

        python run_tests.py test_junit -s real_cam -c <CAMERA_ID>

Running test suite 'all' with console output:

        python run_tests.py test -s all -c <CAMERA_ID>

Running test suite 'all' with junit export:

        python run_tests.py test_junit -s all -c <CAMERA_ID>
