# ================================================================== #
# fTool.py - file (re)moving and archive unzipping automation script #
# ================================================================== #

import os
import sys
import shutil
import zipfile
import re


# TODO: Read root directory name from rc file
rootPath = '/home/user/Downloads'


# TODO: Read rules from rc file
rules = {
#   EXTENSION : DESTINATION_PATH/ACTION (Change to whatever you need)
#   MOVING:
    '.mp3' : '/home/user/MP3s',
    '.txt' : '/home/user/Documents/Txts',

#   OTHER:
    '.zip' : '/home/user/Unzipped',
    '.nnn' : 'REMOVE'
};


# Fill the list of all files in rootPath and its subdirectories:
fileList = []

for currentPath, subdirs, files in os.walk(rootPath):
    for filename in files:
        fileList.append(os.path.join(currentPath, filename))

if not fileList:    # List of files, on which we would perform actions is empty
    print("Nothing to do.")
    sys.exit()


# Queue files for actions:
toBeMoved = []
toBeRemoved = []
toBeUnzipped = []

for extension, destPath in rules.items():
    for name in fileList:
        if extension in name:
            if destPath is 'REMOVE':
                toBeRemoved.append(name)

            elif extension is '.zip':
                toBeUnzipped.append(name)

            else:
                toBeMoved.append(name)

allQueues = [toBeMoved, toBeRemoved, toBeUnzipped]


# Ask about actions before performing them:
padding = 6
colW = max(len(re.sub(rootPath, '', name)) for queue in allQueues for name in queue) + padding
longestListLen = max(len(queue) for queue in allQueues)

print("/MOVE:/".ljust(colW) + "/REMOVE:/".ljust(colW) + "/UNZIP:/".ljust(colW))

for i in range(longestListLen):
    for queue in allQueues:
        if not queue or i >= len(queue):
            print(' '*colW, end="")
        else:
            print(re.sub(rootPath, '', queue[i]).ljust(colW), end="")
    print()

decision = input("\nDo you want to perform those actions?\n(y/n to perform all, m/r/u to choose) ")

if decision not in ['y','n','m','r','u']:   # Correct decision if needed
    decision = 'n'


# Move/remove files / unzip archives depending on their name and decision:
if decision is not 'n':
    if decision is 'y' or decision is 'r':
        for name in toBeRemoved:
            os.remove(name)

    if decision is 'y' or decision is 'u':
        for name in toBeUnzipped:
            zipf = zipfile.ZipFile(name)
            zipf.extractall(destPath)
            os.remove(name)

    if decision is 'y' or decision is 'm':
        for extension, destPath in rules.items():
            for name in toBeMoved:
                if extension in name:
                    shutil.move(name, destPath)
                

