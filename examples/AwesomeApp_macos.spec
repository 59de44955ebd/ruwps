# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['example_class_new_style.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['_bootlocale'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AwesomeApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AwesomeApp',
)
app = BUNDLE(
    coll,
    name='AwesomeApp.app',
    icon='app.icns',
    bundle_identifier=None,
    info_plist={
        'LSUIElement': True,
        'CFBundleShortVersionString': '0.1.0',
    },
)
