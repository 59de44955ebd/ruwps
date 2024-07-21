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
