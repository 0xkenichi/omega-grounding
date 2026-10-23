"""No-op stand-in for py_landlock (a Linux kernel sandbox, unavailable on macOS).

Only for tools/agent_run, which removes every file and shell skill from the agent
instead of sandboxing them.
"""

from enum import IntFlag


class AccessFs(IntFlag):
    EXECUTE = 1
    WRITE_FILE = 2
    READ_FILE = 4
    READ_DIR = 8
    REMOVE_DIR = 16
    REMOVE_FILE = 32
    MAKE_CHAR = 64
    MAKE_DIR = 128
    MAKE_REG = 256
    MAKE_SOCK = 512
    MAKE_FIFO = 1024
    MAKE_BLOCK = 2048
    MAKE_SYM = 4096
    REFER = 8192
    TRUNCATE = 16384
    IOCTL_DEV = 32768


class Landlock:
    def __init__(self, *args, **kwargs):
        pass

    def allow(self, *args, **kwargs):
        return self

    def apply(self, *args, **kwargs):
        return None

    def __getattr__(self, name):
        return lambda *args, **kwargs: self
