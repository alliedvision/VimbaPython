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
    print('////////////////////////////////////////')
    print('/// Vimba API Event Handling Example ///')
    print('////////////////////////////////////////\n')


def print_usage():
    print('Usage:')
    print('    python event_handling.py [camera_id]')
    print('    python event_handling.py [/h] [-h]')
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

    return args[0] if argc == 1 else None


def get_camera(cam_id: Optional[str]):
    with Vimba.get_instance() as vimba:
        # Lookup Camera if it was specified.
        if cam_id:
            try:
                cam = vimba.get_camera_by_id(cam_id)

            except VimbaCameraError:
                abort('Failed to access Camera {}. Abort.'.format(cam_id))

        # If no camera was specified, use first detected camera.
        else:
            cams = vimba.get_all_cameras()
            if not cams:
                abort('No Camera detected. Abort.')

            cam = cams[0]

        # This example works only with GigE Cameras. Verify that Camera is connected to an
        # Ethernet Interface.
        inter = vimba.get_interface_by_id(cam.get_interface_id())

        if inter.get_type() != InterfaceType.Ethernet:
            abort('Example supports only GigE Cameras. Abort.')

        return cam


def setup_camera(cam: Camera):
    with cam:
        # Try to adjust GeV packet size. This Feature is only available for GigE - Cameras.
        try:
            cam.GVSPAdjustPacketSize.run()

            while not cam.GVSPAdjustPacketSize.is_done():
                pass

        except (AttributeError, VimbaFeatureError):
            pass


def feature_changed_handler(feature):
    msg = 'Feature \'{}\' changed value to \'{}\''
    print(msg.format(str(feature.get_name()), str(feature.get())), flush=True)


def main():
    print_preamble()
    cam_id = parse_args()

    with Vimba.get_instance():
        with get_camera(cam_id) as cam:
            setup_camera(cam)

            # Disable all events notifications
            for event in cam.EventSelector.get_available_entries():
                cam.EventSelector.set(event)
                cam.EventNotification.set('Off')

            # Enable event notifications on 'AcquisitionStart'
            cam.EventSelector.set('AcquisitionStart')
            cam.EventNotification.set('On')

            # Register callable on all Features in the '/EventControl/EventData' - Category
            feats = cam.get_features_by_category('/EventControl/EventData')

            for feat in feats:
                feat.register_change_handler(feature_changed_handler)

            # Acquire a single Frame to trigger events.
            cam.get_frame()


if __name__ == '__main__':
    main()
