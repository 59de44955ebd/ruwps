__all__ = ('MainWin',)

from ctypes import (windll, WINFUNCTYPE, c_int64, c_int, c_uint, c_uint64, c_long, c_ulong, c_longlong, c_voidp, c_wchar_p, Structure,
        sizeof, byref, create_string_buffer, create_unicode_buffer, cast,  c_char_p, pointer)
from ctypes.wintypes import (HWND, WORD, DWORD, LONG, HICON, WPARAM, LPARAM, HANDLE, LPCWSTR, MSG, UINT, LPWSTR, HINSTANCE,
        LPVOID, INT, RECT, POINT, BYTE, BOOL, COLORREF, LPPOINT)

from .const import *
from .wintypes_extended import *
from .dlls import gdi32, user32, ACCEL
from .window import *
from .menu import *
from .themes import *
#from winrumps.dialog import *

VKEY_NAME_MAP = {
    'Del': VK_DELETE,
    'Plus': VK_OEM_PLUS,
    'Minus': VK_OEM_MINUS,
    'Enter': VK_RETURN,
    'Left': VK_LEFT,
    'Right': VK_RIGHT,
}


class MainWin(Window):

    def __init__(self,
            window_title='MyPythonApp',
            window_class='MyPythonAppClass',
            hicon=0,
            left=CW_USEDEFAULT, top=CW_USEDEFAULT, width=CW_USEDEFAULT, height=CW_USEDEFAULT,
            style=WS_OVERLAPPEDWINDOW,
            ex_style=0,
            color=None,
            hbrush=None,
            menu_data=None,
            menu_mod_translation_table=None,
            accelerators=None,
            cursor=None,
            parent_window=None
            ):

        self.hicon = hicon

        self.__window_title = window_title
        self.__has_app_menus = menu_data is not None
        self.__popup_menus = {}
        self.__timers = {}
        self.__timer_id_counter = 1000
        self.__die = False
        # For asnyc dialogs
        self.__current_dialogs = []

        def _on_WM_TIMER(hwnd, wparam, lparam):
            if wparam in self.__timers:
                callback = self.__timers[wparam][0]
                if self.__timers[wparam][1]:
                    user32.KillTimer(self.hwnd, wparam)
                    del self.__timers[wparam]
                callback()
            # An application should return zero if it processes this message.
            return 0

        self.__message_map = {
                WM_TIMER:        [_on_WM_TIMER],
                WM_CLOSE:        [self.quit],
                }

        def _window_proc_callback(hwnd, msg, wparam, lparam):
            if msg in self.__message_map:
                for callback in self.__message_map[msg]:
                    res = callback(hwnd, wparam, lparam)
                    if res is not None:
                        return res
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self.windowproc = WNDPROC(_window_proc_callback)

        if type(color) == int:
            hbrush = color + 1
        elif type(color) == COLORREF:
            hbrush = gdi32.CreateSolidBrush(color)
        elif hbrush is None:
            hbrush = COLOR_WINDOW + 1

        self.bg_brush_light = hbrush

        newclass = WNDCLASSEX()
        newclass.lpfnWndProc = self.windowproc
        newclass.style = CS_VREDRAW | CS_HREDRAW
        newclass.lpszClassName = window_class
        newclass.hBrush = hbrush
        newclass.hCursor = user32.LoadCursorW(0, cursor if cursor else IDC_ARROW)
        newclass.hIcon = self.hicon

        accels = []

        if menu_data:
            self.hmenu = user32.CreateMenu()
            MainWin.__handle_menu_items(self.hmenu, menu_data['items'], accels, menu_mod_translation_table)
        else:
            self.hmenu = 0

        user32.RegisterClassExW(byref(newclass))

        super().__init__(
                newclass.lpszClassName,
                style=style,
                ex_style=ex_style,
                left=left, top=top, width=width, height=height,
                window_title=window_title,
                hmenu=self.hmenu,
                parent_window=parent_window
                )

        if accelerators:
            accels += accelerators

        if len(accels):
            acc_table = (ACCEL * len(accels))()
            for (i, acc) in enumerate(accels):
                acc_table[i] = ACCEL(TRUE | acc[0], acc[1], acc[2])
            self.__haccel = user32.CreateAcceleratorTableW(acc_table, len(accels))
        else:
            self.__haccel = None

    def make_popup_menu(self, menu_data):
        hmenu = user32.CreatePopupMenu()
        MainWin.__handle_menu_items(hmenu, menu_data['items'])
        return hmenu

    def create_timer(self, callback, ms, is_singleshot=False, timer_id=None):
        if timer_id is None:
            timer_id = self.__timer_id_counter
            self.__timer_id_counter += 1
        self.__timers[timer_id] = (callback, is_singleshot)
        user32.SetTimer(self.hwnd, timer_id, ms, 0)
        return timer_id

    def kill_timer(self, timer_id):
        if timer_id in self.__timers:
            user32.KillTimer(self.hwnd, timer_id)
            del self.__timers[timer_id]

#    def register_message_callback(self, msg, callback, overwrite=False):
#        if overwrite:
#            self.__message_map[msg] = [callback]
#        else:
#            if msg not in self.__message_map:
#                self.__message_map[msg] = []
#            self.__message_map[msg].append(callback)
#
#    def unregister_message_callback(self, msg, callback=None):
#        if msg in self.__message_map:
#            if callback is None:  # was: == True
#                del self.__message_map[msg]
#            elif callback in self.__message_map[msg]:
#                self.__message_map[msg].remove(callback)
#                if len(self.__message_map[msg]) == 0:
#                    del self.__message_map[msg]

    def run(self):
        msg = MSG()
        while not self.__die and user32.GetMessageW(byref(msg), 0, 0, 0) != 0:

            # unfortunately this disables global accelerators while a dialog is shown
            for dialog in self.__current_dialogs:
                if user32.IsDialogMessageW(dialog.hwnd, byref(msg)):
                    break

            # If the inner loop completes without encountering
            # the break statement then the following else
            # block will be executed and outer loop will continue
            else:
                if not user32.TranslateAcceleratorW(self.hwnd, self.__haccel, byref(msg)):
                    user32.TranslateMessage(byref(msg))
                    user32.DispatchMessageW(byref(msg))

        if self.__haccel:
            user32.DestroyAcceleratorTable(self.__haccel)
        user32.DestroyWindow(self.hwnd)
        user32.DestroyIcon(self.hicon)
        return 0

    def quit(self, *args):
        self.__die = True
        user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)

    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)

        # Update colors of window titlebar
        dwm_use_dark_mode(self.hwnd, is_dark)

        user32.SetClassLongPtrW(self.hwnd, GCL_HBRBACKGROUND, BG_BRUSH_DARK if is_dark else self.bg_brush_light)

        # Update colors of menus
        uxtheme.SetPreferredAppMode(PreferredAppMode.ForceDark if is_dark else PreferredAppMode.ForceLight)
        uxtheme.FlushMenuThemes()

        if self.__has_app_menus:
            # Update colors of menubar
            if is_dark:
                def _on_WM_UAHDRAWMENU(hwnd, wparam, lparam):
                    pUDM = cast(lparam, POINTER(UAHMENU)).contents
                    mbi = MENUBARINFO()
                    ok = user32.GetMenuBarInfo(hwnd, OBJID_MENU, 0, byref(mbi))
                    rc_win = RECT()
                    user32.GetWindowRect(hwnd, byref(rc_win))
                    rc = mbi.rcBar
                    user32.OffsetRect(byref(rc), -rc_win.left, -rc_win.top)
                    res = user32.FillRect(pUDM.hdc, byref(rc), MENUBAR_BG_BRUSH_DARK)
                    return TRUE
                self.register_message_callback(WM_UAHDRAWMENU, _on_WM_UAHDRAWMENU)

                def _on_WM_UAHDRAWMENUITEM(hwnd, wparam, lparam):
                    pUDMI = cast(lparam, POINTER(UAHDRAWMENUITEM)).contents
                    mii = MENUITEMINFOW()
                    mii.fMask = MIIM_STRING
                    buf = create_unicode_buffer('', 256)
                    mii.dwTypeData = cast(buf, LPWSTR)
                    mii.cch = 256
                    ok = user32.GetMenuItemInfoW(pUDMI.um.hmenu, pUDMI.umi.iPosition, TRUE, byref(mii))
                    if pUDMI.dis.itemState & ODS_HOTLIGHT or pUDMI.dis.itemState & ODS_SELECTED:
                        user32.FillRect(pUDMI.um.hdc, byref(pUDMI.dis.rcItem), MENU_BG_BRUSH_HOT)
                    else:
                        user32.FillRect(pUDMI.um.hdc, byref(pUDMI.dis.rcItem), MENUBAR_BG_BRUSH_DARK)
                    gdi32.SetBkMode(pUDMI.um.hdc, TRANSPARENT)
                    gdi32.SetTextColor(pUDMI.um.hdc, TEXT_COLOR_DARK)
                    user32.DrawTextW(pUDMI.um.hdc, mii.dwTypeData, len(mii.dwTypeData), byref(pUDMI.dis.rcItem), DT_CENTER | DT_SINGLELINE | DT_VCENTER)
                    return TRUE
                self.register_message_callback(WM_UAHDRAWMENUITEM, _on_WM_UAHDRAWMENUITEM)

                def UAHDrawMenuNCBottomLine(hwnd, wparam, lparam):
                    rcClient = RECT()
                    user32.GetClientRect(hwnd, byref(rcClient))
                    user32.MapWindowPoints(hwnd, None, byref(rcClient), 2)
                    rcWindow = RECT()
                    user32.GetWindowRect(hwnd, byref(rcWindow))
                    user32.OffsetRect(byref(rcClient), -rcWindow.left, -rcWindow.top)
                    # the rcBar is offset by the window rect
                    rcAnnoyingLine = rcClient
                    rcAnnoyingLine.bottom = rcAnnoyingLine.top
                    rcAnnoyingLine.top -= 1
                    hdc = user32.GetWindowDC(hwnd)
                    user32.FillRect(hdc, byref(rcAnnoyingLine), BG_BRUSH_DARK)
                    user32.ReleaseDC(hwnd, hdc)

                def _on_WM_NCPAINT(hwnd, wparam, lparam):
                    user32.DefWindowProcW(hwnd, WM_NCPAINT, wparam, lparam)
                    UAHDrawMenuNCBottomLine(hwnd, wparam, lparam)
                    return TRUE
                self.register_message_callback(WM_NCPAINT, _on_WM_NCPAINT)

                def _on_WM_NCACTIVATE(hwnd, wparam, lparam):
                    user32.DefWindowProcW(hwnd, WM_NCACTIVATE, wparam, lparam)
                    UAHDrawMenuNCBottomLine(hwnd, wparam, lparam)
                    return TRUE
                self.register_message_callback(WM_NCACTIVATE, _on_WM_NCACTIVATE)

            else:
                self.unregister_message_callback(WM_UAHDRAWMENU)
                self.unregister_message_callback(WM_UAHDRAWMENUITEM)
                self.unregister_message_callback(WM_NCPAINT)
                self.unregister_message_callback(WM_NCACTIVATE)

        self.redraw_window()

    def dialog_show_async(self, dialog):
        self.__current_dialogs.append(dialog)
        dialog._show_async()

    def dialog_show_sync(self, dialog, lparam=0):
        res = dialog._show_sync(lparam=lparam)
        user32.SetActiveWindow(self.hwnd)
        return res

    def _dialog_remove(self, dialog):
        if dialog in self.__current_dialogs:
            self.__current_dialogs.remove(dialog)

    @staticmethod
    def __handle_menu_items(hmenu, menu_items, accels=None, key_mod_translation=None):
        for row in menu_items:
            if 'items' in row:
                hmenu_child = user32.CreateMenu()
                user32.AppendMenuW(hmenu, MF_POPUP, hmenu_child, row['caption'])
                if 'hbitmap' in row:
                    info = MENUITEMINFOW()
                    ok = user32.GetMenuItemInfoW(hmenu, hmenu_child, FALSE, byref(info))
                    info.fMask = MIIM_BITMAP
                    info.hbmpItem = row['hbitmap']
                    user32.SetMenuItemInfoW(hmenu, hmenu_child, FALSE, byref(info))
                MainWin.__handle_menu_items(hmenu_child, row['items'], accels, key_mod_translation)
            else:
                if row['caption'] == '-':
                    user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, '-')
                    continue
                id = row['id'] if 'id' in row else None
                flags = MF_STRING
                if 'flags' in row:
                    if 'CHECKED' in row['flags']:
                        flags |= MF_CHECKED
                    if 'GRAYED' in row['flags']:
                        flags |= MF_GRAYED
                if '\t' in row['caption']:
                    parts = row['caption'].split('\t') #[1]
                    vk = parts[1]
                    fVirt = 0
                    if 'Alt+' in vk:
                        fVirt |= FALT
                        vk = vk.replace('Alt+', '')
                        if key_mod_translation and 'ALT' in key_mod_translation:
                            parts[1] = parts[1].replace('Alt', key_mod_translation['ALT'])
                    if 'Ctrl+' in vk:
                        fVirt |= FCONTROL
                        vk = vk.replace('Ctrl+', '')
                        if key_mod_translation and 'CTRL' in key_mod_translation:
                            parts[1] = parts[1].replace('Ctrl', key_mod_translation['CTRL'])
                    if 'Shift+' in vk:
                        fVirt |= FSHIFT
                        vk = vk.replace('Shift+', '')
                        if key_mod_translation and 'SHIFT' in key_mod_translation:
                            parts[1] = parts[1].replace('Shift', key_mod_translation['SHIFT'])

                    if len(vk) > 1:
                        if key_mod_translation and vk.upper() in key_mod_translation:
                            parts[1] = parts[1].replace(vk, key_mod_translation[vk.upper()])
                        vk = VKEY_NAME_MAP[vk] if vk in VKEY_NAME_MAP else eval('VK_' + vk)
                    else:
                        vk = ord(vk)

                    if accels is not None:
                        accels.append((fVirt, vk, id))

                    row['caption'] = '\t'.join(parts)
                user32.AppendMenuW(hmenu, flags, id, row['caption'])

                if 'hbitmap' in row:
                    info = MENUITEMINFOW()
                    ok = user32.GetMenuItemInfoW(hmenu, id, FALSE, byref(info))
                    info.fMask = MIIM_BITMAP
                    info.hbmpItem = row['hbitmap']
                    user32.SetMenuItemInfoW(hmenu, id, FALSE, byref(info))
