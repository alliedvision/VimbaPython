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

import collections

from inspect import isfunction, ismethod, signature
from functools import wraps
from typing import get_type_hints, Union
from .log import Log


__all__ = [
    'RuntimeTypeCheckEnable'
]


class RuntimeTypeCheckEnable:
    """Decorator adding runtime type checking to the wrapped callable.

    Each time the callable is executed, all arguments are checked if they match with the given
    type hints. If all checks are passed, the wrapped function is executed, if the given
    arguments to not match a TypeError is raised.
    Note: This decorator is no replacement for a feature complete TypeChecker. It supports only
    a subset of all types expressible by type hints.
    """
    _log = Log.get_instance()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            full_args, hints = self.__dismantle_sig(func, *args, **kwargs)

            for arg_name in hints:
                self.__verify_arg(func, hints[arg_name], (arg_name, full_args[arg_name]))

            return func(*args, **kwargs)

        return wrapper

    def __dismantle_sig(self, func, *args, **kwargs):
        # Get merge args, kwargs and defaults to complete argument list.
        full_args = signature(func).bind(*args, **kwargs)
        full_args.apply_defaults()

        # Get available type hints, remove return value.
        hints = get_type_hints(func)
        hints.pop('return', None)

        return (full_args.arguments, hints)

    def __verify_arg(self, func, type_hint, arg_spec):
        arg_name, arg = arg_spec

        if (self.__matches(type_hint, arg)):
            return

        msg = '\'{}\' called with unexpected argument type. Argument\'{}\'. Expected type: {}.'
        msg = msg.format(func.__qualname__, arg_name, type_hint)

        RuntimeTypeCheckEnable._log.error(msg)
        raise TypeError(msg)

    def __matches(self, type_hint, arg) -> bool:
        if self.__matches_base_types(type_hint, arg):
            return True

        elif self.__matches_type_types(type_hint, arg):
            return True

        elif self.__matches_union_types(type_hint, arg):
            return True

        elif self.__matches_tuple_types(type_hint, arg):
            return True

        elif self.__matches_dict_types(type_hint, arg):
            return True

        else:
            return self.__matches_callable(type_hint, arg)

    def __matches_base_types(self, type_hint, arg) -> bool:
        return type_hint == type(arg)

    def __matches_type_types(self, type_hint, arg) -> bool:
        try:
            if not type_hint.__origin__ == type:
                return False

            hint_args = type_hint.__args__

        except AttributeError:
            return False

        return arg in hint_args

    def __matches_union_types(self, type_hint, arg) -> bool:
        try:
            if not type_hint.__origin__ == Union:
                return False

        except AttributeError:
            return False

        # If Matches if true for an Union hint:
        for hint in type_hint.__args__:
            if self.__matches(hint, arg):
                return True

        return False

    def __matches_tuple_types(self, type_hint, arg) -> bool:
        try:
            if not (type_hint.__origin__ == tuple and type(arg) == tuple):
                return False

        except AttributeError:
            return False

        if arg == ():
            return True

        if Ellipsis in type_hint.__args__:
            fn = self.__matches_var_length_tuple

        else:
            fn = self.__matches_fixed_size_tuple

        return fn(type_hint, arg)

    def __matches_fixed_size_tuple(self, type_hint, arg) -> bool:
        # To pass, the entire tuple must match in length and all types
        expand_hint = type_hint.__args__

        if len(expand_hint) != len(arg):
            return False

        for hint, value in zip(expand_hint, arg):
            if not self.__matches(hint, value):
                return False

        return True

    def __matches_var_length_tuple(self, type_hint, arg) -> bool:
        # To pass a tuple can be empty or all contents must match the given type.
        hint, _ = type_hint.__args__

        for value in arg:
            if not self.__matches(hint, value):
                return False

        return True

    def __matches_dict_types(self, type_hint, arg) -> bool:
        # To pass the hint must be a Dictionary and arg must match the given types.
        try:
            if not (type_hint.__origin__ == dict and type(arg) == dict):
                return False

        except AttributeError:
            return False

        key_type, val_type = type_hint.__args__

        for k, v in arg.items():
            if type(k) != key_type or type(v) != val_type:
                return False

        return True

    def __matches_callable(self, type_hint, arg) -> bool:
        # Return if the given hint is no callable
        try:
            if not type_hint.__origin__ == collections.abc.Callable:
                return False

        except AttributeError:
            return False

        # Verify that are is some form of callable.:
        # 1) Check if it is either a function or a method
        # 2) If it is an object, check if it has a __call__ method. If so use call for checks.
        if not (isfunction(arg) or ismethod(arg)):

            try:
                arg = getattr(arg, '__call__')

            except AttributeError:
                return False

        # Examine signature of given callable
        sig_args = signature(arg).parameters
        hint_args = type_hint.__args__

        # Verify Parameter list length
        if len(sig_args) != len(hint_args[:-1]):
            return False

        return True
