import sys
import time

IS_MAC = sys.platform == 'darwin'
IS_WIN = sys.platform == 'win32'
if IS_MAC:
    import rumps as rups
elif IS_WIN:
    import ruwps as rups
else:
    print('Linux not supported!')  # We really also need rulps! ;-)
    sys.exit(1)


rups.debug_mode(True)  # turn on command line logging information for development - default is off

@rups.clicked("About")
def about(sender):
    sender.title = 'NOM' if sender.title == 'About' else 'About'  # can adjust titles of menu items dynamically
    rups.alert("This is a cool app!")

@rups.clicked("Arbitrary", "Depth", "It's pretty easy")  # very simple to access nested menu items
def does_something(sender):
    my_data = {'poop': 88}
    rups.notification(title='Hi', subtitle='There.', message='Friend!', sound=does_something.sound, data=my_data)
does_something.sound = True

@rups.clicked("Preferences")
def not_actually_prefs(sender):
    if not sender.icon:
        sender.icon = 'level_4.bmp' if IS_WIN else 'level_4.png'
    sender.state = not sender.state
    does_something.sound = not does_something.sound

@rups.timer(4)  # create a new thread that calls the decorated function every 4 seconds
def write_unix_time(sender):
    print('Hi', sender)
    with app.open('times', 'a') as f:  # this opens files in your app's Application Support folder
        f.write('The unix time now: {}\n'.format(time.time()))

@rups.clicked("Arbitrary")
def change_statusbar_title(sender):
    app.title = 'Hello World' if app.title != 'Hello World' else 'World, Hello'

@rups.notifications
def my_notifications(notification):  # function that reacts to incoming notification dicts
    print('CALL', notification)

# functions don't have to be decorated to serve as callbacks for buttons
# this function is specified as a callback when creating a MenuItem below
def onebitcallback(sender):
    print(4848484)

if __name__ == "__main__":
    app = rups.App("My Toolbar App", title='World, Hello')

    app.menu = [
        rups.MenuItem('About', icon='pony.bmp' if IS_WIN else 'pony.jpg', dimensions=(18, 18)),  # can specify an icon to be placed near text
        'Preferences',
        None,  # None functions as a separator in your menu
        {
            'Arbitrary':
            {
                "Depth": ["Menus", "It's pretty easy"],
                "And doesn't": ["Even look like Objective C", rups.MenuItem("One bit", callback=onebitcallback)]
            }
        },
        None
    ]

    app.run()
