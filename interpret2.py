 import xml.etree.ElementTree as ET
 import sys
 import argparse


 def printError(content, errCode):
     print(content, file=sys.stderr)
     sys.exit(errCode)

class frame:

    def __int__(self):
        self.frame = []
        self.frame_len = 0

    def push(self, type: str, value):
        self.frame.append([type, value])
        self.frame_len += 1

    def pop(self):
        if self.frame_len == 0:
            printError("Error: empty frame whilst calling pop\n", 55)
        else:
            self.frame_len -= 1
            return self.frame.pop()
    def empty(self):
        if self.frame_len == 0:
            return True
        else:
            return False
    def peek(self):
        return self.frame[0]
    ##todo fix peek
class instructions:
    def __init__(self, opcode, order):
        self.opcode = opcode
        self.order = order
        self.arguments = []

class arguments:

    def __init__(self, type, name = None, val = None, order = None):
        self.type = type
        self.name = name
        self.val = val
        self.order = order
        self.frame = None
        self.frameSetter()

    def frameSetter(self):
        if self.type == 'var' and self.name is not None:
            self.frame = self.name[:2]

    def nameGetter(self):
        if self.type == 'var' and self.name is not None:
            return self.name[3:]

class var:
    def __init__(self, name, init, val, type):
        self.name = name
        self.init = init
        self.val = val
        self.type = type
        self.slicedName = None
        self.sliceName()

        def sliceName(self):
            if self.name is not None:
                self.slicedName = self.name[:3]

class interpret:

    labelsChecker = []
    orderChecker = []

    def __init__(self):

        self.listOfAllInstructions = []
        self.input = None
        self.isThereAnInput = False
        self.inputLines = 0
        self.source = None
        self.isThereASource = False
        self.openFileFlag = False
        self.inputContent = None


        self.listOfAllLabels = {}
        self.mainFrame = frame()

        ##todo change names

        self.frameChecker = frame()
        self.LF = frame
        self.GF = []
        self.TF = []
        self.TFFlag = False

        self.insNum = 0
        self.xml = None

    def help(self):
        print("IPP project 2 interpret.py")
        print("")
        print("Arguments:")
        print("-optional:")
        print(" --help: prints out this help message")
        print("-mandatory:")
        print("At least one of these parameters has to be used!!!")
        print(" --source=file, where file is the name of th source file")
        print(" --input=file, where file is the name of th input file")
        sys.exit(0)
    def sortAllInstructions(self):
        self.listOfAllInstructions.sort(key = lambda  inst: inst.order)

    def findAllLabels(self):
        insNum = 0
        for instruction in self.listOfAllInstructions:
            if instruction.opCode == 'LABEL':
                label = instruction.args[0]
                if label.value in self.listOfAllLabels:
                    printError("Error: Label is not defined, or Label is being redefined\n", 52)
                self.listOfAllLabels[label.value] = insNum
                insNum += 1

    def checkIppCodeHeader(self):
        if self.xml.tag != 'program' or self.xml.attrib['language'] != 'IPPcode23':
            printError("Error: missing or wrong IppCode23 Header", 32)

    def parseInput(self):
        lines = []
        if(self.isThereASource):
            with open(self.source, 'r') as file:
                rLines = file.readlines()
            for lineIndex in range(len(rLines)):
                if rLines[lineIndex] != '':
                    lines.append(rLines[lineIndex].strip())
        else:
            while True:
                try:
                    line = input()
                    line = line.strip()
                    if line != '':
                        lines.append(line)
                except EOFError:
                    break;
        try:
            self.xml = ET.ElementTree(ET.fromstringlist(lines)).getroot()
        except ET.ParseError:
            printError("Error: problem parsing the xml source code", 31)

    def inputLineGetter(self):
        if self.isThereAnInput:
            if not self.openFileFlag:
                with open(self.input) as file:
                    self.inputContent = file.readlines()
                    for lineIndex in range(len(self.inputContent)):
                        self.inputContent[lineIndex] = self.inputContent[lineIndex]. strip()
                    self.isThereAnInput = True