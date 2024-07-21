import sys

IS_MAC = sys.platform == 'darwin'
IS_WIN = sys.platform == 'win32'
if IS_MAC:
    import rumps as rups
elif IS_WIN:
    import ruwps as rups
else:
    print('Linux not supported!')  # We really also need rulps! ;-)
    sys.exit(1)


rups.debug_mode(True)

@rups.clicked('Print Something')
def print_something(_):
    rups.alert(message='something', ok='YES!', cancel='NO!')


@rups.clicked('On/Off Test')
def on_off_test(_):
    print_button = app.menu['Print Something']
    if print_button.callback is None:
        print_button.set_callback(print_something)
    else:
        print_button.set_callback(None)


@rups.clicked('Clean Quit')
def clean_up_before_quit(_):
    print('execute clean up code')
    rups.quit_application()


app = rups.App('Hallo Thar', menu=['Print Something', 'On/Off Test', 'Clean Quit'], quit_button=None)
app.run()
