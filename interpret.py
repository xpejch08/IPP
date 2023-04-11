import argparse as ap
import xml.etree.ElementTree as ET
import sys
import argparse
import re

"""
error codes:
10 prong command line params
11 - chyba při otevírání vstupních souborů (např. neexistence, nedostatečné oprávnění);
12 - chyba při otevření výstupních souborů pro zápis (např. nedostatečné oprávnění, chyba
při zápisu);

31 wrong xml format
32 wrong xml structure
99 - interní chyba (neovlivněná vstupními soubory či parametry příkazové řádky; např. chyba
alokace paměti).

"""


def printError(content, errCode):
    print(content, file=sys.stderr)
    sys.exit(errCode)


class frame:

    def __init__(self):
        self.frame = []
        self.frame_len = 0

    def push(self, typeF: str, value):
        self.frame.append([typeF, value])
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

    def __init__(self, type, name=None, val=None, order=None):
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
    def __init__(self, name = None, init = False, val = None, type = None):
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
        self.LF = frame()
        self.GF = []
        self.TF = []
        self.TFFlag = False

        self.insNum = 0
        self.xml = None

        self.commandLineArguments()
        self.parseInput()
        self.checkIppCodeHeader()
        self.ETreeParser()
        self.sortAllInstructions()
        self.findAllLabels()
        self.runner()

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
        self.listOfAllInstructions.sort(key=lambda inst: inst.order)

    def findAllLabels(self):
        insNum = 0
        for instruction in self.listOfAllInstructions:
            if instruction.opcode == 'LABEL':
                label = instruction.arguments[0]
                if label.val in self.listOfAllLabels:
                    printError("Error: Label is not defined, or Label is being redefined\n", 52)
                self.listOfAllLabels[label.val] = insNum
                insNum += 1

    def checkIppCodeHeader(self):
        if self.xml.tag != 'program' or self.xml.attrib['language'] != 'IPPcode23':
            printError("Error: missing or wrong IppCode23 Header", 32)

    def parseInput(self):
        lines = []
        if self.isThereASource:
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
                    break
        try:
            self.xml = ET.ElementTree(ET.fromstringlist(lines)).getroot()
        except ET.ParseError:
            printError("Erroframe: problem parsing the xml source code", 31)

    def inputLineGetter(self):
        if self.isThereAnInput:
            if not self.openFileFlag:
                with open(self.input) as file:
                    self.inputContent = file.readlines()
                    for lineIndex in range(len(self.inputContent)):
                        self.inputContent[lineIndex] = self.inputContent[lineIndex].strip()
                    self.isThereAnInput = True
            if self.inputLines < len(self.inputContent):
                line = self.inputContent[self.inputLines]
                self.inputLines += 1
                return line
            else:
                return None
        else:
            return input()

    def retIntInStr(self, string: str):
        if string[0] in ('-', '+'):
            return string[1:].isdigit()
        return string.isdigit()

    def argumentParser(self, inst: instructions, argument: ET.Element):
        if argument.tag not in ('arg1', 'arg2', 'arg3'):
            printError("Error: wrong structure of source XML\n", 32)
        aOrder = int(argument.tag[3])

        if argument.attrib['type'] == 'var':
            if len(argument.text) < 4 or argument.text[:3] not in ('GF@', 'LF@', 'TF@'):
                printError("Error: invalid XML source format", 31)
            inst.arguments.append(arguments(type='var', name=argument.text, order=aOrder))
        elif argument.attrib['type'] == 'string':
            if argument.text:
                # todo what does this code do
                for lineIndex, substitution in enumerate(argument.text.split("\\")):
                    if lineIndex == 0:
                        argument.text = substitution
                    else:
                        if int(substitution[0:3]) < 0 or int(substitution[0:3]) > 999:
                            printError("Error: wrong operands of XML source code", 53)
                        argument.text = argument.text + chr(int(substitution[0:3])) + substitution[3:]
            argument.text = ''

            inst.arguments.append(arguments(type='string', val=argument.text, order=aOrder))

        elif argument.attrib['type'] == 'int':
            if not argument.text or not self.retIntInStr(argument.text):
                printError("Error: wrong structure of source XML\n", 32)
            inst.arguments.append(arguments(type='int', val=int(argument.text), order=aOrder))

        elif argument.attrib['type'] == 'bool':
            if not argument.text not in ('false', 'true'):
                printError("Error: invalid XML source format\n", 31)
            inst.arguments.append(arguments(type='bool', val=argument.text, order=aOrder))

        elif argument.attrib['type'] == 'nil':
            if not argument.text not in 'nil':
                printError("Error: invalid XML source format\n", 31)
            inst.arguments.append(arguments(type='nil', val='nil', order=aOrder))

        elif argument.attrib['type'] == 'label':
            if not argument.text:
                printError("Error: invalid XML source format\n", 31)
            inst.arguments.append(arguments(type='label', val=argument.text, order=aOrder))

        elif argument.attrib['type'] == 'type':
            if not argument.text not in ('string', 'int', 'bool'):
                printError("Error: invalid XML source format\n", 31)
            inst.arguments.append(arguments(type=argument.text, order=aOrder))

        else:
            printError("Error: wrong structure of source XML\n", 32)

    def frameGetter(self, argument: arguments):
        if argument.frame == 'GF':
            return self.GF
        if argument.frame == 'LF':
            if self.LF.empty():
                printError("Error: empty frame whilst calling pop\n", 55)
                return
            return self.LF.peek()[1]
        if argument.frame == 'TF':
            if not self.TFFlag:
                printError("Error: empty frame whilst calling pop\n", 55)
                return
            return self.TF

    def ETreeParser(self):
        for element in self.xml:
            if element.tag != 'instruction' or 'order' not in element.attrib or 'opcode' not in element.attrib:
                printError("Error: wrong structure of source XML\n", 32)
            if not element.attrib['order'].isdigit():
                printError("Error: wrong structure of source XML\n", 32)
            if not self.retIntInStr(element.attrib['order']):
                printError("Error: wrong structure of source XML\n", 32)
            if int(element.attrib['order']) in self.orderChecker or int(element.attrib['order']) < 1:
                printError("Error: wrong structure of source XML\n", 32)

            self.orderChecker.append(int(element.attrib['order']))
            inst = instructions(element.attrib['opcode'], int(element.attrib['order']))

            for arg in element.iter():
                if arg != element:
                    # todo argumentParser
                    self.argumentParser(inst, arg)
            inst.arguments.sort(key=lambda x: x.order)

            flag = 1
            for arg in inst.arguments:
                if arg.order != flag:
                    printError("Error: wrong structure of source XML\n", 32)
                flag += 1

            self.listOfAllInstructions.append(inst)

    def variableGetter(self, argument):
        frame = self.frameGetter(argument)
        for variable in frame:
            if variable.slicedName == argument.sliceName():
                return variable
        printError("Error: Variable doesn't exist", 54)

    def valueGetter(self, argument: arguments):
        if argument.type == 'var':
            var = self.variableGetter(argument)
            return var.val, var.type, var.init
        elif argument.type in ('string', 'int', 'bool', 'nil'):
            return argument.val, argument.type, True

    def fileChecker(self, path: str):
        try:
            with open(path, 'r') as file:
                pass
        except IOError:
            printError("Error: input file doesn't exist", 11)

    def commandLineArguments(self):
        parse = argparse.ArgumentParser(description='Helper', add_help=False)
        parse.add_argument('--help', dest='help', action='store_true', default=False, help="print this message\n")

        parse.add_argument('--input', type=str, dest='inputFile', default=False, required=False)
        parse.add_argument('--source', type=str, dest='sourceFile', default=False, required=False)
        allArgs = vars(parse.parse_args())

        if allArgs['help'] and not allArgs['inputFile'] and not allArgs['sourceFile']:
            self.help()
            sys.exit(0)
        elif allArgs['help'] and (allArgs['inputFile'] or allArgs['sourceFile']):
            sys.exit(10)
        # neither --input nor --source was set
        elif not (allArgs['inputFile'] or allArgs['sourceFile']):
            sys.exit(10)

        if allArgs['inputFile']:
            self.isThereAnInput = True
            self.fileChecker(allArgs['inputFile'])
            self.input = allArgs['inputFile']

        if allArgs['sourceFile']:
            self.isThereASource = True
            self.fileChecker(allArgs['sourceFile'])
            self.source = allArgs['sourceFile']

    def runner(self):
        while True:
            if self.insNum > len(self.listOfAllInstructions)-1:
                break

            activeInstruction: instructions = self.listOfAllInstructions[self.insNum]
            opcode = activeInstruction.opcode.upper()

            if opcode == 'LABEL':
                self.insNum += 1
            elif opcode == 'DEFVAR':
                argument = activeInstruction.arguments[0]
                frame = self.frameGetter(argument)
                frame.append(var(name=argument.name))
                self.insNum += 1
            elif opcode == 'CREATEFRAME':
                self.TF = []
                self.TFFlag = True
                self.insNum += 1
            elif opcode == 'PUSHFRAME':
                if not self.TFFlag:
                    printError("Error: empty frame before calling pop", 55)
                self.LF.push('frame', self.TF)
                self.TFFlag = False
                self.insNum += 1
            elif opcode == 'READ':
                variable: var = self.variableGetter(activeInstruction.arguments[0])
            else:
                self.insNum += 1

interpret = interpret()