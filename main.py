import argparse as ap
import xml.etree.ElementTree as ET
import sys
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

class instruction:
    instList = []
    labels = []
    order = []

    def __init__(self, opCode, order):
        self._opCode = opCode
        self._order = int(order)
        self._arguments = [[], [], []]
        type(self).instList.append(self)

    def getOpCode(self):
        return  self._opCode

    def getArguments(self):
        return self._arguments

    instruction_dictionary = {
        "MOVE":
    }

class xmlRead:

    order = 0

    def __init__(self, sourceFile):
        if(sourceFile != None):
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
        if(order == none):
            printError("Error: missing order of instruction\n", 32)

        try:
            tmp = int(order)
        except:
            printError("Error: cannot convert order to int, wrong format of instruction order\n", 32)

class frame:
    scope = {0: "GF",
             1: "LF",
             2: "TF"}
    
    def __init__(self, type):
        self.type = type
        self.content = {}
        self.length = 0

class symbolTable
