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
    print('//////////////////////////////////////////////////////')
    print('/// Vimba API List Ancillary Data Features Example ///')
    print('//////////////////////////////////////////////////////\n')


def print_usage():
    print('Usage:')
    print('    python list_ancillary_data.py [camera_id]')
    print('    python list_ancillary_data.py [/h] [-h]')
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

    if len(args) > 1:
        abort(reason="Invalid number of arguments. Abort.", return_code=2, usage=True)

    return args[0] if argc == 1 else None


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
            cam.GVSPAdjustPacketSize.run()

            while not cam.GVSPAdjustPacketSize.is_done():
                pass

        except (AttributeError, VimbaFeatureError):
            pass

        # Try to enable ChunkMode
        try:
            cam.ChunkModeActive.set(True)

        except (AttributeError, VimbaFeatureError):
            abort('Failed to enable ChunkMode on Camera \'{}\'. Abort.'.format(cam.get_id()))


def main():
    print_preamble()
    cam_id = parse_args()

    with Vimba.get_instance():
        with get_camera(cam_id) as cam:
            setup_camera(cam)

            # Capture single Frame and print all contained ancillary data
            frame = cam.get_frame()
            anc_data = frame.get_ancillary_data()
            if anc_data:
                with anc_data:
                    print('Print ancillary data contained in Frame:')

                    for feat in anc_data.get_all_features():
                        print('Feature Name   : {}'.format(feat.get_name()))
                        print('Display Name   : {}'.format(feat.get_display_name()))
                        print('Tooltip        : {}'.format(feat.get_tooltip()))
                        print('Description    : {}'.format(feat.get_description()))
                        print('SFNC Namespace : {}'.format(feat.get_sfnc_namespace()))
                        print('Value          : {}'.format(feat.get()))
                        print()

            else:
                abort('Frame {} does not contain AncillaryData. Abort'.format(frame.get_id()))


if __name__ == '__main__':
    main()
