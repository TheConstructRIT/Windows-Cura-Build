"""
This script is generated to launch Cura without a console window.
pythonw.exe is not included in the build.
"""

# Hide the console window.
import ctypes
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Start Cura.
try:
    import cura_app
except ImportError as e:
    # On clean installs, an import error will occur due to missing DLLs.
    # If this happens, attempt to install them and try again.
    if "DLL load failed" in str(e):
        import os
        import requests
        import subprocess
        
        # Download the installer.
        if not os.path.exists("vc_redist.x64.exe"):
            installResponse = requests.get("https://aka.ms/vs/17/release/vc_redist.x64.exe")
            with open("vc_redist.x64.exe", "wb") as file:
                file.write(installResponse.content)

        # Run the installer.
        process = subprocess.Popen([os.path.realpath(os.path.join(os.path.realpath(__file__), "..", "vc_redist.x64.exe"))])
        process.wait()

        # Re-run the program.
        import cura_app
    else:
        raise e
