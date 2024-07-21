import sys

IS_MAC = sys.platform == 'darwin'
IS_WIN = sys.platform == 'win32'
if IS_MAC:
    import rups as rups
elif IS_WIN:
    import ruwps as rups
else:
    print('Linux not supported!')  # We really also need rulps! ;-)
    sys.exit(1)


@rups.clicked('Testing')
def tester(sender):
    sender.state = not sender.state

class SomeApp(rups.App):
    def __init__(self):
        super(SomeApp, self).__init__(type(self).__name__, menu=['On', 'Testing'])
        rups.debug_mode(True)

    @rups.clicked('On')
    def button(self, sender):
        sender.title = 'Off' if sender.title == 'On' else 'On'
        rups.Window("I can't think of a good example app...").run()

if __name__ == "__main__":
    SomeApp().run()
