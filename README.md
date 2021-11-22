# Construct Cura Build
Automation tool for generating Ultimaker Cura from the GitHub
source code to allow for modifications for The Construct @ RIT.

## Setup
Setting up the repository on Windows requires having an
existing Python 3 install and 7-Zip installed. No additional
Python libraries are required.
Note: macOS and Linux are not supported.

## Running
To create a build of Cura from GitHub, run the `CuraAssemble` task.
```
python CuraAssemble.py
```

A version will be prompted. If no version is set, the latest version
from `master` will be used.

To apply patches, set up a `patches` directory and call the following:
```
python CuraPatch.py
```

## Patches
Patches are applied to the source code to try to prevent forking
of a version and attempting to merge changes. Patches are put in
a `patches` directory (not included in the repository). Each patch
is a directory that contains the following:
- `assumed` directory - the files and directories assumed to exist to patch.
- `replace` directory - the files and directories to replace.
- `patch.py` (optional) - script ran to apply additional patches. Can implement:
    - `canApplyPatch` (optional) - returns if the patch can be implemented.
    - `applyPatch` (optional) - applies the patch.