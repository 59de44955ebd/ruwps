"""
ruwps
=====

Ridiculously Uncomplicated Windows Python Systray apps.

ruwps exposes Winapi functions as Python classes and functions which greatly simplifies the process of creating a
systray application. It's a complement to rumps (), sharing (mostly) the same API,which allows creating
cross-platform - macOS and Windows - Statusbar/Systray apps based on the same code.

"""

__title__ = 'ruwps'
__version__ = '0.1.0'
__author__ = '59de44955ebd'
__license__ = 'MIT'
__copyright__ = 'Copyright 2024 https://github.com/59de44955ebd'

from ._internal import (alert, application_support, debug_mode, notification, quit_application, timers,
        App, MenuItem, Timer, Window, timer, clicked, notifications, separator)
del _internal
