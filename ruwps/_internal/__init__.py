import inspect
import os
import sys
import traceback

from ctypes import byref, create_unicode_buffer
from ctypes.wintypes import POINT, RECT

from .winapp.const import *
from .winapp.dialog import Dialog
from .winapp.dlls import kernel32, user32
from .winapp.mainwin import MainWin
from .winapp.menu import MENUITEMINFOW
from .winapp.themes import reg_should_use_dark_mode
from .winapp.trayicon import *
from .winapp.wintypes_extended import *

separator = object()

class SeparatorItem(object):
    pass

_app = None

_MYWM_NOTIFYICON = 1025
_NO_APP_ERROR = RuntimeError('No app instance')
_TIMERS = []
_USE_DARK = reg_should_use_dark_mode(True)
_IS_FROZEN = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
_MENU_ICON_SIZE = 16

# If no icon was specified in App's constructor, we could use a system icon like IDI_APPLICATION,
# using: hicon = user32.LoadIconW(0, MAKEINTRESOURCEW(IDI_APPLICATION))
# But this looks really ugly, therefor we use some provided custom ico file instead.
_DEFAULT_ICO_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources', 'default.ico')

########################################
#
########################################
_id_counter = 0
def _unique_id():
    global _id_counter
    id = _id_counter
    _id_counter += 1
    return id

########################################
#
########################################
def _make_menu_data(parent_dict, menuitem):
    if type(menuitem) == SeparatorItem:
        parent_dict['items'].append({'caption': '-'})
        return
    menu_dict = {'caption': menuitem.title, 'id': menuitem.id}
    if menuitem.callback:
        _app._command_message_map[menuitem.id] = menuitem
    else:
        menu_dict['flags'] = 'GRAYED'
    if menuitem.key:
        menu_dict['caption'] += '\t' + menuitem.key
    if menuitem.state:
        menu_dict['flags'] = menu_dict['flags'] + 'CHECKED' if 'flags' in menu_dict else 'CHECKED'
    if menuitem.icon:
        menu_dict['hbitmap'] = user32.LoadImageW(0, menuitem.icon, IMAGE_BITMAP, _MENU_ICON_SIZE, _MENU_ICON_SIZE, LR_LOADFROMFILE)
    parent_dict['items'].append(menu_dict)
    if len(menuitem.values()):
        menu_dict['items'] = []
        for child_item in menuitem.values():
            _make_menu_data(menu_dict, child_item)

########################################
#
########################################
def _call_as_function_or_method(func, *args, **kwargs):
    # The idea here is that when using decorators in a class, the functions passed are not bound so we have to
    # determine later if the functions we have (those saved as callbacks) for particular events need to be passed
    # 'self'.
    #
    # This works for an App subclass method or a standalone decorated function. Will attempt to find function as
    # a bound method of the App instance. If it is found, use it, otherwise simply call function.
    if _app:
        for name, method in inspect.getmembers(_app, predicate=inspect.ismethod):
            if method.__func__ is func:
                return method(*args, **kwargs)
    return func(*args, **kwargs)

########################################
#
########################################
def alert(title='', message='', ok=None, cancel=None):
    global _app
    if _app is None:
        _app = MainWin()
        if _USE_DARK:
            _app.apply_theme(True)

    if title and not message:
        message = title
        title = ''

    buttons = []
    if ok is None:
        buttons.append(user32.MB_GetString(IDOK - 1))
    else:
        buttons.append(str(ok))
    if type(cancel) == str:
        buttons.append(cancel)
    elif cancel:
        buttons.append(user32.MB_GetString(IDCANCEL - 1))

    font = ['Segoe UI', 9]

    dialog_width = 200
    margin = 7
    text_width = dialog_width - 2 * margin
    text_y = 14
    button_width, button_height, button_dist = 50, 12, 5
    text_height = Dialog.calculate_multiline_text_height(message, text_width, *font)
    dialog_height = 50 + text_height

    dialog_dict = {
        'class': '#32770',
        'caption': title,
        'font': font,
        'rect': [0, 0, dialog_width, dialog_height],
        'style': 2496137669,
        'exstyle': 65793,
        'controls': []
    }

    # add text
    dialog_dict['controls'].append({
        'id': -1,
        'class': 'STATIC',
        'caption': message,
        'rect': [margin, text_y, text_width, text_height],
        'style': 1342316672,
    })

    # add button(s)
    x = dialog_width - margin - len(buttons) * button_width - (len(buttons) - 1) * button_dist
    for i, button_text in enumerate(buttons):
        dialog_dict['controls'].append({
            'id': i,
            'class': 'BUTTON',
            'caption': button_text,
            'rect': [x, dialog_height - margin - button_height, button_width, button_height],
            'style': WS_CHILD | WS_VISIBLE | WS_GROUP | WS_TABSTOP | BS_TEXT | (BS_DEFPUSHBUTTON if i == 0 else BS_PUSHBUTTON),
        })
        x += button_width + button_dist

    def _dialog_proc_callback(hwnd, msg, wparam, lparam):
        if msg == WM_COMMAND:
            control_id = LOWORD(wparam)
            command = HIWORD(wparam)
            if command == BN_CLICKED:
                user32.EndDialog(hwnd, control_id)
        elif msg == WM_CLOSE:
            user32.EndDialog(hwnd, len(buttons) - 1)
        return FALSE

    _log('alert opened with message: {0}, title: {1}'.format(repr(message), repr(title)))
    btn_id = _app.dialog_show_sync(Dialog(_app, dialog_dict, _dialog_proc_callback))
    # The “ok” button will return 1 and the “cancel” button will return 0.
    return 1 - btn_id

########################################
#
########################################
def application_support(name):
    d = os.path.join(os.environ['LOCALAPPDATA'], name)
    if not os.path.isdir(d):
        os.mkdir(d)
    return d

########################################
#
########################################
def debug_mode(choice):
    """Enable/disable printing helpful information for debugging the program. Default is off."""
    global _log
    if choice:
        if _IS_FROZEN:
            def _log(*args):
                kernel32.OutputDebugStringW(' '.join(map(str, args)))
        else:
            _log = print
    else:
        def _log(*_):
            pass
debug_mode(False)

########################################
#
########################################
def notification(title='', subtitle='', message='', data=None, sound=True, win_flags=NIIF_INFO):
    if _app is None:
        raise _NO_APP_ERROR
    if not sound:
        win_flags |= NIIF_NOSOUND
    if subtitle:
        title += '\n' + subtitle  # win notifications have no subtitles
    notification.__dict__['*data'] = data
    _app.trayicon.notify(message, title, flags=win_flags)

########################################
#
########################################
def quit_application(*args):
    _log('closing application')
    if _app is None:
        raise _NO_APP_ERROR
    try:
        super(App, _app).quit()
    except:
        _app.quit()

########################################
#
########################################
def timers():
    return _TIMERS


########################################
#
########################################
class MenuItem(object):

    def __init__(self, title, callback=None, key=None, icon=None, dimensions=None, template=None):
        self._title = title
        self.callback = callback
        self.key = key
        if template:
            self._icon = icon[int(_USE_DARK)]
        else:
            self._icon = icon
        self._state = 0
        self.id = _unique_id()
        self.child_dict = {}

    def __repr__(self):
        return '<{}: [{}; callback: {}]>'.format(type(self).__name__,
                repr(self.title), repr(self.callback))

    def __setitem__(self, key, value):
        exists = key in self.child_dict
        self.child_dict[key] = default
        _app._update_menu()

    def __getitem__(self, key):
        return self.child_dict[key]

    def __delitem__(self, key):
        c = self.child_dict[key]
        del self.child_dict[key]
        _app._update_menu()

    def setdefault(self, key, default=None):
        'od.setdefault(k[,d]) -> od.get(k,d), also set od[k]=d if k not in od'
        if key in self.child_dict:
            return self.child_dict[key]
        self.child_dict[key] = default
        _app._update_menu()
        return default

    def add(self, menuitem):
        if type(menuitem) == str:
            menuitem = MenuItem(menuitem)
        elif menuitem == separator:
            menuitem = SeparatorItem()
        if type(menuitem) == SeparatorItem:
            self.child_dict[menuitem] = menuitem
        else:
            self.child_dict[menuitem.title] = menuitem
        _app._update_menu()

    def clear(self):
        self.child_dict = {}
        _app._update_menu()

    def update(self, menu=[]):
        self.child_dict = {}
        self._append(menu)
        _app._update_menu()

    def keys(self):
        return list(self.child_dict.keys())

    def values(self):
        return list(self.child_dict.values())

    def items(self):
        return self.child_dict.items()  # cast to list?

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        if _app:
            info = MENUITEMINFOW()
            info.fMask = MIIM_STRING
            info.dwTypeData = value
            user32.SetMenuItemInfoW(_app.hmenu_popup, self.id, FALSE, byref(info))

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, value):
        self._icon = value
        if _app:
            info = MENUITEMINFOW()
            info.fMask = MIIM_BITMAP
            info.hbmpItem = user32.LoadImageW(0, value, IMAGE_BITMAP, _MENU_ICON_SIZE, _MENU_ICON_SIZE, LR_LOADFROMFILE)
            user32.SetMenuItemInfoW(_app.hmenu_popup, self.id, FALSE, byref(info))

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        if _app:
            user32.CheckMenuItem(_app.hmenu_popup, self.id, MF_BYCOMMAND | (MF_CHECKED if value else MF_UNCHECKED))

    def set_callback(self, callback, key=None):
        had_callback = self.callback is not None
        self.callback = callback
        has_callback = self.callback is not None
        if _app and has_callback != had_callback:
            info = MENUITEMINFOW()
            info.fMask = MIIM_STATE
            info.fState = (MFS_ENABLED if has_callback else MFS_GRAYED) | (MFS_CHECKED if self._state else MFS_UNCHECKED)
            user32.SetMenuItemInfoW(_app.hmenu_popup, self.id, FALSE, byref(info))

    def _append(self, m):
        if m is None:
            self.add(SeparatorItem())
        elif type(m) == MenuItem:
            self.add(m)
        elif type(m) == str:
            self.add(MenuItem(m))
        elif type(m) == dict:
            for k, v in m.items():
                mi = MenuItem(k)
                self.add(mi)
                mi._append(v)
        elif type(m) == list:
            for v in m:
                self._append(v)

########################################
#
########################################
class App(MainWin):

    def __init__(self, name, title=None, icon=None, template=None, menu=None, quit_button='Quit'):
        super().__init__(name)

        global _app
        _app = self

        self.name = name
        self._title = name if title is None else str(title)

        self.quit_button = quit_button
        self.hmenu_popup = None
        self._command_message_map = {}

        self._icon = icon
        if icon is None:
            if _IS_FROZEN:
                hicon = user32.LoadIconW(kernel32.GetModuleHandleW(None), MAKEINTRESOURCEW(1))
            else:
                hicon = user32.LoadImageW(0, _DEFAULT_ICO_FILE, IMAGE_ICON, 48, 48, LR_LOADFROMFILE)
        else:
            hicon = user32.LoadImageW(0, self._icon, IMAGE_ICON, 48, 48, LR_LOADFROMFILE)

        self.trayicon = TrayIcon(self, hicon, self._title, _MYWM_NOTIFYICON, show=False)

        self._menu = MenuItem('')  #Menu()

        ########################################
        #
        ########################################
        def _on_MYWM_NOTIFYICON(hwnd, wparam, lparam):

            msg = LOWORD(lparam)
            if msg == WM_RBUTTONUP:
                rc = RECT()
                user32.SystemParametersInfoA(SPI_GETWORKAREA, NULL, byref(rc), NULL)
                pt = POINT(GET_X_LPARAM(wparam), rc.bottom)
                self.set_foreground_window()
                item_id = user32.TrackPopupMenuEx(self.hmenu_popup, TPM_LEFTBUTTON | TPM_RETURNCMD, pt.x, pt.y, self.hwnd, 0)
                user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)

                if item_id in self._command_message_map:
                    mi = self._command_message_map[item_id]
                    if mi.callback:
                        _call_as_function_or_method(mi.callback, mi)

            elif msg == NIN_BALLOONTIMEOUT or msg == NIN_BALLOONUSERCLICK:
                self.trayicon.restore_tooltip()
                if msg == NIN_BALLOONUSERCLICK and hasattr(notifications, '*notifications'):
                    _call_as_function_or_method(getattr(notifications, '*notifications'), getattr(notification, '*data'))

        self.register_message_callback(_MYWM_NOTIFYICON, _on_MYWM_NOTIFYICON)

        if _USE_DARK:
            self.apply_theme(True)

        self.trayicon.show()

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, value):
        self._icon = _DEFAULT_ICO_FILE if value is None else value
        hicon = user32.LoadImageW(0, self._icon, IMAGE_ICON, 48, 48, LR_LOADFROMFILE)
        self.trayicon.set_icon(hicon)

    @property
    def menu(self):
        """Represents the main menu of the statusbar application. Setting `menu` works by calling
        :meth:`rumps.MenuItem.update`.
        """
        return self._menu

    @menu.setter
    def menu(self, iterable):
        self._menu.update(iterable)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        value = '' if value is None else str(value)
        self._title = value
        self.trayicon.set_tooltip(value)

    ########################################
    #
    ########################################
    def open(self, filename, *args):
        d = application_support(self.name)
        return open(os.path.join(d, filename), *args)

    ########################################
    #
    ########################################
    def run(self):

#        setattr(App, '*app_instance', self)  # class level ref to running instance (for passing self to App subclasses)

        t = b = None
        for t in _TIMERS:
            t.start()
        for b in getattr(clicked, '*buttons', []):
            b(self)  # we waited on registering clicks so we could pass self to access _menu attribute
        del t, b

        if self.quit_button is not None:
            if len(self._menu.values()) and type(self._menu.values()[-1]) != SeparatorItem:  #self._menu.values()[-1].title != '-':
                self._menu.add(SeparatorItem())  #MenuItem('-'))
            if type(self.quit_button) == str:
                self.quit_button = MenuItem(self.quit_button)
            self.quit_button.set_callback(self.quit)
            self._menu.add(self.quit_button)

        # convert to winapp menu dict
        menu_data = {"items": []}
        for c in self._menu.values():
             _make_menu_data(menu_data, c)

        self.hmenu_popup = self.make_popup_menu(menu_data)

        super().run()

    ########################################
    #
    ########################################
    def _update_menu(self):
        if self.hmenu_popup:
            user32.DestroyMenu(self.hmenu_popup)
        if len(self.menu.values()):
            menu_data = {"items": []}
            for c in self.menu.values():
                 _make_menu_data(menu_data, c)
            self.hmenu_popup = self.make_popup_menu(menu_data)


########################################
# Holds information from user interaction with a rumps.Window after it has been closed.
########################################
class Response(object):

    def __init__(self, clicked, text=''):
        self.clicked = clicked
        self.text = text


########################################
#
########################################
class Window(object):

    def __init__(self, message='', title='', default_text='', ok=None, cancel=None, dimensions=(320, 160)):
        global _app
        if _app is None:
            _app = MainWin()
            if _USE_DARK:
                _app.apply_theme(True)

        self._message = message
        self._title = title
        self._default_text = default_text
        self._buttons = []

        if ok is None:
            self._buttons.append(user32.MB_GetString(IDOK - 1))
        else:
            self._buttons.append(str(ok))

        if type(cancel) == str:
            self._buttons.append(cancel)
        elif cancel:
            self._buttons.append(user32.MB_GetString(IDCANCEL - 1))

        self._dialog_width = dimensions[0] // 2

    def add_button(self, name):
        """ Create a new button. """
        self._buttons.append(name)

    def add_buttons(self, *args):
        if len(args):
            if type(args[0]) != str:
                for btn in args[0]:
                    self.add_button(btn)
            else:
                for btn in args:
                    self.add_button(btn)

    def run(self):
        IDC_EDIT = 2
        margin = 7
        button_width, button_height, button_dist = 50, 12, 5
        dialog_width_min = 2 * margin + len(self._buttons) * button_width + (len(self._buttons) - 1) * button_dist
        dialog_width = max(self._dialog_width, dialog_width_min)
        dialog_height = 60

        self._dialog_dict = {
            "class": "DIALOGEX",
            "rect": [200, 200, dialog_width, dialog_height],
            "style": -2134376256,
            "caption": self._title,
            "font": ['Segoe UI', 9],
            "controls": [
                {
                    "caption": self._message,
                    "id": -1,
                    "class": "STATIC",
                    "style": 1342308352,
                    "rect": [margin, margin, dialog_width - 2 * margin, 8]
                },
                {
                    "caption": "",
                    "id": IDC_EDIT,
                    "class": "EDIT",
                    "style": WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
                    "rect": [margin, 18, dialog_width - 2 * margin, 12]
                },
            ]
        }

        x = dialog_width - margin - len(self._buttons) * button_width - (len(self._buttons) - 1) * button_dist

        for i, button_text in enumerate(self._buttons):
            self._dialog_dict['controls'].append({
                'id': i,
                'class': 'BUTTON',
                'caption': button_text,
                'rect': [x, dialog_height - margin - button_height, button_width, button_height],
                'style': WS_CHILD | WS_VISIBLE | WS_GROUP | WS_TABSTOP | BS_TEXT | (BS_DEFPUSHBUTTON if i == 0 else BS_PUSHBUTTON),
            })
            x += button_width + button_dist

        def _dialog_proc_callback(hwnd, msg, wparam, lparam):
            if msg == WM_INITDIALOG:
                if self._default_text:
                    user32.SendDlgItemMessageW(hwnd, IDC_EDIT, WM_SETTEXT, 0, create_unicode_buffer(self._default_text))
            elif msg == WM_COMMAND:
                command = HIWORD(wparam)
                if command == BN_CLICKED:
                    control_id = LOWORD(wparam)
                    text_len = user32.SendDlgItemMessageW(hwnd, IDC_EDIT, WM_GETTEXTLENGTH, 0, 0) + 1
                    buf = create_unicode_buffer(text_len)
                    user32.SendDlgItemMessageW(hwnd, IDC_EDIT, WM_GETTEXT, text_len, byref(buf))
                    self._result = str(buf.value)
                    user32.EndDialog(hwnd, control_id)
            elif msg == WM_CLOSE:
                user32.EndDialog(hwnd, len(self._buttons) - 1)
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._dialog = Dialog(_app, self._dialog_dict, _dialog_proc_callback)

        self._result = self._default_text
        btn_id = _app.dialog_show_sync(self._dialog)
        # The “ok” button will return 1 and the “cancel” button will return 0.
        if btn_id < 2:
            btn_id = 1 - btn_id
        return Response(btn_id, self._result)


########################################
#
########################################
class Timer(object):

    def __init__(self, callback, interval):
        self.callback = callback
        self._interval = interval
        self._timer_id = None
        _TIMERS.append(self)

    def __repr__(self):
        return ('<{0}: [callback: {1}; interval: {2}; '
                'status: {3}]>').format(type(self).__name__, repr(self.callback.__name__),
                                        self._interval, 'ON' if self._timer_id else 'OFF')
    @property
    def interval(self):
        """The time in seconds to wait before calling the :attr:`callback` function."""
        return self._interval

    @interval.setter
    def interval(self, new_interval):
        self._interval = new_interval
        if self.is_alive():
            self.stop()
            self.start()

    def is_alive(self):
        """Whether the timer thread loop is currently running."""
        return self._timer_id is not None

    def set_callback(self, callback):
        """Set the function that should be called every interval seconds. It will be passed this rumps.Timer object as its only parameter."""
        self.callback = callback
        if self.is_alive():
            self.stop()
            self.start()

    def start(self):
        """Start the timer thread loop."""
        if _app is None:
            raise _NO_APP_ERROR
        self._timer_id = _app.create_timer(lambda: _call_as_function_or_method(self.callback, self),
                int(self._interval * 1000))

    def stop(self):
        """Stop the timer thread loop."""
        if self._timer_id:
            _app.kill_timer(self._timer_id)
            self._timer_id = None


# Decorators and helper function serving to register functions for dealing with interaction and events
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def timer(interval):
    """Decorator for registering a function as a callback in a new thread. The function will be repeatedly called every
    `interval` seconds. This decorator accomplishes the same thing as creating a :class:`rumps.Timer` object by using
    the decorated function and `interval` as parameters and starting it on application launch.

    .. code-block:: python

        @rumps.timer(2)
        def repeating_function(sender):
            print 'hi'

    :param interval: a number representing the time in seconds before the decorated function should be called.
    """
    def decorator(func):
        t = Timer(func, interval)
        return func
    return decorator

def clicked(*args, **options):
    """Decorator for registering a function as a callback for a click action on a :class:`rumps.MenuItem` within the
    application. The passed `args` must specify an existing path in the main menu. The :class:`rumps.MenuItem`
    instance at the end of that path will have its :meth:`rumps.MenuItem.set_callback` method called, passing in the
    decorated function.

    .. code-block:: python

        @rumps.clicked('Animal', 'Dog', 'Corgi')
        def corgi_button(sender):
            import subprocess
            subprocess.call(['say', '"corgis are the cutest"'])

    :param args: a series of strings representing the path to a :class:`rumps.MenuItem` in the main menu of the
                 application.
    :param key: a string representing the key shortcut as an alternative means of clicking the menu item.
    """

    def decorator(func):
        def register_click(self):
            menuitem = self._menu  # self not defined yet but will be later in 'run' method
            if menuitem is None:
                raise ValueError('no menu created')
            for arg in args:
                try:
                    menuitem = menuitem.child_dict[arg]
                except KeyError:
                    mi = MenuItem(arg)
                    menuitem.add(mi)
                    menuitem = mi
            menuitem.set_callback(func, options.get('key'))
        # delay registering the button until we have a current instance to be able to traverse the menu
        buttons = clicked.__dict__.setdefault('*buttons', [])
        buttons.append(register_click)
        return func
    return decorator

def notifications(func):
    notifications.__dict__['*notifications'] = func
