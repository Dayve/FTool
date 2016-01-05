#!/usr/bin/python3

import yaml
import os
import re
import sys
import time
from datetime import date
from datetime import datetime


# TODO:
# - divide code
# - create FileList class
# - handle performing actions
# - clean up the code


# Colored output: ------------------------------------------------------------------------------

Cols = {
    "black"   : '\033[30m',
    "red"     : '\033[31m',
    "green"   : '\033[32m',
    "orange"  : '\033[33m',
    "blue"    : '\033[34m',
    "purple"  : '\033[35m',
    "cyan"    : '\033[36m',
    "l_grey"  : '\033[37m',
    "d_grey"  : '\033[90m',
    "l_red"   : '\033[91m',
    "l_green" : '\033[92m',
    "yellow"  : '\033[93m',
    "l_blue"  : '\033[94m',
    "pink"    : '\033[95m',
    "l_cyan"  : '\033[96m',

    "END"     : '\033[0m',
}

def printc(colorCaption_tuples, endchar):
    for tup in colorCaption_tuples:
        print("%s%s%s" % (Cols[tup[0]], tup[1], Cols["END"]), end='')
    print("", end=endchar)


# Attribute classes: ------------------------------------------------------------------------------
class ConfigAttrib:
    def __init__(self, attribute):
        self.filenameOp, self.filename = attribute['name'].split(' ', 1) if 'name' in attribute else ['','']
        self.ext = attribute['ext'] if 'ext' in attribute else ''

        # Get modification time's and size's: inequality operator, number, unit
        self.sizeOp, self.sizeNum, self.sizeUnit = attribute['size'].split() if 'size' in attribute else ['','','']
        self.modOp, self.modNum, self.modUnit = attribute['mod'].split() if 'mod' in attribute else ['','','']


class FileWithAttrib:
    def __init__(self, filePathAndName):
        # Extract file's name and extension:
        slashPos = filePathAndName.rfind(os.path.sep)
        dotPos = filePathAndName.rfind('.')

        self.filename = filePathAndName[slashPos+1 : dotPos]
        self.ext = filePathAndName[dotPos:]

        # Get file's size:
        self.size = {
            'B' : os.stat(filePathAndName).st_size,
            'kB' : os.stat(filePathAndName).st_size/(10**3),
            'MB' : os.stat(filePathAndName).st_size/(10**6),
            'GB' : os.stat(filePathAndName).st_size/(10**9)
        }

        # And modification time:
        modTimestamp = os.path.getctime(filePathAndName)

        self.mod = {
            'days' : (date.today() - date.fromtimestamp(modTimestamp)).days,
            'weeks' : (date.today() - date.fromtimestamp(modTimestamp)).days/7
        }


# Checking for attributes: -------------------------------------------------------------------------

def checkIfFulfillsAttribute(filePathAndName, attribute):
    fulfills = []

    configAttr = ConfigAttrib(attribute)
    fileAttr = FileWithAttrib(filePathAndName)

    # Extension:
    if configAttr.ext != '':
        if fileAttr.ext == configAttr.ext:
            fulfills.append(True)
        else:
            fulfills.append(False)

    # Filename:
    if configAttr.filename != '':                   # Skip if empty
        if configAttr.filenameOp == 'contains':
            if configAttr.filename in fileAttr.filename:
                fulfills.append(True)
            else:
                fulfills.append(False)

        elif configAttr.filenameOp == 'is':
            if configAttr.filename == fileAttr.filename:
                fulfills.append(True)
            else:
                fulfills.append(False)

        elif configAttr.filenameOp == 'doesnt_contain':
            if configAttr.filename not in fileAttr.filename:
                fulfills.append(True)
            else:
                fulfills.append(False)

    # Size:
    if configAttr.sizeNum != '':                   # Skip if empty
        if configAttr.sizeOp == 'over':
            if fileAttr.size[configAttr.sizeUnit] >= int(configAttr.sizeNum):
                fulfills.append(True)
            else:
                fulfills.append(False)

        elif configAttr.sizeOp == 'is':
            if fileAttr.size[configAttr.sizeUnit] == int(configAttr.sizeNum):
                fulfills.append(True)
            else:
                fulfills.append(False)

        elif configAttr.sizeOp == 'under':
            if fileAttr.size[configAttr.sizeUnit] <= int(configAttr.sizeNum):
                fulfills.append(True)
            else:
                fulfills.append(False)

    # Modification time:
    if configAttr.modNum != '':                   # Skip if empty
        if configAttr.modOp == 'over':
            if fileAttr.mod[configAttr.modUnit] >= int(configAttr.modNum):
                fulfills.append(True)
            else:
                fulfills.append(False)

        elif configAttr.modOp == 'is':
            if fileAttr.mod[configAttr.modUnit] == int(configAttr.modNum):
                fulfills.append(True)
            else:
                fulfills.append(False)

        elif configAttr.modOp == 'under':
            if fileAttr.mod[configAttr.modUnit] <= int(configAttr.modNum):
                fulfills.append(True)
            else:
                fulfills.append(False)

    for b in fulfills:
        if b == False:
            return False

    return True


class FileList:             # TODO
    def __init__(self):
        # [(max(len(re.sub(folder + os.path.sep, '', element)) for element in queue) + columnsPadding) for queue in nonEmptyLists.values()]
        pass


# Load settings: -----------------------------------------------------------------------------------

printc([("yellow", " => Reading 'config.yaml'...")], '\n')

try:
    with open("config.yaml", 'r') as configFile:
        printc([("l_grey", ' '*4 + "Done")], '\n')
        dataMap = yaml.safe_load(configFile)
        configFile.close()

except IOError:
    printc([("red", ' '*4 + "Can't open config file.")], '\n')
    sys.exit()


# Look up for files: -------------------------------------------------------------------------------

# Length (number of characters) in the longest path:
maxPathLen = max(len(folder) for folder in dataMap['folders'])

printc([("yellow", " => Chosen folders:")], '\n')

# Set up for folder identifying:
folderIDs = {}
ID = 1

# Some unimportant padding variables:
path_labelPadding = 2
columnsPadding = 2

for folder in dataMap['folders']:
    # Show full path to the current folder, as given in config file:
    printc([("l_grey", ' '*3 + "-> " + folder.ljust(maxPathLen + path_labelPadding))], '')

    if os.path.exists(folder):
        # Make the list of all the files in the current folder and its subdirectories:
        fileList = []

        for currentPath, subdirs, files in os.walk(folder):
            for filename in files:
                fileList.append(os.path.join(currentPath, filename))

        if fileList:            # If there are some files in the current folder:

            # Queue files for actions:
            toBeMoved = {}      # file (path & name) : destination path
            toBeCopied = {}     # file (path & name) : destination path
            toBeRemoved = []    # list of files to be removed

            # Go through files and check if a give file fulfills any attribute.
            # If it does, then add it to corresponding list, and search the rules for corresponding actions.
            # Then search the actions, get the right command and save it into proper queue:

            for afile in fileList:
                for attrSetK, attrSetV in dataMap['attributes'].items():
                    if checkIfFulfillsAttribute(afile, attrSetV):
                        for ruleSetK, ruleSetV in dataMap['rules'].items():
                            if ruleSetK == attrSetK:
                                for actionSetK, actionSetV in dataMap['actions'].items():
                                    if actionSetK == ruleSetV:
                                        if type(actionSetV) == dict:

                                            command, destPath = list(actionSetV.keys())[0], list(actionSetV.values())[0]

                                            if command == 'copy':
                                                toBeCopied[afile] = destPath
                                            elif command == 'move':
                                                toBeMoved[afile] = destPath

                                        elif type(actionSetV) == str:
                                            # Assume that this other type is string and the caption is "remove"
                                            toBeRemoved.append(afile)


            # Print out the list of files, but not full, only the first few: (amount specified in config file)
            nonEmptyLists = {}

            labeledLists = {
                "MOVE:" : list(toBeMoved.keys()),
                "COPY:" : list(toBeCopied.keys()),
                "REMOVE:" : toBeRemoved
            }

            # Check for non-empty lists:
            for label, alist in labeledLists.items():
                if alist:
                    nonEmptyLists[label] = alist

            # If there are any non-empty lists calculate column width and length of the longest of them:
            if not nonEmptyLists:
                printc([("orange", '\n'+' '*5+"[Nothing to do here]")], '\n')
            else:
                printc([("l_cyan", "[%d]" % ID)], '\n')
                folderIDs[folder] = ID ; ID += 1

                # TODO/FIXME: colW is the same for each list, but the filenames are not -> solution: FileList class
                colW = max(len(re.sub(folder + os.path.sep, '', element)) for queue in nonEmptyLists.values() for element in queue) + columnsPadding
                longestListLen = max(len(queue) for queue in nonEmptyLists.values())

                # Print out labels for non-empty lists:
                labels = ['MOVE:', 'COPY:', 'REMOVE:']  # <--Order

                print(' '*5, end='')
                for label in labels:
                    if label in nonEmptyLists:
                        printc([("orange", label.ljust(colW))], '')
                print()

                for j in range(longestListLen):
                    print(' '*5, end='')
                    for alist in [nonEmptyLists.get(label) for label in labels if nonEmptyLists.get(label) is not None]:
                        if j >= len(alist):
                            print(' '*colW, end="")
                        else:
                            print(re.sub(folder + os.path.sep, '', alist[j]).ljust(colW), end="")
                    print()
        else:
            printc([("orange", '\n'+' '*5+"[Directory is empty]")], '\n')

    else:
        printc([("red", '\n'+' '*5+"[Directory not found]")], '\n')

    print()


# Perform actions: -------------------------------------------------------------------------------
# TODO


