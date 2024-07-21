# ruwps
**R**idiculously **U**ncomplicated **W**indows **P**ython **S**ystray apps.

``ruwps`` exposes Winapi functions as Python classes and functions which greatly simplifies the process of creating a system tray application, i.e. an application that is supposed to run in the background and only has a minimal GUI based on menus and simple dialogs. It's a complement to [``rumps``](https://github.com/jaredks/rumps), sharing (mostly) the same API, which allows the fast creation of win/mac cross-platform system tray/statusbar applications based on the same code.

Here a minimal example app:
```python
import ruwps

class AwesomeApp(ruwps.App):
    @ruwps.clicked("Preferences")
    def prefs(self, _):
        rumps.alert("jk! no preferences available!")

    @ruwps.clicked("Silly button")
    def onoff(self, sender):
        sender.state = not sender.state

    @ruwps.clicked("Say hi")
    def sayhi(self, _):
        ruwps.notification("Awesome title", "amazing subtitle", "hi!!1")

if __name__ == "__main__":
    AwesomeApp("Awesome App").run()
```
And here the same app as above, but written in a way so that it runs both in Windows and macOS:
```python
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

class AwesomeApp(rups.App):
    @rups.clicked("Preferences")
    def prefs(self, _):
        rups.alert("jk! no preferences available!")

    @rups.clicked("Silly button")
    def onoff(self, sender):
        sender.state = not sender.state

    @rups.clicked("Say hi")
    def sayhi(self, _):
        rups.notification("Awesome title", "amazing subtitle", "hi!!1")

if __name__ == "__main__":
    AwesomeApp("Awesome App").run()
```

Here the resulting app running in Windows 11:  
![System tray menu in Windows 11](screenshots/systray_menu.png)
![System tray notification in Windows 11](screenshots/systray_notifcation.png)

And here the resulting app in macOS, based on rumps:  
![Statusbar menu and norification in macOS](https://raw.github.com/jaredks/rumps/master/examples/rumps_example.png)

## Installation

Since ``ruwps`` has no dependancies (other than Python 3), no real installation needed, either bundle the ``ruwps`` folder with your local project or copy it to Python's site-packages folder.

## Documentation

The ``ruwps`` API is (almost) the same as for ``rumps``, so you can refer to this documentation: http://rumps.readthedocs.org

But of course there are some differences, since the underlying system APIs differ. Here some of them:
* The app's systray icon is loaded from an .ico file (instead of a .icns file in macOS). If you don't specify a custom icon, at dev time some arbitrary b&w default icon (see screenshots) is used, while in a frozen application the application's main icon (that was passed to pyinstaller) is used instead.
* The Winapi doesn't support automatic icon conversion based the user's light/dark mode, therefor the optional ``template`` argument of the App's constructor works differently in Windows, if it is specified and set to True, the ``icon`` argument has to be a tuple/list of two icon files, and the first is then used in light and the second in dark mode.
* Menu icons (optional) are loaded from .bmp files (instead of .png or .jpg files in macOS). The optional ``dimensions`` argument is ignored.
* In macOS the app can either show an icon or text in the statusbar, while in the Windows system tray it's always an icon. The ``title`` property of the App class instead only determines the icon's tooltip.
* if debug mode is activated and the app is frozen (i.e. there is no console to print to), debug infos are written to the Windows debug console and can be monitored using Sysinternal's [DebugView](https://learn.microsoft.com/en-us/sysinternals/downloads/debugview).