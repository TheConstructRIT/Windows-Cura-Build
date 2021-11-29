"""
Zachary Cook

Assembles Cura from the sources.
Must be run on Windows.
"""

import os
import requests
import shutil
import subprocess
import tarfile
import zipfile
from distutils.dir_util import copy_tree


BUILD_REQUIREMENTS = {
    "Visual Studio 2019 C++ Build Tools": {
        "file": "C:\Program Files (x86)\Microsoft Visual Studio\\2019\Community\VC\Auxiliary\Build\\vcvars64.bat",
        "description": "Visual Studio 2019 with \"Desktop development with C++\" selected and installed.",
    },
    "Visual Studio 2015 Build Tools (V140)": {
        "file": "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\\vcvarsall.bat",
        "description": "Visual Studio 2019 with \"MSVC v140 - VS 2015 C++ build tools (v14.00)\" selected and installed under \"Installaction details\".",
    },
    "Visual Studio Windows 8.1 SDK": {
        "file": "C:\Program Files (x86)\Microsoft SDKs\Windows\\v8.1A\\bin\\NETFX 4.5.1 Tools",
        "description": "Windows 8.1 SDK. Download from: https://developer.microsoft.com/en-us/windows/downloads/sdk-archive/",
    },
    "MinGW": {
        "path": "x86_64-w64-mingw32-c++.exe",
        "description": "MinGW installed and in the system PATH. Must be installed as x64 with posix for threading. Download from: https://sourceforge.net/projects/mingw-w64/files/Toolchains%20targetting%20Win32/Personal%20Builds/mingw-builds/installer/mingw-w64-install.exe/download",
    },
    "CMake": {
        "path": "cmake.exe",
        "description": "CMake installed and in the system PATH. Download from: https://cmake.org/download/",
    },
    "Subversion": {
        "path": "svn.exe",
        "description": "Subversion installed and in the system PATH. SlikSVN is a quick way to install it: https://sliksvn.com/download/",
    },
}


"""
Checks the requirements for compiling.
"""
def checkRequirements():
    # Check for Window.
    if os.name != "nt":
        print("Windows is required for building dependencies.")
        exit(-1)

    # Check the installed software.
    missingSoftware = 0
    print("Checking the software requirements")
    for name in BUILD_REQUIREMENTS.keys():
        requirement = BUILD_REQUIREMENTS[name]
        print(name)
        print("\t" + requirement["description"])

        # Check for a file existing.
        if "file" in requirement.keys():
            print("\tFile being looked for: " + requirement["file"])
            if os.path.exists(requirement["file"]):
                print("\tRequirement met: Yes")
            else:
                print("\tRequirement met: No")
                missingSoftware += 1

        # Check for a file in PATH existing.
        if "path" in requirement.keys():
            print("\tFile in PATH being looked for: " + requirement["path"])
            pathFileFound = False
            for path in os.environ["PATH"].split(";"):
                if os.path.exists(os.path.join(path, requirement["path"])):
                    pathFileFound = True
            if pathFileFound:
                print("\tRequirement met: Yes")
            else:
                print("\tRequirement met: No")
                missingSoftware += 1

    # Stop if a requirement is missing.
    if missingSoftware != 0:
        print("Not all requirements met.")
        exit(-1)

"""
Performs a list of commands with CMD.
"""
def runCmd(workingDirectory, commands, file=None):
    commands.append("exit")
    initialCommand = ["cmd"]
    if file is not None:
        initialCommand.append("/k")
        initialCommand.append(file)
    commandPromptProcess = subprocess.Popen(initialCommand, cwd=workingDirectory, stdin=subprocess.PIPE)
    for command in commands:
        commandPromptProcess.stdin.write((command + "\n").encode())
    commandPromptProcess.communicate()
    commandPromptProcess.wait()
    if commandPromptProcess.returncode != 0:
        exit(commandPromptProcess.returncode)
"""
Performs a build with the given commands that requires NMake.
"""
def performNMakeBuild(workingDirectory, commands):
    runCmd(workingDirectory, commands, "C:\Program Files (x86)\Microsoft Visual Studio\\2019\Community\VC\Auxiliary\Build\\vcvars64.bat")

"""
Downloads and extracts an archive.
"""
def downloadArchive(extractedPath, url):
    # Remove the existing folder.
    if os.path.exists(extractedPath):
        shutil.rmtree(extractedPath)

    # Create the directory.
    if not os.path.exists(os.path.dirname(extractedPath)):
        os.makedirs(os.path.dirname(extractedPath))

    # Download the file.
    downloadPath = extractedPath + ".tar.gz"
    if not os.path.exists(downloadPath) and not os.path.exists(extractedPath):
        response = requests.get(url)
        with open(downloadPath, "wb") as file:
            file.write(response.content)

    # Extract the file.
    if not os.path.exists(extractedPath):
        file = tarfile.open(downloadPath)
        file.extractall(extractedPath)
        file.close()

    # Move the directory up.
    while len(os.listdir(extractedPath)) == 1:
        subDirectory = os.path.join(extractedPath, os.listdir(extractedPath)[0])
        shutil.move(subDirectory, extractedPath + "-tmp")
        shutil.rmtree(extractedPath)
        shutil.move(extractedPath + "-tmp", extractedPath)

    # Delete the download.
    if os.path.exists(downloadPath):
        os.remove(downloadPath)

"""
Builds the dependencies for Cura.
"""
def buildDependencies(version):
    # Determine the directories.
    curaBuildDirectory = os.path.realpath("download\\" + version + "\\cura-build-environment")
    curaEngineDirectory = os.path.realpath("download\\" + version + "\\CuraEngine")
    curaInstallDirectory = os.path.realpath("CuraPortable")
    if os.path.exists(curaInstallDirectory):
        shutil.rmtree(curaInstallDirectory)

    # Download the build environment.
    if not os.path.exists(curaBuildDirectory):
        downloadArchive(curaBuildDirectory, "https://api.github.com/repos/Ultimaker/Cura-Build-Environment/tarball/master")

    # Run the build for Cura.
    performNMakeBuild(curaBuildDirectory, [
        "set cbe_src_dir=" + curaBuildDirectory,
        "set cbe_install_dir=" + curaInstallDirectory,
        "cd %cbe_src_dir%",
        "mkdir build",
        "cd build",
        "..\env_win64.bat",
        "cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=%cbe_install_dir% -DCMAKE_PREFIX_PATH=%cbe_install_dir% -G \"NMake Makefiles\" ..",
        "nmake",
    ])

    if not os.path.exists(os.path.join(curaInstallDirectory, "CuraEngine.exe")):
        # Download Cura Engine.
        if not os.path.exists(curaEngineDirectory):
            downloadArchive(curaEngineDirectory, "https://api.github.com/repos/Ultimaker/CuraEngine/tarball/" + version)

        # Run the build for Cura Engine.
        performNMakeBuild(curaEngineDirectory, [
            "set ARCUS_DIR=" + os.path.join(curaInstallDirectory, "lib", "cmake", "Arcus").replace("/", "\\"),
            "set PROTOBUF_MINGW_SRC=" + os.path.join(curaBuildDirectory, "build", "Protobuf-MinGW-prefix", "src", "Protobuf-MinGW").replace("/", "\\"),
            "set PROTOBUF_MINGW_INSTALL=" + curaInstallDirectory.replace("/", "\\"),
            "mkdir install_dir",
            "mkdir build && cd build",
            "cmake -DCMAKE_INSTALL_PREFIX=../install_dir -DCMAKE_BUILD_TYPE=Release -DArcus_DIR=%ARCUS_DIR% -DPROTOBUF_SRC_ROOT_FOLDER=%PROTOBUF_MINGW_SRC% -DPROTOBUF_LIBRARY=%PROTOBUF_MINGW_INSTALL%/lib/libprotobuf.a -DProtobuf_INCLUDE_DIR=%PROTOBUF_MINGW_INSTALL%/include -DPROTOBUF_PROTOC_EXECUTABLE=%PROTOBUF_MINGW_INSTALL%/bin/protoc.exe -DPROTOC=%PROTOBUF_MINGW_INSTALL%/bin/protoc.exe -G \"MinGW Makefiles\" ..",
            "mingw32-make",
            "mingw32-make install",
        ])

        # Copy CuraEngine.
        shutil.copy(os.path.join(curaEngineDirectory, "install_dir", "bin", "CuraEngine.exe"), os.path.join(curaInstallDirectory, "CuraEngine.exe"))

"""
Adds Cura files to the environment.
"""
def addCuraFiles(version):
    # Create the download directory.
    downloadsDirectory = os.path.realpath("download/" + version)
    curaInstallDirectory = os.path.realpath("CuraPortable")
    if not os.path.exists(downloadsDirectory):
        os.makedirs(downloadsDirectory)

    # Download Cura.
    print("Downloading and extracting Cura.")
    downloadArchive(os.path.join(downloadsDirectory, "Cura-Download"), "https://api.github.com/repos/Ultimaker/Cura/tarball/" + version)
    if not os.path.exists(os.path.join(curaInstallDirectory, "cura_app.py")):
        copy_tree(os.path.join(downloadsDirectory, "Cura-Download"), curaInstallDirectory)

    # Download Uranium.
    print("Downloading and extracting Uranium.")
    downloadArchive(os.path.join(downloadsDirectory, "Uranium"), "https://api.github.com/repos/Ultimaker/Uranium/tarball/" + version)

    # Download the FDM material definitions.
    print("Downloading and extracting FDM material definitions.")
    downloadArchive(os.path.join(downloadsDirectory, "FDMMaterials") , "https://api.github.com/repos/Ultimaker/fdm_materials/tarball/" + version)
    if not os.path.exists(os.path.join(curaInstallDirectory, "resources", "materials")):
        shutil.copytree(os.path.join(downloadsDirectory, "FDMMaterials"), os.path.join(curaInstallDirectory, "resources", "materials"))

    # Copy the Uranium plugin files.
    print("Copying Uranium plugin files.")
    uraniumBaseDirectory = os.path.join(downloadsDirectory, "Uranium")
    copy_tree(os.path.join(uraniumBaseDirectory, "plugins"), os.path.join(curaInstallDirectory, "plugins"))

    # Copy the Uranium resource files.
    print("Copying Uranium resource files.")
    copy_tree(os.path.join(uraniumBaseDirectory, "resources"), os.path.join(curaInstallDirectory, "resources"))

    # Copy the Uranium module.
    print("Copying UM module.")
    if not os.path.exists(os.path.join(curaInstallDirectory, "lib", "UM")):
        shutil.copytree(os.path.join(uraniumBaseDirectory, "UM"), os.path.join(curaInstallDirectory, "lib", "UM"))

    # Create a script to open it.
    print("Creating batch script to launch Cura.")
    if not os.path.exists(os.path.join(curaInstallDirectory, "launch.py")):
        shutil.copy("resources/launch.py", os.path.join(curaInstallDirectory, "launch.py"))
    if not os.path.exists(os.path.join(curaInstallDirectory, "launch.bat")):
        with open(os.path.join(curaInstallDirectory, "launch.bat"), "w") as file:
            file.write("bin\\python.exe launch.py")


# Run the program.
if __name__ == '__main__':
    # Check the requirements.
    checkRequirements()

    # Prompt for the version.
    version = input("Input a version (like 4.4). Press enter for the latest.\n")
    if version.strip() == "":
        version = "master"
    print("Building Cura (" + version + ")")

    # Build the dependencies.
    if os.path.exists("CuraPortable"):
        print("Dependencies already built.")
    else:
        buildDependencies(version)

    # Add the Cura files.
    addCuraFiles(version)