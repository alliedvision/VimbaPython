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

from functools import reduce, wraps
from inspect import signature
from .log import Log


__all__ = [
    'TraceEnable'
]


_FMT_MSG_ENTRY: str = 'Enter | {}'
_FMT_MSG_LEAVE: str = 'Leave | {}'
_FMT_MSG_RAISE: str = 'Raise | {}, {}'
_FMT_ERROR: str = 'ErrorType: {}, ErrorValue: {}'
_INDENT_PER_LEVEL: str = '  '


def _args_to_str(func, *args, **kwargs) -> str:
    # Expand function signature
    sig = signature(func).bind(*args, **kwargs)
    sig.apply_defaults()
    full_args = sig.arguments

    # Early return if there is nothing to print
    if not full_args:
        return '(None)'

    def fold(args_as_str: str, arg):
        name, value = arg

        if name == 'self':
            arg_str = 'self'

        else:
            arg_str = str(value)

        return '{}{}, '.format(args_as_str, arg_str)

    return '({})'.format(reduce(fold, full_args.items(), '')[:-2])


def _get_indent(level: int) -> str:
    return _INDENT_PER_LEVEL * level


def _create_enter_msg(name: str, level: int, args_str: str) -> str:
    msg = '{}{}{}'.format(_get_indent(level), name, args_str)
    return _FMT_MSG_ENTRY.format(msg)


def _create_leave_msg(name: str, level: int, ) -> str:
    msg = '{}{}'.format(_get_indent(level), name)
    return _FMT_MSG_LEAVE.format(msg)


def _create_raise_msg(name: str, level: int,  exc_type: Exception, exc_value: str) -> str:
    msg = '{}{}'.format(_get_indent(level), name)
    exc = _FMT_ERROR.format(exc_type, exc_value)
    return _FMT_MSG_RAISE.format(msg, exc)


class _Tracer:
    __log = Log.get_instance()
    __level: int = 0

    @staticmethod
    def is_log_enabled() -> bool:
        return bool(_Tracer.__log)

    def __init__(self, func, *args, **kwargs):
        self.__full_name: str = '{}.{}'.format(func.__module__, func.__qualname__)
        self.__full_args: str = _args_to_str(func, *args, **kwargs)

    def __enter__(self):
        msg = _create_enter_msg(self.__full_name, _Tracer.__level, self.__full_args)

        _Tracer.__log.trace(msg)
        _Tracer.__level += 1

    def __exit__(self, exc_type, exc_value, exc_traceback):
        _Tracer.__level -= 1

        if exc_type:
            msg = _create_raise_msg(self.__full_name, _Tracer.__level, exc_type, exc_value)

        else:
            msg = _create_leave_msg(self.__full_name, _Tracer.__level)

        _Tracer.__log.trace(msg)


class TraceEnable:
    """Decorator: Adds an entry of LogLevel. Trace on entry and exit of the wrapped function.
    On exit, the log entry contains information if the function was left normally or with an
    exception.
    """
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if _Tracer.is_log_enabled():
                with _Tracer(func, *args, **kwargs):
                    result = func(*args, **kwargs)

                return result

            else:
                return func(*args, **kwargs)

        return wrapper
