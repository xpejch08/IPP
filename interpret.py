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

class symTable:


class interpret:
    def __init__(self, arrayOfAllLabels, input):
        self.symtable = symTable()
        self.arrayOfAllLabels =  arrayOfAllLabels
        self.stack = []
        self.instructionCount = 0
        self.input = input


    instruction_dictionary = {
        "MOVE": ["variable", "symbol"],
        "CREATEFRAME": [None],
        "PUSHFRAME": [None],
        "POPFRAME": [None],
        "DEFVAR": [None],
        "CALL": ["label"],
        "RETURN": [None],
        "PUSHS": ["symbol"],
        "POPS": ["variable"],
        "ADD": ["variable", "symbol", "symbol"],
        "SUB": ["variable", "symbol", "symbol"],
        "MUL": ["variable", "symbol", "symbol"],
        "IDIV": ["variable", "symbol", "symbol"],
        "LT": ["variable", "symbol", "symbol"],
        "GT": ["variable", "symbol", "symbol"],
        "EQ": ["variable", "symbol", "symbol"],
        "AND": ["variable", "symbol", "symbol"],
        "OR": ["variable", "symbol", "symbol"],
        "NOT": ["variable", "symbol", "symbol"],
        "INT2CHAR": ["variable", "symbol"],
        "STRI2INT": ["variable", "symbol", "symbol"],
        "READ": ["variable", "type"],
        "WRITE": ["symbol"],
        "CONCAT": ["variable", "symbol", "symbol"],
        "STRLEN": ["variable", "symbol"],
        "GETCHAR": ["variable", "symbol", "symbol"],
        "SETCHAR": ["variable", "symbol", "symbol"],
        "TYPE": ["variable", "symbol"],
        "LABEL": ["label"],
        "JUMP": ["label"],
        "JUMPIFEQ": ["label", "symbol", "symbol"],
        "JUMPIFNEQ": ["label", "symbol", "symbol"],
        "EXIT": ["symbol"],
        "DPRINT": ["symbol"],
        "BREAK": [None]
    }


class xmlRead:
    xmlOrder = 0

    def __init__(self, sourceFile):
        if (sourceFile != None):
            try:
                tree = ET.parse(sourceFile)

            except:
                printError("Error: can't open file for reading\n", 11)

            try:
                self.root = tree.getroot()

            except:
                printError("Error: invalid xml format\n", 31)
        else:
            tree = input()
            try:
                self.root = ET.fromstring(tree)
            except:
                printError("Error: invalid xml format\n", 31)

    def checkOrder(self, order):
        if (order == None):
            printError("Error: missing order of instruction\n", 32)

        try:
            tmp = int(order)
        except:
            printError("Error: cannot convert order to int, wrong format of instruction order\n", 32)

        if (int(order) < 0):
            printError("Error: instruction order is invalid\n", 32)

        if (self.xmlOrder < int(order)):
            self.xmlOrder = order;
            return True;
        else:
            printError("Error: instruction order is invalid", 32)

    def opcodeGetter(self, instruction):
        return instruction.attrib.get('opcode')

    def xmlCheck(self):
        if self.root.tag != "program" or self.root.attrib.get('language') != "IPPcode23":
            printError("Error: invalid xml program tag\n", 31)
        if self.root.findall('arg1') or self.root.findall('arg2') or self.root.findall('arg3'):
            printError("Error: invalid xml program attribute(s)\n", 31)


class commandLineArguments:

    def argsProcedure(self):
        helpParameter = False
        inputParameter = None
        sourceFileParameter = None
        commandLineArguments = sys.argv
        firstArgumentSkip = False
        if len(sys.argv) < 3:
            printError("Error: wrong number of arguments\n", 10)

        for arguments in commandLineArguments:
            if firstArgumentSkip:
                if arguments.find('--source=') != -1:
                    sourceFile = arguments.replace('--source=', '')
                elif arguments.find('--input') != -1:
                    input = arguments.replace('--input=', '')
                elif arguments.find('--help') != -1:
                    helpParameter = True
                else:
                    printError("Error: in command line arguments\n", 10)
            firstArgumentSkip = True

        if helpParameter and (sourceFileParameter != None and inputParameter != None):
            print("Error: --help was used with a different argument\n", 10)

        if helpParameter:
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

        if sourceFileParameter == None and inputParameter == None:
            print("Error: not even one mandatory argument was used\n", 10)

        return sourceFileParameter, inputParameter


def howToSort(ins):
    return int(ins.attrib.get('order'))


class frame:
    scope = {0: "GF",
             1: "LF",
             2: "TF"}

    def __init__(self, type):
        self.type = type
        self.content = {}
        self.length = 0


def orderGetterAndChecker(instruction):
    return int(instruction.attrib.get('order'))


def runProgram(sourceFile, inputFile):
    readXml = xmlRead(sourceFile)
    listOfAllInstructions = []
    arrayOfAllLabels = {}
    order = 0

    readXml.xmlCheck()

    for instruction in readXml.root.iter('instruction'):
        listOfAllInstructions.append(instruction)

    listOfAllInstructions.sort(key=orderGetterAndChecker)

    for instruction in listOfAllInstructions:
        if not readXml.checkOrder(instruction.attrib.get('order')):
            printError("Error: missing order of instruction\n", 32)

        if instruction.attrib.get('opcode').upper() == "LABEL":
            if instruction.find('arg1').text in arrayOfAllLabels:
                printError("Error: Label redefinition occurred\n", 52)
            else:
                arrayOfAllLabels[instruction.find('arg1').text] = order

    order += 1


# main function

if __name__ == '__main__':
    # checking command line arguments
    argumentsCheck = commandLineArguments()
    argumentsCheck.argsProcedure()
    sourceFile, inputFile = argumentsCheck.getSourceAndInput()

    runProgram(sourceFile, inputFile)
