<?php
ini_set('display_errors', 'stderr');


define("PARAM_ERROR", 10);
define("MISSING_HEADER_ERROR", 21);
define("OPERATION_CODED_ERROR", 22);
define("OTHER_ERROR", 23);
///////////////////////////////////////HELPER FUNCTIONS////////////////////////////////////////////
/**
 * @brief function for printing help on stdin after user uses the --help argument
 * @return void
 */
function printHelpOnStdin(){
    echo "////////////////// Help for parse.php script //////////////////\n";
    echo "The purpose of this script is to read source code in the IPPcode23 language from STDIN\nand output a XML representation of the code on STDOUT.\nThe script performs a lexical and syntax analysis before outputting.\n";
    echo "\nHow to use:\n";
    echo "php8.1 parse.php [options] < inputFile > outputFile\n";
}

/**
 * @brief function that prints out specific error message on STDOUT
 * @param errorMsg string containing error message
 * @param lineIndex index of line containing error
 * @param exitValue numerical value of error
 * @return void
 */
function printErrorMsg($errorMsg, $lineIndex, $exitValue)
{
    if ($lineIndex != 1) {
            fprintf(STDERR, "Error on line %d\n", $lineIndex + 1);
    }
    fprintf(STDERR, "%s", $errorMsg);
    exit($exitValue);
}

/**
 * @brief function that checks if the correct arguments where used when running script
 * @param $argc
 * @param $argv
 * @return void
 */
function argumentsCheck($argc, $argv){
    if ($argc > 1){
        if($argc == 2) {
            if ($argv[1] == "--help") {
                printHelpOnStdin();
                exit(0);
            } else {
                printErrorMsg("argument doesn't exist, try using --help\n", 1, PARAM_ERROR);
            }
        }
        else{
            printErrorMsg("Wrong number of program arguments\n", 1, PARAM_ERROR);
        }
    }
}

/////////////////////////////////FUNCTIONS FOR XML GENERATION//////////////////////////////////////

/**
 * @brief function that prints instruction using xml object
 * @param $xml xml object
 * @param $order order of instruction
 * @param $arrayOfSourceTokens array containing all tokens
 * @return void
 */
function printXmlInstr($xml, $order, $arrayOfSourceTokens){
        $xml->startElement('instruction');
        $xml->writeAttribute('order', $order);
        $xml->writeAttribute('opcode', strtoupper($arrayOfSourceTokens[0]));

}

/**
 * @brief function that prints out xml operand using xml object
 * @param $xml xml object
 * @param $argumentPosition
 * @param $content string containing xml attribute
 * @param $type od attribute
 * @return void
 */
function printXmlOp($xml, $argumentPosition, $content, $type){
    $xml->startElement($argumentPosition);
    $xml->writeAttribute('type', $type);
    $xml->text($content);
    $xml->endElement();

}

/**
 * @brief Function that prints out xml constant using xml object
 * @param $explodedTokens tokens parsed with @
 * @param $xml xml object
 * @param $tokenIndex line index of token
 * @param $arg number of the argument
 * @param $reg the regex it's supposed to match
 * @return void
 */
function printXmlConstant($explodedTokens, $xml, $tokenIndex, $arg, $reg){
    $stringToFind = $explodedTokens[1];
    if($explodedTokens[0] == "string"){
        $regex = '/([\\\][\d]{3})/';
        $replace = '';
        $stringToFind = preg_replace($regex, $replace, $explodedTokens[1]);
    }
    if($stringToFind == '' && $explodedTokens[0] == "string"){
        $xml->startElement($arg);
        $xml->writeAttribute('type', $explodedTokens[0]);
        $xml->endElement();
    }
    else if(preg_match($reg, $stringToFind)){
        printXmlOp($xml, $arg, $explodedTokens[1], $explodedTokens[0]);
    }
    else{
        printErrorMsg("INVALID CONSTANT\n", $tokenIndex, OTHER_ERROR);
    }
    //todo
}

/**
 * @brief function that checks if token is a constant or not
 * @param $explodedTokens array of tokens parsed by @
 * @param $xml xml object used for printing xml code
 * @param $order order of token
 * @param $tokenIndex index of the line of current token
 * @return void
 */
function constantCheck($explodedTokens, $xml, $order, $tokenIndex){
    $arg = "arg";
    $arg =  $arg . $order;
    if($explodedTokens[0] == "nil"){
        printXmlConstant($explodedTokens, $xml, $tokenIndex, $arg, "/^nil$/");
    }
    else if($explodedTokens[0] == "bool"){
        printXmlConstant($explodedTokens, $xml, $tokenIndex, $arg, "/^(true|false)$/");
    }
    else if($explodedTokens[0] == "int"){
        printXmlConstant($explodedTokens, $xml, $tokenIndex, $arg, "/^[+-]?[0-9]+$/");
    }
    else if($explodedTokens[0] == "string"){
        printXmlConstant($explodedTokens, $xml, $tokenIndex, $arg, "/^[^\\\]+$/");
    }
    else{
        printErrorMsg("INVALID CONSTANT\n", $tokenIndex, OTHER_ERROR);
    }
}

/**
 * @brief function that checks if token is a variable or not
 * @param $arrayOfSourceTokens array containing all tokens
 * @param $xml xml object used for printing xml code
 * @param int $order order of token
 * @param $tokenIndex index of the line of the line of the current token
 * @return void
 */
function variableCheck($arrayOfSourceTokens, $xml, $order, $tokenIndex){
    $arg = "arg";
    $arg =  $arg . $order;

    if(preg_match("/^(LF|TF|GF)@[a-zA-Z_\-\$&%\*!\?][\w\-\$&%\*!\?]*$/", $arrayOfSourceTokens[$order])){
        printXmlOp($xml, $arg, $arrayOfSourceTokens[$order], "var");
    }
    else{
        printErrorMsg("INVALID VARIABLE\n", $tokenIndex, OTHER_ERROR);
    }
}

/**
 * @brief function that checks if token is a label or not
 * @param $arrayOfSourceTokens array containing all tokens
 * @param $xml xml object used for printing xml code
 * @param $tokenIndex index of the line of the current token
 * @return void
 */
function labelCheck($arrayOfSourceTokens, $xml, $tokenIndex){
    if(preg_match("/^[a-zA-Z_\-\$&%\*!\?][\w\-\$&%\*!\?]*$/", $arrayOfSourceTokens[1])){
        printXmlOp($xml, "arg1", $arrayOfSourceTokens[1], "label");
    }
    else{
        printErrorMsg("INVALID LABEL\n", $tokenIndex, OTHER_ERROR);
    }
}

/**
 * @brief function that checks if token is a type or not
 * @param $arrayOfSourceTokens array containing all tokens
 * @param $xml xml object used for printing xml code
 * @param $tokenIndex index of the line of the current token
 * @return void
 */
function typeCheck($arrayOfSourceTokens, $xml, $tokenIndex){
    if(preg_match("/^(nil|bool|int|string)$/", $arrayOfSourceTokens[2])){
        printXmlOp($xml, "arg2", $arrayOfSourceTokens[2], "type");
    }
    else{
        printErrorMsg("INVALID TYPE\n", $tokenIndex, OTHER_ERROR);
    }
}
/**
 * @brief function that checks if token is a symbol or not
 * @param $arrayOfSourceTokens array containing all tokens
 * @param $xml xml object used for printing xml code
 * @param int $order order of token
 * @param $tokenIndex index of the line of the line of the current token
 * @return void
 */
function symbolCheck($arrayOfSourceTokens, $xml, $order, $tokenIndex){
    $explodedTokens = explode('@', $arrayOfSourceTokens[$order], 2);
    if(count($explodedTokens) == 2){
        if($explodedTokens[0] == "GF" || $explodedTokens[0] == "LF" || $explodedTokens[0] == "TF"){
            variableCheck($arrayOfSourceTokens, $xml, $order, $tokenIndex);
        }
        else{
            constantCheck($explodedTokens, $xml, $order, $tokenIndex);
        }
    }
    else{
        printErrorMsg("INVALID SYMBOL\n", $tokenIndex, OTHER_ERROR);
    }
}

/**
 * @brief the following functions have the same parameters,
 * they are used for printing specific arguments and operands of instructions
 * @param $arrayOfSourceTokens array of all tokens
 * @param $xml xml object used for printing xml code
 * @param $order order of instruction
 * @param $tokenIndex index of line of current instruction
 * @return void
 */
function instrWith0Arg($arrayOfSourceTokens, $xml, $order, $tokenIndex){
    if(count($arrayOfSourceTokens) != 1){
        printErrorMsg("Wrong argument count", $tokenIndex, OTHER_ERROR);
    }
    else{
        printXmlInstr($xml, $order, $arrayOfSourceTokens);
    }

}

function instrWith1Var($arrayOfSourceTokens, $xml, $order, $tokenIndex){
    if(count($arrayOfSourceTokens) != 2){
        printErrorMsg("Wrong argument count", $tokenIndex, OTHER_ERROR);
    }
    printXmlInstr($xml, $order, $arrayOfSourceTokens);
    variableCheck($arrayOfSourceTokens, $xml, 1, $tokenIndex);
}


function instrWith1Label($arrayOfSourceTokens, $xml, $order, $tokenIndex){
    if(count($arrayOfSourceTokens) != 2){
        printErrorMsg("Wrong argument count", $tokenIndex, OTHER_ERROR);
    }
    printXmlInstr($xml, $order, $arrayOfSourceTokens);
    labelCheck($arrayOfSourceTokens, $xml, $tokenIndex);
}
function instrWith1Symbol($arrayOfSourceTokens, $xml, $order, $tokenIndex){
    if(count($arrayOfSourceTokens) != 2){
        printErrorMsg("Wrong argument count", $tokenIndex, OTHER_ERROR);
    }
    printXmlInstr($xml, $order, $arrayOfSourceTokens);
    symbolCheck($arrayOfSourceTokens, $xml, 1, $tokenIndex);
}

function instrWith1SymbolAnd1Var($arrayOfSourceTokens, $xml, $order, $tokenIndex){
    if(count($arrayOfSourceTokens) != 3){
        printErrorMsg("Wrong argument count", $tokenIndex, OTHER_ERROR);
    }
    printXmlInstr($xml, $order, $arrayOfSourceTokens);
    variableCheck($arrayOfSourceTokens, $xml, 1, $tokenIndex);
    symbolCheck($arrayOfSourceTokens, $xml, 2, $tokenIndex);
}
function instrWith2SymbolsAnd1Var($arrayOfSourceTokens, $xml, $order, $tokenIndex){
    if(count($arrayOfSourceTokens) != 4){
        printErrorMsg("Wrong argument count", $tokenIndex, OTHER_ERROR);
    }
    printXmlInstr($xml, $order, $arrayOfSourceTokens);
    variableCheck($arrayOfSourceTokens, $xml, 1, $tokenIndex);
    symbolCheck($arrayOfSourceTokens, $xml, 2, $tokenIndex);
    symbolCheck($arrayOfSourceTokens, $xml, 3, $tokenIndex);
}
function instrWith1VarAnd1Type($arrayOfSourceTokens, $xml, $order, $tokenIndex){
    if(count($arrayOfSourceTokens) != 3){
        printErrorMsg("Wrong argument count", $tokenIndex, OTHER_ERROR);
    }
    printXmlInstr($xml, $order, $arrayOfSourceTokens);
    variableCheck($arrayOfSourceTokens, $xml, 1, $tokenIndex);
    typeCheck($arrayOfSourceTokens, $xml, $tokenIndex);
}
function instrWith1LabelAnd2Symbols($arrayOfSourceTokens, $xml, $order, $tokenIndex){
    if(count($arrayOfSourceTokens) != 4){
        printErrorMsg("Wrong argument count", $tokenIndex, OTHER_ERROR);
    }
    printXmlInstr($xml, $order, $arrayOfSourceTokens);
    labelCheck($arrayOfSourceTokens, $xml, $tokenIndex);
    symbolCheck($arrayOfSourceTokens, $xml, 2, $tokenIndex);
    symbolCheck($arrayOfSourceTokens, $xml, 3, $tokenIndex);

}
/////////////////////////////////////////MAIN BODY OF SCRIPT///////////////////////////////////////////


//checking if user input "--help" argument or not
argumentsCheck($argc, $argv);
//Variable for checking if the IPPcode23 header is found, variable "order" to index the lines
$ippCodeHeader = false;
$order = 0;


//setting new xml object with XMLWriter lib
$xml = new XMLWriter();
$xml->openMemory();
$xml->startDocument('1.0', 'utf-8');
$xml->setIndent(1);
$xml->startElement('program');
$xml->writeAttribute('language', 'IPPcode23');
$lines = file("php://stdin");



//triming white spaces and comments
for($tokenIndex = 0; $tokenIndex < count($lines); $tokenIndex++){
    $trim = '/#(.*)/';
    $replace = '';
    $lines[$tokenIndex] = preg_replace($trim, $replace, $lines[$tokenIndex]);
    $lines[$tokenIndex] = trim($lines[$tokenIndex]);
}


//main part of script going through the source code
for($tokenIndex = 0; $tokenIndex < count($lines); $tokenIndex++) {
    if ($lines[$tokenIndex] != '') {
        //splitting the source code using whitespaces
        $arrayOfSourceTokens = preg_split('/\s+/', $lines[$tokenIndex]);

        //checking correct header input
        if($ippCodeHeader){
            if(strtoupper($arrayOfSourceTokens[0]) == ".IPPCODE23"){
                echo("MORE THAN 1 HEADERS");
                exit(22);
            }
        }

        //checking if header is missing or not
        if (!$ippCodeHeader) {
            if (strtoupper($arrayOfSourceTokens[0]) == ".IPPCODE23") {
                $ippCodeHeader = true;
            } else {
                echo("wrong structure of source code: missing .IPPcode23 header\n");
                exit(21);
            }
        } else {


            //switch for calling specific instruction depending on the arguments of and instruction
            $order++;
            switch (strtoupper($arrayOfSourceTokens[0])) {
                //one word instructions
                case 'CREATEFRAME':
                case 'PUSHFRAME':
                case 'POPFRAME':
                case 'RETURN':
                case 'BREAK':
                    instrWith0Arg($arrayOfSourceTokens, $xml, $order, $tokenIndex);
                    break;
                //1 variable instructions
                case 'POPS':
                case 'DEFVAR':
                    instrWith1Var($arrayOfSourceTokens, $xml, $order, $tokenIndex);
                    break;
                case 'CALL':
                case 'LABEL':
                case 'JUMP':
                    instrWith1Label($arrayOfSourceTokens, $xml, $order, $tokenIndex);
                    break;
                //1 symbol instruction
                case 'PUSHS':
                case 'WRITE':
                case 'EXIT':
                case 'DPRINT':
                    instrWith1Symbol($arrayOfSourceTokens, $xml, $order,$tokenIndex);
                    break;
                //1 variable and 1 symbol instruction
                case 'MOVE':
                case 'INT2CHAR':
                case 'STRLEN':
                case 'TYPE':
                case 'NOT':
                instrWith1SymbolAnd1Var($arrayOfSourceTokens, $xml,$order,$tokenIndex);
                    break;
                //1 variable and 2 symbols instruction
                case 'ADD':
                case 'SUB':
                case 'MUL':
                case 'IDIV':
                case 'LT':
                case 'GT':
                case 'EQ':
                case 'AND':
                case 'OR':
                case 'STRI2INT':
                case 'CONCAT':
                case 'CONCAT':
                case 'GETCHAR':
                case 'SETCHAR':
                    instrWith2SymbolsAnd1Var($arrayOfSourceTokens, $xml, $order,$tokenIndex);
                    break;
                //1 variable and 1 type instruction
                case 'READ':
                    instrWith1VarAnd1Type($arrayOfSourceTokens, $xml, $order, $tokenIndex);
                    break;
                //1 label and 2 symbols instruction
                case 'JUMPIFEQ':
                case 'JUMPIFNEQ':
                    instrWith1LabelAnd2Symbols($arrayOfSourceTokens, $xml, $order, $tokenIndex);
                    break;
                //error
                default:
                    printErrorMsg("UNKNOWN INSTRUCTION\n", $tokenIndex, OTHER_ERROR);
                    break;
            }
            $xml->endElement();
        }
    }
}
    //ending and printing xml code on stdout
    $xml->endElement();
    $xml->endDocument();
    file_put_contents("php://output", trim($xml->outputMemory()));
    $xml->flush();
?>