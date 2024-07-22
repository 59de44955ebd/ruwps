from ctypes import Structure, POINTER
from ctypes.wintypes import HWND, UINT, HDC, RECT

from ..const import *
from ..wintypes_extended import ULONG_PTR


class MEASUREITEMSTRUCT(Structure):
    _fields_ = [
        ("CtlType", UINT),
        ("CtlID", UINT),
        ("itemID", UINT),
        ("itemWidth", UINT),
        ("itemHeight", UINT),
        ("lItemlParam", ULONG_PTR),
    ]
LPMEASUREITEMSTRUCT = POINTER(MEASUREITEMSTRUCT)

class DRAWITEMSTRUCT(Structure):
    _fields_ = [
        ("CtlType", UINT),
        ("CtlID", UINT),
        ("itemID", UINT),
        ("itemAction", UINT),
        ("itemState", UINT),
        ("hwndItem", HWND),
        ("hDC", HDC),
        ("rcItem", RECT),
        ("itemData", ULONG_PTR),
    ]
