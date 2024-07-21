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


window = rups.Window('Nothing...', 'ALERTZ')
window.title = 'WINDOWS jk'
window.message = 'Something.'
window.default_text = 'eh'

response = window.run()
print(response)

window.add_buttons('One', 'Two', 'Three')

print(window.run())
