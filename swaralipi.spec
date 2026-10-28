# PyInstaller recipe for the Windows app. Build with:  python tools/build_windows.py
# (one-folder build: starts fast and is less likely to be flagged by antivirus than one-file)

datas = [
    ("assets", "assets"),
    ("data", "data"),
    ("recorder/ui/fonts", "recorder/ui/fonts"),
    ("recorder/ui/icons", "recorder/ui/icons"),
]

a = Analysis(
    ["app.py"],
    datas=datas,
    excludes=["tkinter", "pytest", "PyInstaller", "unittest", "pydoc"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Swaralipi",
    icon="assets/swaralipi.ico",
    console=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="Swaralipi", upx=False)
