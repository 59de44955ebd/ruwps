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

@rups.clicked('Icon', 'On')
def a(_):
    app.icon = 'pony.ico' if IS_WIN else 'pony.jpg'

@rups.clicked('Icon', 'Off')
def b(_):
    app.icon = None

@rups.clicked('Title', 'On')
def c(_):
    app.title = 'Buzz'

@rups.clicked('Title', 'Off')
def d(_):
    app.title = None

app = rups.App('Buzz Application', quit_button=rups.MenuItem('Quit Buzz', key='q'))
app.menu = [
    ('Icon', ('On', 'Off')),
    ('Title', ('On', 'Off'))
]
app.run()
