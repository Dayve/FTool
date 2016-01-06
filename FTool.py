#!/usr/bin/python3

import yaml
import os
import shutil
import re
import sys
import time
from datetime import date
from datetime import datetime


# Colored output: --------------------------------------------------------------------------------------------

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


# Attribute classes: -----------------------------------------------------------------------------------------

class ConfigAttrib:
    def __init__(self, attribute):
        self.filenameOp, self.filename = attribute['name'].split(' ', 1) if 'name' in attribute else ['','']
        self.ext = attribute['ext'] if 'ext' in attribute else ''

        # Get inequality operator, number and unit for modification time and size:
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


# Checking for attributes: -----------------------------------------------------------------------------------

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

    # TODO: D.R.Y.
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


# Check the command line arguments: --------------------------------------------------------------------------

printOnly = '-p' in sys.argv


# Load the settings: -----------------------------------------------------------------------------------------

printc([("yellow", " => Reading 'config.yaml'...")], '\n')

try:
    with open("config.yaml", 'r') as configFile:
        printc([("l_grey", ' '*4 + "Done")], '\n')
        dataMap = yaml.safe_load(configFile)
        configFile.close()

except IOError:
    printc([("red", ' '*4 + "Can't open/find config file.")], '\n')
    sys.exit()


# Look up for files: -----------------------------------------------------------------------------------------

# Length (number of characters) in the longest path:
maxPathLen = max(len(folder) for folder in dataMap['folders'])

printc([("yellow", " => Chosen folders:")], '\n')

# Set up for folder identifying:
folderIDs = {}
ID = 1

# Tasks which will be performed after showing lists:
tasks = {}

# Some unimportant padding variables:
path_labelPadding = 2
columnsPadding = 6

for folder in dataMap['folders']:
    # Show the full path to current folder, as given in the config file:
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

            # Go through files and check if a given file fulfills any attribute.
            # If it does, then add it to the corresponding list, and search the rules for corresponding actions.
            # Then search the actions, get the right command and save it into the proper queue:

            # Check if those files fulfill any "attributes": -------------------------------------------------

            for afile in fileList:
                for attrSetK, attrSetV in dataMap['attributes'].items():
                    if checkIfFulfillsAttribute(afile, attrSetV):
                        # Search for the rules matching with attribute:
                        for ruleSetK, ruleSetV in dataMap['rules'].items():
                            if ruleSetK == attrSetK:
                                if ruleSetV == 'remove':
                                    toBeRemoved.append(afile)
                                else:
                                    # Else we have to do with dictionary-type action:
                                    for actionSetK, actionSetV in dataMap['actions'].items():
                                        if actionSetK == ruleSetV:
                                            if type(actionSetV) == dict:

                                                # Get data from one-item anonymous dictionary:
                                                command, destPath = list(actionSetV.keys())[0], list(actionSetV.values())[0]

                                                if command == 'copy':
                                                    toBeCopied[afile] = destPath
                                                elif command == 'move':
                                                    toBeMoved[afile] = destPath


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

            if not nonEmptyLists:
                printc([("orange", '\n'+' '*5+"[Nothing to do here]")], '\n')
            else:
                # Show what we have to do: -------------------------------------------------------------------

                # Save the task list: (order matters and is important here)
                tasks[folder] = (toBeMoved, toBeCopied, toBeRemoved)

                # Show folder ID:
                printc([("l_cyan", "[%d]" % ID)], '\n')
                folderIDs[ID] = folder ; ID += 1

                # Calculate a column width (based on the lenghts of filenames that will be displayed) for every list and the length of the longest list:
                # (Came out a little illegible tho...)
                colW =  {label : (max([len(re.sub(folder + os.path.sep, '', element)) for element in queue[:dataMap['lines']]]) + columnsPadding) for (label, queue) in nonEmptyLists.items()}
                longestListLen = max(len(queue) for queue in nonEmptyLists.values())

                # Print out labels for non-empty lists:
                labels = ['MOVE:', 'COPY:', 'REMOVE:']  #(order matters)

                print(' '*5, end='')
                for label in labels:
                    if label in nonEmptyLists:
                        printc([("orange", label.ljust(colW[label]))], '')
                print()

                # Print out the lists themselves:
                positionsLeft = {label : 0 for label in labels}     # Number of files that are not displayed
                nuff = False                                        # Boolean for checking if we already displayed enough

                for j in range(longestListLen):
                    print(' '*5, end='')

                    # The list below is constructed that way for the elements to remain in the order:
                    # (The if clause is there, because .get will return "None" if the key is not in the dictionary)
                    for (label, alist) in [(label, nonEmptyLists.get(label)) for label in labels if nonEmptyLists.get(label) is not None]:
                        if j >= len(alist):
                            print(' '*colW[label], end="")
                        else:
                            print(re.sub(folder + os.path.sep, '', alist[j]).ljust(colW[label]), end="")

                            # We're supposed to print out the amount of files specified in the config file as 'lines':
                            if j+1 >= dataMap['lines']:
                                nuff = True
                                positionsLeft[label] = len(alist)-(j+1)
                    print()

                    if nuff:
                        break

                # Print out the information about the amount of remaining (not displayed) files:
                wereAnyRemaining = False
                print(' '*5, end='')

                for label in labels:
                    if label in nonEmptyLists:
                        if positionsLeft[label] > 0:
                            printc([("orange", "And %d other(s)".ljust(colW[label]) % positionsLeft[label])], '')
                            wereAnyRemaining = True
                        else:
                            print(' '*colW[label], end="")
                if wereAnyRemaining:
                    print()

        else:
            printc([("l_green", '\n'+' '*5+"[Directory is empty]")], '\n')

    else:
        printc([("red", '\n'+' '*5+"[Directory not found]")], '\n')

    print()


# Ask: -------------------------------------------------------------------------------------------------------

printc([("yellow", " => Choose the actions to be perfored now (enter a letter):")], '\n')
printc([("l_grey", ' '*4 + "[A]ll  [NUMBER]-th folder only  [N]one  [M]ove  [C]opy  [R]emove  ->")], '')
choice = input()
print()     # In case user decides to redirect output to file


# Perform actions: -------------------------------------------------------------------------------------------

# Check if the user's input is a number (ID):
try:
    givenID = int(choice)
    if givenID in folderIDs:
        byID = True
    else:
        choice = 'N'

except ValueError:
    givenID = 0
    byID = False


if choice != 'N':
    # Find the longest paths' lengths: (for print-only mode)
    if printOnly:
        maxPathL = max(len(path) for t3Tuple in tasks.values() for path in list(t3Tuple[0].keys()) + list(t3Tuple[0].keys()))

    # Perform actions: (or just print them out)
    for tFolder, t3Tuple in tasks.items():
        if choice in ['A','a','M','m'] or (byID and tFolder == folderIDs[givenID]):
            for afile, itsDest in t3Tuple[0].items():   # toBeMoved dictionary
                if printOnly:
                    print(' '*4 + "MOVE:   %s to %s" % (afile.ljust(maxPathL), itsDest))
                else:
                    shutil.move(afile, itsDest)

        if choice in ['A','a','C','c'] or (byID and tFolder == folderIDs[givenID]):
            for afile, itsDest in t3Tuple[1].items():   # toBeCopied dictionary
                if printOnly:
                    print(' '*4 + "COPY:   %s to %s" % (afile.ljust(maxPathL), itsDest))
                else:
                    shutil.copy(afile, itsDest)

        if choice in ['A','a','R','r'] or (byID and tFolder == folderIDs[givenID]):
            for filename in t3Tuple[2]:                 # toBeRemoved list
                if printOnly:
                    print(' '*4 + "REMOVE: %s" % filename)
                else:
                    os.remove(filename)


