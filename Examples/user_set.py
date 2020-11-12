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
from typing import Optional, Dict, Any
from vimba import *


def print_preamble():
    print('//////////////////////////////////')
    print('/// Vimba API User Set Example ///')
    print('//////////////////////////////////\n')


def print_usage():
    print('Usage:')
    print('    python user_set.py [camera_id] [/i:Index] [/{h|s|l|i|m|d|or|os|n}]')
    print()
    print('Parameters:')
    print('    camera_id   ID of the camera to use (using first camera if not specified)')
    print('    /i:index    User set index')
    print('    /h          Print help')
    print('    /s          Save user set to flash')
    print('    /l          Load user set from flash (default if not specified)')
    print('    /i          Get selected user set index')
    print('    /m          Make user set default')
    print('    /d          Is user set default')
    print('    /or         Get user set operation default.')
    print('    /os         Get user set operation status.')
    print('    /n          Get user set count')
    print()
    print('Examples:')
    print('     To load user set 0 (factory set) from flash in order to activate it call:')
    print('     UserSet /i:0 /l')
    print()
    print('     To save the current settings to user set 1 call:')
    print('     UserSet /i:1 /s')
    print()


def abort(reason: str, return_code: int = 1, usage: bool = False):
    print(reason + '\n')

    if usage:
        print_usage()

    sys.exit(return_code)


def parse_args() -> Dict[str, Any]:
    args = sys.argv[1:]
    argc = len(args)

    result: Dict[str, Any] = {}

    if (argc <= 0) or (4 <= argc):
        abort(reason="Invalid number of arguments. Abort.", return_code=2, usage=True)

    for arg in args:
        if arg in ('/h'):
            print_usage()
            sys.exit(0)

        # Examine command parameters
        if arg in ('/s', '/l', '/i', '/m', '/d', '/or', '/os', '/n'):
            if result.get('mode') is None:
                result['mode'] = arg

            else:
                abort(reason="Multiple Commands specified. Abort.", return_code=2, usage=True)

        # Examine specified index
        elif arg.startswith('/i:'):
            _, set_id = arg.split(':')

            if not set_id:
                abort(reason="No index specified after /i:. Abort.", return_code=2, usage=True)

            try:
                set_id_int = int(set_id)

            except ValueError:
                abort(reason="Number in /i:<no> is no Integer. Abort.", return_code=2, usage=True)

            if set_id_int < 0:
                abort(reason="Number in /i:<no> is negative. Abort.", return_code=2, usage=True)

            if result.get('set_id') is not None:
                abort(reason="Multiple /i:<no> specified. Abort.", return_code=2, usage=True)

            result['set_id'] = set_id_int

        # Examine camera id
        elif result.get('camera_id') is None:
            result['camera_id'] = arg

        else:
            abort(reason="Invalid arguments. Abort.", return_code=2, usage=True)

    # Apply defaults
    if not result.get('mode'):
        result['mode'] = '/l'

    return result


def get_camera(cam_id: Optional[str]):
    with Vimba.get_instance() as vimba:
        # Lookup Camera if it was specified.
        if cam_id:
            try:
                return vimba.get_camera_by_id(cam_id)

            except VimbaCameraError:
                abort('Failed to access Camera {}. Abort.'.format(cam_id))

        # If no camera was specified, use first detected camera.
        else:
            cams = vimba.get_all_cameras()
            if not cams:
                abort('No Camera detected. Abort.')

            return cams[0]


def select_user_set(camera: Camera, set_id: int):
    try:
        camera.get_feature_by_name('UserSetSelector').set(set_id)

    except VimbaFeatureError:
        abort('Failed to select user set with \'{}\'. Abort.'.format(set_id))


def load_from_flash(cam: Camera, set_id: int):
    with cam:
        print('Loading user set \'{}\' from flash.'.format(set_id))

        select_user_set(cam, set_id)

        try:
            cmd = cam.get_feature_by_name('UserSetLoad')
            cmd.run()

            while not cmd.is_done():
                pass

        except VimbaFeatureError:
            abort('Failed to load user set \'{}\' from flash. Abort.'.format(set_id))

        print('Loaded user set \'{}\' loaded from flash successfully.'.format(set_id))


def save_to_flash(cam: Camera, set_id: int):
    with cam:
        print('Saving user set \'{}\' to flash.'.format(set_id))

        select_user_set(cam, set_id)

        try:
            cmd = cam.get_feature_by_name('UserSetSave')
            cmd.run()

            while not cmd.is_done():
                pass

        except VimbaFeatureError:
            abort('Failed to save user set \'{}\' to flash. Abort.'.format(set_id))

        print('Saved user set \'{}\' to flash.'.format(set_id))


def get_active_user_set(cam: Camera, _: int):
    with cam:
        print('Get selected user set id.')

        try:
            value = cam.get_feature_by_name('UserSetSelector').get()

        except VimbaFeatureError:
            abort('Failed to get user set id. Abort.')

        print('The selected user set id is \'{}\'.'.format(int(value)))


def get_number_of_user_sets(cam: Camera, _: int):
    with cam:
        print('Get total number of user sets.')

        try:
            feat = cam.get_feature_by_name('UserSetSelector')
            value = len(feat.get_available_entries())

        except VimbaFeatureError:
            abort('Failed to get total number of user sets. Abort.')

        print('The total number of user sets is \'{}\''.format(value))


def set_default_user_set(cam: Camera, set_id: int):
    with cam:
        print('Set user set \'{}\' as default.'.format(set_id))

        # Try to set mode via UserSetDefaultSelector feature
        try:
            feat = cam.get_feature_by_name('UserSetDefaultSelector')

            try:
                feat.set(set_id)

            except VimbaFeatureError:
                abort('Failed to set user set id \'{}\' as default user set'.format(set_id))

        except VimbaFeatureError:
            # Try to set mode via UserSetMakeDefault command
            select_user_set(cam, set_id)

            try:
                cmd = cam.get_feature_by_name('UserSetMakeDefault')
                cmd.run()

                while not cmd.is_done():
                    pass

            except VimbaFeatureError:
                abort('Failed to set user set id \'{}\' as default user set'.format(set_id))

        print('User set \'{}\' is the new default user set.'.format(set_id))


def is_default_user_set(cam: Camera, set_id: int):
    with cam:
        print('Is user set \'{}\' the default user set?'.format(set_id))

        try:
            default_id = int(cam.get_feature_by_name('UserSetDefaultSelector').get())

        except VimbaFeatureError:
            abort('Failed to get default user set id. Abort.')

        msg = 'User set \'{}\' {} the default user set.'
        print(msg.format(set_id, 'is' if set_id == default_id else 'is not'))


def get_operation_result(cam: Camera, set_id: int):
    with cam:
        print('Get user set operation result.')

        try:
            result = cam.get_feature_by_name('UserSetOperationResult').get()

        except VimbaFeatureError:
            abort('Failed to get user set operation result. Abort.')

        print('Operation result was {}.'.format(result))


def get_operation_status(cam: Camera, set_id: int):
    with cam:
        print('Get user set operation status.')

        try:
            result = cam.get_feature_by_name('UserSetOperationStatus').get()

        except VimbaFeatureError:
            abort('Failed to get user set operation status. Abort.')

        print('Operation status was {}.'.format(result))


def main():
    print_preamble()
    args = parse_args()

    with Vimba.get_instance():
        cam = get_camera(args.get('camera_id'))
        print('Using Camera with ID \'{}\''.format(cam.get_id()))

        with cam:
            mode = args['mode']

            try:
                set_id = args.get('set_id', int(cam.get_feature_by_name('UserSetSelector').get()))

            except VimbaFeatureError:
                abort('Failed to get id of current user set. Abort.')

            # Mode -> Function Object mapping
            mode_to_fn = {
                '/l': load_from_flash,
                '/s': save_to_flash,
                '/i': get_active_user_set,
                '/n': get_number_of_user_sets,
                '/m': set_default_user_set,
                '/d': is_default_user_set,
                '/or': get_operation_result,
                '/os': get_operation_status
            }

            fn = mode_to_fn[mode]
            fn(cam, set_id)


if __name__ == '__main__':
    main()
