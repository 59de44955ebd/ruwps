import sys
import time

IS_MAC = sys.platform == 'darwin'
IS_WIN = sys.platform == 'win32'
if IS_MAC:
    import rups as rups
elif IS_WIN:
    import ruwps as rups
else:
    print('Linux not supported!')  # We really also need rulps! ;-)
    sys.exit(1)


def timez():
    return time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())

@rups.timer(1)
def a(sender):
    print('%r %r' % (sender, timez()))

@rups.clicked('Change timer')
def changeit(_):
    response = rups.Window('Enter new interval').run()
    if response.clicked:
        global_namespace_timer.interval = int(response.text)

@rups.clicked('All timers')
def activetimers(_):
    print(rups.timers())

@rups.clicked('Start timer')
def start_timer(_):
    global_namespace_timer.start()

@rups.clicked('Stop timer')
def stop_timer(_):
    global_namespace_timer.stop()

if __name__ == "__main__":
    global_namespace_timer = rups.Timer(a, 4)
    rups.App('fuuu', menu=('Change timer', 'All timers', 'Start timer', 'Stop timer')).run()
