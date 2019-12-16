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

import sys
from typing import Optional
from vimba import *


def print_preamble():
    print('//////////////////////////////////////////')
    print('/// Vimba API Synchronous Grab Example ///')
    print('//////////////////////////////////////////\n')


def print_usage():
    print('Usage:')
    print('    python synchronous_grab.py [camera_id]')
    print('    python synchronous_grab.py [/h] [-h]')
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


def setup_camera(cam: Camera):
    with cam:
        # Try to adjust GeV packet size. This Feature is only available for GigE - Cameras.
        try:
            cmd_feat = cam.get_feature_by_name('GVSPAdjustPacketSize')

            try:
                cmd_feat.run()

                while not cmd_feat.is_done():
                    pass

            except VimbaFeatureError:
                abort('Failed to set Feature \'GVSPAdjustPacketSize\'. Abort.')

        except VimbaFeatureError:
            pass


def main():
    print_preamble()
    cam_id = parse_args()

    with Vimba.get_instance():
        with get_camera(cam_id) as cam:
            setup_camera(cam)

            # Acquire 10 frame with a custom timeout (default is 2000ms) per frame acquisition.
            for frame in cam.get_frame_iter(limit=10, timeout_ms=3000):
                print('Got {}'.format(frame))


if __name__ == '__main__':
    main()
