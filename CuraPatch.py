"""
Zachary Cook

Attempts to patch the Cura install.
"""

import os
import importlib.util
import shutil

PATCH_FILE_NAME = "patch.py"



"""
Imports a module from a file.
From: https://stackoverflow.com/questions/4383571/importing-files-from-different-folder
"""
def importFromFile(module_name,file_path):
    spec = importlib.util.spec_from_file_location(module_name,file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

"""
Returns if a patch can be applied.
"""
def canApplyPatch(patchName):
    pacthDirectory = os.path.join("patches",patchName)
    assumedFilesDirectory = os.path.join(pacthDirectory,"assumed")
    replaceFilesDirectory = os.path.join(pacthDirectory,"replace")
    invalidFiles,missingfiles,alreadyPatchedFiles = [],[],[]

    # Checks if a file can be applied.
    def checkApplyFile(location):
        expectedFile = os.path.join(assumedFilesDirectory,location)
        patchFile = os.path.join(replaceFilesDirectory,location)
        actualFile = os.path.join("CuraPortable",location)
        if os.path.isfile(expectedFile):
            if not os.path.exists(actualFile):
                # Add the missing file if the actual doesn't exist.
                missingfiles.append(actualFile)
            else:
                # Read the files.
                patchSource = ""
                with open(expectedFile) as file:
                    expectedSource = file.read()
                with open(actualFile) as file:
                    actualSource = file.read()
                if os.path.exists(patchFile):
                    with open(patchFile) as file:
                        patchSource = file.read()

                # Add the file.
                if actualSource == patchSource:
                    alreadyPatchedFiles.append(actualFile)
                elif actualSource != expectedSource:
                    invalidFiles.append(actualFile)
        else:
            for file in os.listdir(expectedFile):
                checkApplyFile(os.path.join(location,file))

    # Determine the invalid files.
    if os.path.exists(assumedFilesDirectory):
        for file in os.listdir(assumedFilesDirectory):
            checkApplyFile(file)

    # Print the already patched files.
    if len(alreadyPatchedFiles) > 0:
        print("Patch files already applied: " + patchName)
        for file in alreadyPatchedFiles:
            print("\t" + file)

    # Return false if the files don't match.
    if len(invalidFiles) != 0 and len(missingfiles) != 0:
        print("Unable to apply patch: " + patchName)
        for file in invalidFiles:
            print("\tExpected and actual files don't match: " + file)
        for file in missingfiles:
            print("\tFile expected to exist is missing: " + file)

        return False

    # Print and return if any patches can't be applied.
    patchFile = os.path.join("patches",patchName,"patch.py")
    if os.path.exists(patchFile):
        patchModuleName = patchName.replace(" ","_") + "_patch"
        patchModule = importFromFile(patchModuleName,patchFile)

        # Check the patch and return false if it can't be applied.
        if hasattr(patchModule,"canApplyPatch") and not patchModule.canApplyPatch():
            print("Patch can't be applied: " + patchName + " (according to " + patchFile + ")")
            return False

    # Return true (can apply).
    return True


"""
Returns if a patch collision exists.
"""
def patchCollisionExists(patches):
    filesToReplace = {}
    collisionsExist = False

    # Adds a file to be replaced.
    def addFileToReplace(patchName,location):
        collisionsExist = False

        # Add the files.
        newFile = os.path.join("patches",patchName,"replace",location)
        replaceFile = os.path.join("CuraPortable",location)
        if os.path.isdir(newFile):
            for file in os.listdir(newFile):
                addFileToReplace(patchName,os.path.join(location,file))
        else:
            if replaceFile in filesToReplace.keys():
                filesToReplace[replaceFile].append(patchName)
                collisionsExist = True
            else:
                filesToReplace[replaceFile] = [patchName]

        # Return if a collision exists.
        return collisionsExist


    # Find the files to change.
    for patchName in patches:
        patchReplaceDirectory = os.path.join("patches",patchName,"replace")
        if os.path.isdir(patchReplaceDirectory):
            for file in os.listdir(patchReplaceDirectory):
                collisionsExist = addFileToReplace(patchName,file) or collisionsExist

    # Print the collisions and return true if they exists.
    if collisionsExist:
        # Print the colliding patches.
        print("Multiple patches change the same files.")
        for fileToReplace in filesToReplace.keys():
            collidingPatches = filesToReplace[fileToReplace]
            if len(collidingPatches) > 1:
                print("\t" + fileToReplace + ": " + str(collidingPatches)[1:-1].replace("'",""))

        # Return true (collisions found).
        return True

    # Return false (no collisions found).
    return False

"""
Applies a patch.
"""
def applyPatch(patchName):
    pacthDirectory = os.path.join("patches",patchName)
    replaceFilesDirectory = os.path.join(pacthDirectory,"replace")

    # Copies files into Cura.
    def copyFiles(file):
        existingFile = os.path.join("CuraPortable",file)
        replaceFile = os.path.join(replaceFilesDirectory,file)

        # Copy the file.
        if os.path.isdir(replaceFile):
            if not os.path.isdir(existingFile):
                os.mkdir(existingFile)
            for subFile in os.listdir(replaceFile):
                copyFiles(os.path.join(file,subFile))
        else:
            if os.path.exists(existingFile):
                os.remove(existingFile)
            shutil.copy(replaceFile,existingFile)

    # Copy the files.
    if os.path.isdir(replaceFilesDirectory):
        for file in os.listdir(replaceFilesDirectory):
            copyFiles(file)

    # Run the file.
    patchFile = os.path.join("patches",patchName,"patch.py")
    if os.path.exists(patchFile):
        patchModuleName = patchName.replace(" ", "_") + "_patch"
        patchModule = importFromFile(patchModuleName, patchFile)

        # Apply the patch.
        if hasattr(patchModule,"applyPatch"):
            patchModule.applyPatch()


if __name__ == '__main__':
    # Return if the patches don't exists.
    if not os.path.exists("patches"):
        print("Patches directory doesn't exist.")
        exit(1)

    # Determine the patches.
    patches = []
    for patchName in os.listdir("patches"):
        if patchName[0] != "." and os.path.isdir(os.path.join("patches",patchName)):
            patches.append(patchName)

    # Check if the patches can be applied.
    canApply = True
    print("Checking patches.")
    for patchName in patches:
        if not canApplyPatch(patchName):
            canApply = False
    if not canApply:
        exit(1)

    # Check if any patch files collide.
    print("Checking for patch collisions.")
    if patchCollisionExists(patches):
        exit(1)

    # Apply the patches.
    for patchName in patches:
        print("Apply patch: " + patchName)
        applyPatch(patchName)
    print("Patches applied.")