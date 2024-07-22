import sys

IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'

if IS_WIN:
    import ruwps as rups
    from ctypes import windll
elif IS_MAC:
    import rumps as rups
else:
    print('Linux not supported!')  # We really also need rulps! ;-)
    sys.exit(1)

import json
import os
import subprocess
import traceback

APP_NAME = 'SocksManager'

IS_FROZEN = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
if IS_FROZEN and IS_MAC:
    RES_DIR = os.path.realpath(os.path.join(os.path.dirname(sys.executable), '..', 'Resources'))
else:
    RES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

POLL_PERIOD_SEC = 3
MAX_RECONNECTS = 3

if IS_WIN:
    SSH_BIN = os.path.join(os.environ['SystemRoot'], 'System32', 'OpenSSH', 'ssh.exe')
    if not os.path.isfile(SSH_BIN):
        print('Error: ssh.exe not found')
        sys.exit(2)
    SSH_ASKPASS_BIN = os.path.join(RES_DIR, 'bin', 'askpass.exe')
else:
    SSH_BIN = '/usr/bin/ssh'
    SSH_PASS_BIN = os.path.join(RES_DIR, 'bin', 'sshpass')


class SocksManagerApp(rups.App):

    ########################################
    #
    ########################################
    def __init__(self):
        super().__init__(APP_NAME, icon=os.path.join(RES_DIR, "app.icns") if IS_MAC else None,
                quit_button=None)

        self.connection_dict = {}   # con_id => connection details
        self.reconnects = {}        # con_id => number of reconnects
        self.procs = {}             # con_id => proc

        self.connections_json_file = os.path.join(rups.application_support(self.name), 'connections.json')
        if not os.path.isfile(self.connections_json_file):
            with open(self.connections_json_file, 'w') as f:
                f.write('[]')

        self.load_connections()
        self.create_menu()

    ########################################
    #
    ########################################
    def create_menu(self):
        self.menu.clear()
        menu = []
        for con_id, con in self.connection_dict.items():
            menu_item = rups.MenuItem(con["name"], callback=lambda sender, con_id=con_id:
                    self.toggle_connection(sender, con_id))
            con['menu_item'] = menu_item
            if 'autostart' in con and con['autostart']:
                self.toggle_connection(menu_item, con_id)
            menu.append(menu_item)
        menu.extend([
            None,
            {'Settings': [
                rups.MenuItem('Edit connections.jsons', callback=self.edit_connections),
                rups.MenuItem('Reload connections.json', callback=self.reload_connections),
            ]},
            None,
            rups.MenuItem('Quit', callback=self.quit)
        ])
        self.menu.update(menu)

    ########################################
    #
    ########################################
    @rups.timer(POLL_PERIOD_SEC)
    def poll(self, sender):
        for con_id in list(self.procs.keys()):
            exit_code = self.procs[con_id].poll()
            if exit_code is not None:
                con = self.connection_dict[con_id]
                con['menu_item'].state = 0
                del self.procs[con_id]
                if "reconnect" in con and con["reconnect"] and self.reconnects[con_id] < MAX_RECONNECTS:
                    rups.notification(message=f"Connection {con['name']} got disconnected.\nTrying to reconnect...")
                    self.toggle_connection(con_id)
                else:
                    rups.notification(message=f"Connection {con['name']} got disconnected.")

    ########################################
    #
    ########################################
    def edit_connections(self, sender):
        if IS_WIN:
            windll.Shell32.ShellExecuteW(self.hwnd, 'open', 'notepad.exe', self.connections_json_file, None, 1)
        else:
            subprocess.call(['open', '-a', 'TextEdit', self.connections_json_file])

    ########################################
    #
    ########################################
    def reload_connections(self, _):
        self.load_connections()
        self.create_menu()

    ########################################
    #
    ########################################
    def quit(self, _):
        if len(self.procs.keys()):
            res = rups.alert(
                    title='SOCKS5 Proxies running',
                    message=f'{len(self.procs.keys())} proxies are still running. Do you want to quit them?',
                    ok='Yes',
                    cancel='No')
            print(res)
            if res:
                for proc in self.procs.values():
                    proc.terminate()
        rups.quit_application()

    ########################################
    #
    ########################################
    def load_connections(self):
        self.connection_dict = {}
        self.reconnects = {}
        try:
            with open(self.connections_json_file, 'r') as f:
                connection_list = json.loads(f.read())
            for con_id, row in enumerate(connection_list):
                self.connection_dict[con_id] = row
                self.reconnects[con_id] = 0
        except Exception as e:
            print(e)
            rumps.alert(title='Error in JSON file', message=str(e))

    ########################################
    #
    ########################################
    def toggle_connection(self, sender, con_id):
        con = self.connection_dict[con_id]
        if sender.state:
            sender.state = 0
            self.procs[con_id].terminate()
            del self.procs[con_id]
        else:
            if con["auth"] == "key":
                command = [
                    SSH_BIN,
                    '-o',
                    'StrictHostKeyChecking=no',
                    f"{con['user']}@{con['host']}",
                    '-i',
                    con['key_file'],
                    '-D',
                    f"localhost:{con['port']}",
                    '-N',
                ]
                env = None
            else:
                command = [
                    SSH_BIN,
                    '-o',
                    'StrictHostKeyChecking=no',
                    f"{con['user']}@{con['host']}",
                    '-D',
                    f"localhost:{con['port']}",
                    '-N',
                ]
                if IS_MAC:
                    command = [SSH_PASS_BIN, '-e',] + command
                env = os.environ | ({
                    'SSH_ASKPASS': SSH_ASKPASS_BIN,
                    'SSH_ASKPASS_REQUIRE': 'force',
                    'ASKPASS_PASSWORD': con['password']
                } if IS_WIN else {
                    'SSHPASS': con['password']
                })
            if IS_WIN:
                self.procs[con_id] = subprocess.Popen(command, env = env,
                        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
            else:
                self.procs[con_id] = subprocess.Popen(command, env = env)
            sender.state = 1
            self.reconnects[con_id] = 0


if __name__ == "__main__":
    sys.excepthook = traceback.print_exception
    SocksManagerApp().run()
