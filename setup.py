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

import setuptools
import os
import re

def read_file(name):
    with open(file=name, mode='r', encoding='utf-8') as file:
        return file.read()


def get_version(file_content):
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format('__version__'),
                       file_content)
    return result.group(1)

name = 'VimbaPython'
version = get_version(read_file(os.path.join('.', 'vimba', '__init__.py')))
author = 'Allied Vision Technologies GmbH'
description = 'Python Bindings for Allied Visions VimbaSDK'
long_description = read_file('README.md')
long_description_type = 'text/markdown'
license = 'BSD-2-Clause'
packages = [
    'vimba',
    'vimba.c_binding',
    'vimba.util'
]
python_requires = '>=3.7'
tests_require = [
    'xmlrunner',
    'flake8',
    'flake8-junit-report',
    'mypy',
    'coverage',
    'docopt'
]
extras_require = {
    'numpy-export': ['numpy'],
    'opencv-export': ['opencv-python'],
    'test': tests_require
}

setuptools.setup(
    name=name,
    version=version,
    author=author,
    description=description,
    long_description=long_description,
    long_description_content_type=long_description_type,
    license=license,
    packages=packages,
    python_requires=python_requires,
    extras_require=extras_require
)
