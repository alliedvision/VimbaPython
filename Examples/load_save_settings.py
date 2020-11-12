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

import sys
from typing import Optional
from vimba import *


def print_preamble():
    print('////////////////////////////////////////////')
    print('/// Vimba API Load Save Settings Example ///')
    print('////////////////////////////////////////////\n')


def print_usage():
    print('Usage:')
    print('    python load_save_settings.py [camera_id]')
    print('    python load_save_settings.py [/h] [-h]')
    print()
    print('Parameters:')
    print('    camera_id   ID of the camera to use (using first camera if not specified)')
    print()


def abort(reason: str, return_code: int = 1, usage: bool = False):
    print(reason + '\n')

    if usage:
        print_usage()

    sys.exit(return_code)


def parse_args() -> Optional[str]:
    args = sys.argv[1:]
    argc = len(args)

    for arg in args:
        if arg in ('/h', '-h'):
            print_usage()
            sys.exit(0)

    if argc > 1:
        abort(reason="Invalid number of arguments. Abort.", return_code=2, usage=True)

    return None if argc == 0 else args[0]


def get_camera(camera_id: Optional[str]) -> Camera:
    with Vimba.get_instance() as vimba:
        if camera_id:
            try:
                return vimba.get_camera_by_id(camera_id)

            except VimbaCameraError:
                abort('Failed to access Camera \'{}\'. Abort.'.format(camera_id))

        else:
            cams = vimba.get_all_cameras()
            if not cams:
                abort('No Cameras accessible. Abort.')

            return cams[0]


def main():
    print_preamble()
    cam_id = parse_args()

    with Vimba.get_instance():
        print("--> Vimba has been started")

        with get_camera(cam_id) as cam:
            print("--> Camera has been opened (%s)" % cam.get_id())

            # Save camera settings to file.
            settings_file = '{}_settings.xml'.format(cam.get_id())
            cam.save_settings(settings_file, PersistType.All)
            print ("--> Feature values have been saved to '%s'" % settings_file)

            # Restore settings to initial value.
            try:
                cam.UserSetSelector.set('Default')

            except (AttributeError, VimbaFeatureError):
                abort('Failed to set Feature \'UserSetSelector\'')

            try:
                cam.UserSetLoad.run()
                print("--> All feature values have been restored to default")

            except (AttributeError, VimbaFeatureError):
                abort('Failed to run Feature \'UserSetLoad\'')

            # Load camera settings from file.
            cam.load_settings(settings_file, PersistType.All)
            print("--> Feature values have been loaded from given file '%s'" % settings_file)


if __name__ == '__main__':
    main()
