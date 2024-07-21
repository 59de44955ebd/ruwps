import uuid

from ctypes import Union, Structure, c_ubyte, sizeof, byref
from ctypes.wintypes import UINT, DWORD, HWND, WCHAR, HICON

from .dlls import shell32

NIM_ADD = 0
NIM_MODIFY = 1
NIM_DELETE = 2
NIM_SETFOCUS = 3
NIM_SETVERSION = 4

WM_USER = 1024
NIN_BALLOONSHOW = WM_USER + 2
NIN_BALLOONHIDE = WM_USER + 3
NIN_BALLOONTIMEOUT = WM_USER + 4
NIN_BALLOONUSERCLICK = WM_USER + 5
NIN_POPUPOPEN = WM_USER + 6
NIN_POPUPCLOSE = WM_USER + 7

NIF_MESSAGE = 1
NIF_ICON = 2
NIF_TIP = 4
NIF_STATE = 8
NIF_INFO = 16
NIF_GUID = 32
NIF_REALTIME = 64
NIF_SHOWTIP = 128

NIIF_NONE = 0
NIIF_INFO = 1
NIIF_WARNING = 2
NIIF_ERROR = 3
NIIF_USER = 4
NIIF_NOSOUND = 16
NIIF_LARGE_ICON = 32
NIIF_RESPECT_QUIET_TIME = 128
NIIF_ICON_MASK = 15

NOTIFYICON_VERSION = 3
NOTIFYICON_VERSION_4 = 4

NIS_HIDDEN = 0x1
NIS_SHAREDICON = 0x2

ID_TRAYICON = 300

class _TimeoutVersionUnion(Union):
    _fields_ = [('uTimeout', UINT),
                ('uVersion', UINT),]

class NOTIFYICONDATAW(Structure):
    def __init__(self, *args, **kwargs):
        super(NOTIFYICONDATAW, self).__init__(*args, **kwargs)
        self.cbSize = sizeof(self)
    _fields_ = [
        ('cbSize', DWORD),
        ('hWnd', HWND),
        ('uID', UINT),
        ('uFlags', UINT),
        ('uCallbackMessage', UINT),
        ('hIcon', HICON),
        ('szTip', WCHAR * 128),
        ('dwState', DWORD),
        ('dwStateMask', DWORD),
        ('szInfo', WCHAR * 256),
        ('union', _TimeoutVersionUnion),
        ('szInfoTitle', WCHAR * 64),
        ('dwInfoFlags', DWORD),
        ('guidItem', c_ubyte * 16),  # GUID
        ('hBalloonIcon', HICON),
    ]


class TrayIcon(object):

    def __init__(self, parent_window, hicon, window_title, message_id, show=True, message_timeout=5000):
        self.trayiconinfo = NOTIFYICONDATAW()
        self.trayiconinfo.hWnd = parent_window.hwnd
        self.trayiconinfo.uID = ID_TRAYICON
        self.trayiconinfo.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP | NIF_SHOWTIP | NIF_GUID
        self.trayiconinfo.uCallbackMessage = message_id
        self.trayiconinfo.hIcon = hicon
        self.trayiconinfo.szTip = window_title
        self.trayiconinfo.dwState = NIS_SHAREDICON
        self.trayiconinfo.szInfo = window_title
        self.trayiconinfo.union.uTimeout = message_timeout
        self.trayiconinfo.dwInfoFlags = NIIF_INFO
        self.trayiconinfo.guidItem = (c_ubyte * 16)(*bytearray(uuid.uuid4().bytes))
        self.trayiconinfo.hBalloonIcon = 0
        if show:
            self.show()

    def __del__(self):
        shell32.Shell_NotifyIconW(NIM_DELETE, byref(self.trayiconinfo))

    def show(self, flag=True):
        res = shell32.Shell_NotifyIconW(NIM_ADD if flag else NIM_DELETE, byref(self.trayiconinfo))
        if flag:
            self.trayiconinfo.union.uVersion = NOTIFYICON_VERSION_4
            res = shell32.Shell_NotifyIconW(NIM_SETVERSION, byref(self.trayiconinfo))

    def notify(self, info, info_title='', flags=NIIF_INFO):
        nid = NOTIFYICONDATAW()
        nid.uFlags = NIF_INFO | NIF_GUID
        nid.guidItem = self.trayiconinfo.guidItem
        nid.dwInfoFlags = flags
        nid.szInfoTitle = info_title
        nid.szInfo = info
        return shell32.Shell_NotifyIconW(NIM_MODIFY, byref(nid))

    def restore_tooltip(self):
        nid = NOTIFYICONDATAW()
        nid.uFlags = NIF_SHOWTIP | NIF_GUID
        nid.guidItem = self.trayiconinfo.guidItem
        return shell32.Shell_NotifyIconW(NIM_MODIFY, byref(nid))

    def set_tooltip(self, tooltip):
        nid = NOTIFYICONDATAW()
        nid.szTip = tooltip
        nid.uFlags = NIF_TIP | NIF_SHOWTIP | NIF_GUID
        nid.guidItem = self.trayiconinfo.guidItem
        return shell32.Shell_NotifyIconW(NIM_MODIFY, byref(nid))

    def set_icon(self, hicon):
        nid = NOTIFYICONDATAW()
        nid.hIcon = hicon
        nid.uFlags = NIF_ICON | NIF_SHOWTIP | NIF_GUID
        nid.guidItem = self.trayiconinfo.guidItem
        return shell32.Shell_NotifyIconW(NIM_MODIFY, byref(nid))
