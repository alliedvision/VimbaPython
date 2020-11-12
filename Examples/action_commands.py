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
from typing import Tuple
from vimba import *


def print_preamble():
    print('/////////////////////////////////////////')
    print('/// Vimba API Action Commands Example ///')
    print('/////////////////////////////////////////\n')


def print_usage():
    print('Usage:')
    print('    python action_commands.py <camera_id> <interface_id>')
    print('    python action_commands.py [/h] [-h]')
    print()
    print('Parameters:')
    print('    camera_id      ID of the camera to be used')
    print('    interface_id   ID of network interface to send out Action Command')
    print('                   \'ALL\' enables broadcast on all interfaces')
    print()


def abort(reason: str, return_code: int = 1, usage: bool = False):
    print(reason + '\n')

    if usage:
        print_usage()

    sys.exit(return_code)


def parse_args() -> Tuple[str, str]:
    args = sys.argv[1:]

    for arg in args:
        if arg in ('/h', '-h'):
            print_usage()
            sys.exit(0)

    if len(args) != 2:
        abort(reason="Invalid number of arguments. Abort.", return_code=2, usage=True)

    return (args[0], args[1])


def get_input() -> str:
    prompt = 'Press \'a\' to send action command. Press \'q\' to stop example. Enter:'
    print(prompt, flush=True)
    return input()


def get_camera(camera_id: str) -> Camera:
    with Vimba.get_instance() as vimba:
        try:
            return vimba.get_camera_by_id(camera_id)

        except VimbaCameraError:
            abort('Failed to access Camera {}. Abort.'.format(camera_id))


def get_command_sender(interface_id):
    # If given interface_id is ALL, ActionCommand shall be sent from all Ethernet Interfaces.
    # This is achieved by run ActionCommand on the Vimba instance.
    if interface_id == 'ALL':
        return Vimba.get_instance()

    with Vimba.get_instance() as vimba:
        # A specific Interface was given. Lookup via given Interface id and verify that
        # it is an Ethernet Interface. Running ActionCommand will be only send from this Interface.
        try:
            inter = vimba.get_interface_by_id(interface_id)

        except VimbaInterfaceError:
            abort('Failed to access Interface {}. Abort.'.format(interface_id))

        if inter.get_type() != InterfaceType.Ethernet:
            abort('Given Interface {} is no Ethernet Interface. Abort.'.format(interface_id))

    return inter


def frame_handler(cam: Camera, frame: Frame):
    if frame.get_status() == FrameStatus.Complete:
        print('Frame(ID: {}) has been received.'.format(frame.get_id()), flush=True)

    cam.queue_frame(frame)


def main():
    print_preamble()
    camera_id, interface_id = parse_args()

    with Vimba.get_instance():
        cam = get_camera(camera_id)
        sender = get_command_sender(interface_id)

        with cam, sender:
            # Prepare Camera for ActionCommand - Trigger
            device_key = 1
            group_key = 1
            group_mask = 1

            cam.GVSPAdjustPacketSize.run()
            while not cam.GVSPAdjustPacketSize.is_done():
                pass

            cam.TriggerSelector.set('FrameStart')
            cam.TriggerSource.set('Action0')
            cam.TriggerMode.set('On')
            cam.ActionDeviceKey.set(device_key)
            cam.ActionGroupKey.set(group_key)
            cam.ActionGroupMask.set(group_mask)

            # Enter Streaming mode and wait for user input.
            try:
                cam.start_streaming(frame_handler)

                while True:
                    ch = get_input()

                    if ch == 'q':
                        break

                    elif ch == 'a':
                        sender.ActionDeviceKey.set(device_key)
                        sender.ActionGroupKey.set(group_key)
                        sender.ActionGroupMask.set(group_mask)
                        sender.ActionCommand.run()

            finally:
                cam.stop_streaming()


if __name__ == '__main__':
    main()
