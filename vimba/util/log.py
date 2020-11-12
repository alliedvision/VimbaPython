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

import os
import enum
import datetime
import logging

from typing import List, Optional


__all__ = [
    'LogLevel',
    'LogConfig',
    'Log',
    'LOG_CONFIG_TRACE_CONSOLE_ONLY',
    'LOG_CONFIG_TRACE_FILE_ONLY',
    'LOG_CONFIG_TRACE',
    'LOG_CONFIG_INFO_CONSOLE_ONLY',
    'LOG_CONFIG_INFO_FILE_ONLY',
    'LOG_CONFIG_INFO',
    'LOG_CONFIG_WARNING_CONSOLE_ONLY',
    'LOG_CONFIG_WARNING_FILE_ONLY',
    'LOG_CONFIG_WARNING',
    'LOG_CONFIG_ERROR_CONSOLE_ONLY',
    'LOG_CONFIG_ERROR_FILE_ONLY',
    'LOG_CONFIG_ERROR',
    'LOG_CONFIG_CRITICAL_CONSOLE_ONLY',
    'LOG_CONFIG_CRITICAL_FILE_ONLY',
    'LOG_CONFIG_CRITICAL'
]


class LogLevel(enum.IntEnum):
    """Enum containing all LogLevels.

    Enum values are:
        Trace    - Show Tracing information. Show all messages.
        Info     - Show Informational, Warning, Error, and Critical Events.
        Warning  - Show Warning, Error, and Critical Events.
        Error    - Show Errors and Critical Events.
        Critical - Show Critical Events only.
    """
    Trace = logging.DEBUG
    Info = logging.INFO
    Warning = logging.WARNING
    Error = logging.ERROR
    Critical = logging.CRITICAL

    def __str__(self):
        return self._name_

    def as_equal_len_str(self) -> str:
        return _LEVEL_TO_EQUAL_LEN_STR[self]


_LEVEL_TO_EQUAL_LEN_STR = {
    LogLevel.Trace: 'Trace   ',
    LogLevel.Info: 'Info    ',
    LogLevel.Warning: 'Warning ',
    LogLevel.Error: 'Error   ',
    LogLevel.Critical: 'Critical'
}


class LogConfig:
    """The LogConfig is a builder to configure various specialized logging configurations.
    The constructed LogConfig must set via vimba.Vimba or the ScopedLogEnable Decorator
    to start logging.
    """

    __ENTRY_FORMAT = logging.Formatter('%(asctime)s | %(message)s')

    def __init__(self):
        self.__handlers: List[logging.Handler] = []
        self.__max_msg_length: Optional[int] = None

    def add_file_log(self, level: LogLevel) -> 'LogConfig':
        """Add a new Log file to the Config Builder.

        Arguments:
            level: LogLevel of the added log file.

        Returns:
            Reference to the LogConfig instance (builder pattern).
        """
        log_ts = datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
        log_file = 'VimbaPython_{}_{}.log'.format(log_ts, str(level))
        log_file = os.path.join(os.getcwd(), log_file)

        handler = logging.FileHandler(log_file, delay=True)
        handler.setLevel(level)
        handler.setFormatter(LogConfig.__ENTRY_FORMAT)

        self.__handlers.append(handler)
        return self

    def add_console_log(self, level: LogLevel) -> 'LogConfig':
        """Add a new Console Log to the Config Builder.

        Arguments:
            level: LogLevel of the added console log file.

        Returns:
            Reference to the LogConfig instance (builder pattern).
        """
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(LogConfig.__ENTRY_FORMAT)

        self.__handlers.append(handler)
        return self

    def set_max_msg_length(self, max_msg_length: int):
        """Set max length of a log entry. Messages longer than this entry will be cut off."""
        self.__max_msg_length = max_msg_length

    def get_max_msg_length(self) -> Optional[int]:
        """Get configured max message length"""
        return self.__max_msg_length

    def get_handlers(self) -> List[logging.Handler]:
        """Get all configured log handlers"""
        return self.__handlers


class Log:
    class __Impl:
        """This class is wraps the logging Facility. Since this is as Singleton
        Use Log.get_instace(), to access the log.
        """
        def __init__(self):
            """Do not call directly. Use Log.get_instance() instead."""
            self.__logger: Optional[logging.Logger] = None
            self.__config: Optional[LogConfig] = None
            self._test_buffer: Optional[List[str]] = None

        def __bool__(self):
            return bool(self.__logger)

        def enable(self, config: LogConfig):
            """Enable global VimbaPython logging mechanism.

            Arguments:
                config: The configuration to apply.
            """
            self.disable()

            logger = logging.getLogger('VimbaPythonLog')
            logger.setLevel(logging.DEBUG)

            for handler in config.get_handlers():
                logger.addHandler(handler)

            self.__config = config
            self.__logger = logger

        def disable(self):
            """Disable global VimbaPython logging mechanism."""
            if self.__logger and self.__config:
                for handler in self.__config.get_handlers():
                    handler.close()
                    self.__logger.removeHandler(handler)

                self.__logger = None
                self.__config = None

        def get_config(self) -> Optional[LogConfig]:
            """ Get log configuration

            Returns:
                Configuration if the log is enabled. In case the log is disabled return None.
            """
            return self.__config

        def trace(self, msg: str):
            """Add an entry of LogLevel.Trace to the log. Does nothing is the log is disabled.

            Arguments:
                msg - The message that should be added to the Log.
            """
            if self.__logger:
                self.__logger.debug(self.__build_msg(LogLevel.Trace, msg))

        def info(self, msg: str):
            """Add an entry of LogLevel.Info to the log. Does nothing is the log is disabled.

            Arguments:
                msg - The message that should be added to the Log.
            """
            if self.__logger:
                self.__logger.info(self.__build_msg(LogLevel.Info, msg))

        def warning(self, msg: str):
            """Add an entry of LogLevel.Warning to the log. Does nothing is the log is disabled.

            Arguments:
                msg - The message that should be added to the Log.
            """
            if self.__logger:
                self.__logger.warning(self.__build_msg(LogLevel.Warning, msg))

        def error(self, msg: str):
            """Add an entry of LogLevel.Error to the log. Does nothing is the log is disabled.

            Arguments:
                msg - The message that should be added to the Log.
            """
            if self.__logger:
                self.__logger.error(self.__build_msg(LogLevel.Error, msg))

        def critical(self, msg: str):
            """Add an entry of LogLevel.Critical to the log. Does nothing is the log is disabled.

            Arguments:
                msg - The message that should be added to the Log.
            """
            if self.__logger:
                self.__logger.critical(self.__build_msg(LogLevel.Critical, msg))

        def __build_msg(self, loglevel: LogLevel, msg: str) -> str:
            msg = '{} | {}'.format(loglevel.as_equal_len_str(), msg)
            max_len = self.__config.get_max_msg_length() if self.__config else None

            if max_len and (max_len < len(msg)):
                suffix = ' ...'
                msg = msg[:max_len - len(suffix)] + suffix

            if self._test_buffer is not None:
                self._test_buffer.append(msg)

            return msg

    __instance = __Impl()

    @staticmethod
    def get_instance() -> '__Impl':
        """Get Log instance."""
        return Log.__instance


def _build_cfg(console_level: Optional[LogLevel], file_level: Optional[LogLevel]) -> LogConfig:
    cfg = LogConfig()

    cfg.set_max_msg_length(200)

    if console_level:
        cfg.add_console_log(console_level)

    if file_level:
        cfg.add_file_log(file_level)

    return cfg


# Exported Default Log configurations.
LOG_CONFIG_TRACE_CONSOLE_ONLY = _build_cfg(LogLevel.Trace, None)
LOG_CONFIG_TRACE_FILE_ONLY = _build_cfg(None, LogLevel.Trace)
LOG_CONFIG_TRACE = _build_cfg(LogLevel.Trace, LogLevel.Trace)
LOG_CONFIG_INFO_CONSOLE_ONLY = _build_cfg(LogLevel.Info, None)
LOG_CONFIG_INFO_FILE_ONLY = _build_cfg(None, LogLevel.Info)
LOG_CONFIG_INFO = _build_cfg(LogLevel.Info, LogLevel.Info)
LOG_CONFIG_WARNING_CONSOLE_ONLY = _build_cfg(LogLevel.Warning, None)
LOG_CONFIG_WARNING_FILE_ONLY = _build_cfg(None, LogLevel.Warning)
LOG_CONFIG_WARNING = _build_cfg(LogLevel.Warning, LogLevel.Warning)
LOG_CONFIG_ERROR_CONSOLE_ONLY = _build_cfg(LogLevel.Error, None)
LOG_CONFIG_ERROR_FILE_ONLY = _build_cfg(None, LogLevel.Error)
LOG_CONFIG_ERROR = _build_cfg(LogLevel.Error, LogLevel.Error)
LOG_CONFIG_CRITICAL_CONSOLE_ONLY = _build_cfg(LogLevel.Critical, None)
LOG_CONFIG_CRITICAL_FILE_ONLY = _build_cfg(None, LogLevel.Critical)
LOG_CONFIG_CRITICAL = _build_cfg(LogLevel.Critical, LogLevel.Critical)
