import cx_Freeze
import sys
# import matplotlib

base = None

if sys.platform == 'win32':
    base = "Win32GUI"

executables = [cx_Freeze.Executable("ControllerGUIttk.py", base=base, icon="HJ.ico")]

cx_Freeze.setup(
    name = "ControllerGUI",
    options = {"build_exe": {"packages":["tkinter"], "include_files":["HJ.ico"]}},
    version = "0.01",
    executables = executables
    )