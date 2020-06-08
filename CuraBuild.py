"""
Zachary Cook

Builds the latest version of Cura.
"""

REDISTRIBUTABLES_DOWNLOAD_URL = "https://download.microsoft.com/download/9/3/F/93FCF1E7-E6A4-478B-96E7-D4B285925B00/vc_redist.x86.exe"
CURA_INSTALLER_DOWNLOAD_URL = "https://software.ultimaker.com/cura/Ultimaker_Cura-4.6.1-win64.exe"
CURA_BUILD_LOCATION = "CuraPortable"

_7ZIP_LOCATIONS = [
    "C:/Program Files/7-Zip/7z.exe",
    "C:/Program Files (x86)/7-Zip/7z.exe",
]

DLL_FILE_NAMES = [
    "libgcc_s_seh-1.dll",
    "libgomp-1.dll",
    "libstdc++-6.dll",
    "libwinpthread-1.dll",
]



import os
import shutil
import subprocess
import urllib.request



"""
Find the location of 7-Zip.
"""
def find7ZipLocation():
    # Return the executable if it exists.
    for location in _7ZIP_LOCATIONS:
        if os.path.exists(location):
            return location

    # Return none (not found).
    return None

"""
Runs a process and waits for it to complete.
Exits the program if the exit code isn't 0.
"""
def runProcess(args,currentWorkingDirectory=None):
    # Create the environment.
    environment = os.environ.copy()
    environment["PATH"] = os.path.realpath("python") + ";" + environment["PATH"]

    # Run the process.
    process = subprocess.Popen(args,cwd=currentWorkingDirectory,env=environment)
    process.wait()

    # Exit the program if it failed.
    if process.returncode != 0:
        print("Process returned non-zero exit code; exiting program.")
        exit(process.returncode)

"""
Downloads an archive and extracts it.
"""
def downloadAndExtract(downloadUrl,archiveLocation,extractedLocation):
    # Download the executable.
    if not os.path.exists(archiveLocation):
        urllib.request.urlretrieve(downloadUrl,archiveLocation)

    # Extract the files.
    if not os.path.exists(extractedLocation):
        runProcess([find7ZipLocation(),"x",archiveLocation,"-o./" + extractedLocation,"-y"])

"""
Copies the missing files from a directory to another.
"""
def mergeDirectory(sourceDirectory,targetDirectory):
    sourceDirectory = os.path.realpath(sourceDirectory)
    targetDirectory = os.path.realpath(targetDirectory)
    if os.path.exists(sourceDirectory):
        for file in os.listdir(sourceDirectory):
            sourceFile = os.path.join(sourceDirectory,file)
            targetFile = os.path.join(targetDirectory,file)
            if os.path.isdir(sourceFile):
                mergeDirectory(sourceFile,targetFile)
            elif not os.path.exists(targetFile):
                if not os.path.exists(targetDirectory):
                    os.makedirs(targetDirectory)
                shutil.copy(sourceFile,targetFile)
    else:
        shutil.copytree(sourceDirectory,targetDirectory)


if __name__ == '__main__':
    # Check if 7-Zip is installed.
    if find7ZipLocation() is None:
        print("7-Zip was not found in any of the following:")
        for location in _7ZIP_LOCATIONS:
            print("\t" + location)
        print("Please install it to run it. https://www.7-zip.org/download.html")
        exit(1)

    # Prompt for the version.
    version = input("Input a version (like 4.4). Press enter for the latest.\n")
    if version == "":
        version = "master"
        print("Building Cura (latest version)")
    else:
        print("Building Cura (" + version + ")")

    # Create the downloads directory.
    downloadsDirectory = "download/" + version
    if not os.path.exists(downloadsDirectory):
        os.makedirs(downloadsDirectory)

    # Download the Cura installer.
    print("Downloading and extracting Cura installer.")
    downloadAndExtract(CURA_INSTALLER_DOWNLOAD_URL,os.path.join(downloadsDirectory,"CuraInstaller.exe"),os.path.join(downloadsDirectory,"CuraInstaller"))

    # Download Cura.
    print("Downloading and extracting Cura.")
    downloadAndExtract("https://github.com/Ultimaker/Cura/archive/" + version + ".zip",os.path.join(downloadsDirectory,"Cura.zip"),os.path.join(downloadsDirectory,"Cura-Download"))
    if not os.path.exists(CURA_BUILD_LOCATION):
        shutil.copytree(os.path.join(downloadsDirectory,"Cura-Download","Cura-" + version),CURA_BUILD_LOCATION)

    # Download Uranium.
    print("Downloading and extracting Uranium.")
    downloadAndExtract("https://github.com/Ultimaker/Uranium/archive/" + version + ".zip",os.path.join(downloadsDirectory,"Uranium.zip"),os.path.join(downloadsDirectory,"Uranium"))

    # Download the FDM material definitions.
    print("Downloading and extracting FDM material definitions.")
    downloadAndExtract("https://github.com/Ultimaker/fdm_materials/archive/" + version + ".zip",os.path.join(downloadsDirectory,"FDMMaterials.zip"),os.path.join(downloadsDirectory,"FDMMaterials"))
    if not os.path.exists(os.path.join(CURA_BUILD_LOCATION,"resources","materials")):
        shutil.copytree(os.path.join(downloadsDirectory,"FDMMaterials","fdm_materials-" + version),os.path.join(CURA_BUILD_LOCATION,"resources","materials"))

    # Fetch the redistributables installer.
    print("Downloading the redistributables installer.")
    redistributableDownloadLocation = os.path.join(downloadsDirectory,"vc_redist.x86.exe")
    redistributableInstallLocation = os.path.join(CURA_BUILD_LOCATION,"vc_redist.x86.exe")
    if not os.path.exists(redistributableDownloadLocation):
        urllib.request.urlretrieve(REDISTRIBUTABLES_DOWNLOAD_URL,redistributableDownloadLocation)
    if not os.path.exists(redistributableInstallLocation):
        shutil.copy(redistributableDownloadLocation,redistributableInstallLocation)

    # Copy the Python install.
    print("Copying Python install.")
    if not os.path.exists(os.path.join(CURA_BUILD_LOCATION,"python")):
        shutil.copytree("precompiled/python",os.path.join(CURA_BUILD_LOCATION,"python"))

    # Update PIP.
    print("Updating PIP.")
    runProcess([os.path.join(CURA_BUILD_LOCATION,"python","python.exe"),"-m","pip","install","--upgrade","pip"])

    # Add the PIP libraries.
    print("Installing the PIP Python libraries.")
    runProcess([os.path.join(CURA_BUILD_LOCATION,"python","python.exe"),"-m","pip","install","numpy","scipy","cryptography","colorlog","netifaces","zeroconf","pyserial","PyQt5==5.10","requests"])

    # Add the shapely module.
    print("Installing Shapely module.")
    shapelyLocation = "precompiled/Shapely/Shapely-1.6.4.post2-cp35-cp35m-win32.whl"
    runProcess([os.path.join(CURA_BUILD_LOCATION,"python","python.exe"),"-m","pip","install",shapelyLocation])

    # Copy the Uranium plugin files.
    print("Copying Uranium plugin files.")
    uraniumBaseDirectory = os.path.join(downloadsDirectory,"Uranium","Uranium-" + version)
    mergeDirectory(os.path.join(uraniumBaseDirectory,"plugins"),os.path.join(CURA_BUILD_LOCATION,"plugins"))

    # Copy the Uranium resource files.
    print("Copying Uranium resource files.")
    mergeDirectory(os.path.join(uraniumBaseDirectory,"resources"),os.path.join(CURA_BUILD_LOCATION,"resources"))

    # Copy the Uranium module.
    print("Copying UM module.")
    if not os.path.exists(os.path.join(CURA_BUILD_LOCATION,"python","Lib","UM")):
        shutil.copytree(os.path.join(uraniumBaseDirectory,"UM"),os.path.join(CURA_BUILD_LOCATION,"python","Lib","UM"))

    # Copy the Arcus module.
    print("Copying Arcus module.")
    if not os.path.exists(os.path.join(CURA_BUILD_LOCATION,"python","Lib","site-packages","_Arcus.lib")):
        shutil.copy("precompiled/Arcus/_Arcus.lib",os.path.join(CURA_BUILD_LOCATION,"python/Lib/site-packages/_Arcus.lib"))
    if not os.path.exists(os.path.join(CURA_BUILD_LOCATION,"python","Lib","site-packages","Arcus.pyd")):
        shutil.copy("precompiled/Arcus/Arcus.pyd",os.path.join(CURA_BUILD_LOCATION,"python","Lib","site-packages","Arcus.pyd"))

    # Copy the Savitar module.
    print("Copying Savitar module.")
    if not os.path.exists(os.path.join(CURA_BUILD_LOCATION,"python","Lib","site-packages","_Savitar.lib")):
        shutil.copy("precompiled/Savitar/_Savitar.lib",os.path.join(CURA_BUILD_LOCATION,"python","Lib","site-packages","_Savitar.lib"))
    if not os.path.exists(os.path.join(CURA_BUILD_LOCATION,"python","Lib","site-packages","Savitar.pyd")):
        shutil.copy("precompiled/Savitar/Savitar.pyd",os.path.join(CURA_BUILD_LOCATION,"python","Lib","site-packages","Savitar.pyd"))

    # Copy the sip module.
    print("Copying sip module.")
    shutil.copy("precompiled/sip/sip.pyd",os.path.join(CURA_BUILD_LOCATION,"python","Lib","site-packages","sip.pyd"))

    # Copy the CuraEngine.
    print("Copying CuraEngine.")
    if not os.path.exists(os.path.join(CURA_BUILD_LOCATION,"CuraEngine.exe")):
        shutil.copy(os.path.join(downloadsDirectory,"CuraInstaller","CuraEngine.exe"),os.path.join(CURA_BUILD_LOCATION,"CuraEngine.exe"))

    # Copy the DLLs.
    print("Copying DLLs.")
    for dllFileName in DLL_FILE_NAMES:
        if not os.path.exists(os.path.join(CURA_BUILD_LOCATION,dllFileName)):
            shutil.copy(os.path.join(downloadsDirectory,"CuraInstaller",dllFileName),os.path.join(CURA_BUILD_LOCATION,dllFileName))

    # Create a script to open it.
    print("Creating batch script to launch Cura.")
    if not os.path.exists(os.path.join(CURA_BUILD_LOCATION,"launch.bat")):
        with open(os.path.join(CURA_BUILD_LOCATION,"launch.bat"),"w") as file:
            file.write("python\\python.exe cura_app.py")