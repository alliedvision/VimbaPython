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

from functools import wraps
from typing import Any, Callable, Tuple, Optional
from .log import LogConfig, Log


__all__ = [
    'ScopedLogEnable'
]


class _ScopedLog:
    __log = Log.get_instance()

    def __init__(self, config: LogConfig):
        self.__config: LogConfig = config
        self.__old_config: Optional[LogConfig] = None

    def __enter__(self):
        self.__old_config = _ScopedLog.__log.get_config()
        _ScopedLog.__log.enable(self.__config)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.__old_config:
            _ScopedLog.__log.enable(self.__old_config)

        else:
            _ScopedLog.__log.disable()


class ScopedLogEnable:
    """Decorator: Enables logging facility before execution of the wrapped function
    and disables logging after exiting the wrapped function. This allows more specific
    logging of a code section compared to enabling or disabling the global logging mechanism.

    Arguments:
        config: The configuration the log should be enabled with.
    """
    def __init__(self, config: LogConfig):
        """Add scoped logging to a Callable.

        Arguments:
            config: The configuration the log should be enabled with.
        """
        self.__config = config

    def __call__(self, func: Callable[..., Any]):
        @wraps(func)
        def wrapper(*args: Tuple[Any, ...]):
            with _ScopedLog(self.__config):
                return func(*args)

        return wrapper
