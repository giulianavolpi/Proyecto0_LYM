import re

# Palabras clave y tokens del lenguaje
KEYWORDS = {"EXEC", "NEW", "VAR", "MACRO", "if", "then", "else", "fi", "do", "od", "rep", "times", "per", "while", "not", "nop", "safeExe"}
COMMANDS = {"M", "R", "C", "B", "c", "b", "P", "J", "G", "turnToMy", "turnToThe", "walk", "jump", "drop", "pick", "grab", "letGo", "pop", "moves"}
CONDITIONS = {"isBlocked?", "isFacing?", "zero?", "not"}

# Identificación de tokens
token_specification = [
    ("NUMBER", r"\d+"),                # Números
    ("ASSIGN", r"="),                  # Asignación
    ("SEMI", r";"),                    # Fin de instrucción
    ("ID", r"[A-Za-z_]\w*"),           # Identificadores
    ("LBRACE", r"{"),                  # Llave izquierda
    ("RBRACE", r"}"),                  # Llave derecha
    ("LPAREN", r"\("),                 # Paréntesis izquierdo
    ("RPAREN", r"\)"),                 # Paréntesis derecho
    ("COMMA", r","),                   # Coma
    ("SKIP", r"[ \t\n]+"),             # Espacios, tabuladores y nuevas líneas (ignorados)
    ("MISMATCH", r"."),                # Cualquier otro carácter
]


token_regex = "|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in token_specification)

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = self.tokenize(code)
        self.current_token = None
        self.next_token()

    def tokenize(self, code):
        for match in re.finditer(token_regex, code):
            token_type = match.lastgroup
            token_value = match.group()
            if token_type == "ID" and token_value in KEYWORDS:
                token_type = token_value
            if token_type != "SKIP":
                yield (token_type, token_value)
        yield ("EOF", None)

    def next_token(self):
        self.current_token = next(self.tokens)

    def match(self, token_type):
        if self.current_token[0] == token_type:
            self.next_token()
        else:
            raise SyntaxError(f"Expected {token_type}, found {self.current_token[0]} at {self.current_token[1]}")


## Hasta aquí Silvia dijo que se puede usar la libreria RE para tokenizar el código

class Parser:

    #Inicializa el parser
    def __init__(self, lexer):
        self.lexer = lexer
        self.variables = {}
        self.macros = {}

    #Analiza el programa y devuelve la respuesta
    def parse(self):
        try:
            self.program()
            return "si"
        except SyntaxError as e:
            print(f"Error de sintaxis: {e}")
            return "no"
            
    #Procesa el programa, mientras el token seleccionado no sea EOF llama a statement
    def program(self):
        while self.lexer.current_token[0] != "EOF":
            self.statement()

    #Define si el token es EXEC o NEW, dependiendo de esto llama a su respectiva función, si no es ninguno da Syntax error
    def statement(self):
        if self.lexer.current_token[0] == "EXEC":
            self.exec_block()
        elif self.lexer.current_token[0] == "NEW":
            self.definition()
        else:
            raise SyntaxError(f"Unexpected token: {self.lexer.current_token[0]}")

    #Comprueba que el token sea EXEC, que las instrucciones estén dentro de {} y luego llama a bloc
    def exec_block(self):
        self.lexer.match("EXEC")
        self.lexer.match("LBRACE")
        self.block()
        self.lexer.match("RBRACE")

    #Se encarga de analizar lo que hay dentro de {}, para cada instrucción se llama a instruction
    def block(self):
        while self.lexer.current_token[0] not in {"RBRACE", "EOF"}:
            self.instruction()
            
    #Procesa una instrucción individual, determina si es un comando, un condicional, una repetición, un loop o una invocación de
    # macro, llama a respectiva la función y si no es ninguno de los anteriores da Syntax error. 
    def instruction(self):
        token_type, token_value = self.lexer.current_token
        if token_type == "ID" and token_value in COMMANDS:
            self.command()
        elif token_type == "if":
            self.if_statement()
        elif token_type == "rep":
            self.repeat_times()
        elif token_type == "while":
            self.while_loop()
        elif token_type in self.macros:
            self.macro_invocation()
        else:
            raise SyntaxError(f"Unknown instruction: {token_value}")
        self.lexer.match("SEMI")

    #Procesa un comando y verifica que tenga la información correcta según el comando en particular
    def command(self):
        token_type, token_value = self.lexer.current_token
        self.lexer.match("ID")
        if token_type in {"J", "G", "turnToMy", "turnToThe", "walk", "jump", "drop", "pick", "grab", "letGo", "pop"}:
            self.lexer.match("LPAREN")
            self.lexer.match("NUMBER")
            self.lexer.match("RPAREN")
        elif token_type == "moves":
            self.lexer.match("LPAREN")
            while self.lexer.current_token[0] != "RPAREN":
                self.lexer.match("ID")
                if self.lexer.current_token[0] == "COMMA":
                    self.lexer.match("COMMA")
            self.lexer.match("RPAREN")

    def command(self):
        token_type, token_value = self.current_token
        self.match("ID")

        if token_value in {"M", "R", "C", "B", "c", "b", "P"}:
            pass       
        elif token_value in {"G"}:
            self.match("LPAREN")
            self.match("NUMBER")  # x-coordinate
            self.match("COMMA")
            self.match("NUMBER")  # y-coordinate
            self.match("RPAREN")

        elif token_value in {"turnToMy"}:
            self.match("LPAREN")
            if self.current_token[1] not in {"left", "right", "back"}:
                raise SyntaxError(f"Invalid direction for turnToMy: {self.current_token[1]}")
            self.match("ID")
            self.match("RPAREN")

        elif token_value in {"turnToThe"}:
            self.match("LPAREN")
            if self.current_token[1] not in {"north", "south", "east", "west"}:
                raise SyntaxError(f"Invalid orientation for turnToThe: {self.current_token[1]}")
            self.match("ID")
            self.match("RPAREN")

        elif token_value in {"J", "walk", "jump", "drop", "pick", "grab", "letGo", "pop"}:
            self.match("LPAREN")
            self.match("NUMBER")
            self.match("RPAREN")

        elif token_value == "moves":
            self.match("LPAREN")
            while self.current_token[0] != "RPAREN":
                if self.current_token[1] not in {"forward", "right", "left", "backward"}:
                    raise SyntaxError(f"Invalid direction in moves: {self.current_token[1]}")
                self.match("ID")
                if self.current_token[0] == "COMMA":
                    self.match("COMMA")
            self.match("RPAREN")

        else:
            raise SyntaxError(f"Unknown command: {token_value}")

    #Procesa un condicional y verifica que tenga la información correcta
    def if_statement(self):
        self.lexer.match("if")
        self.condition()
        self.lexer.match("then")
        self.block()
        if self.lexer.current_token[0] == "else":
            self.lexer.match("else")
            self.block()
        self.lexer.match("fi")

     #Procesa una repetición y verifica que tenga la información correcta
    def repeat_times(self):
        self.lexer.match("rep")
        self.lexer.match("NUMBER")
        self.lexer.match("times")
        self.block()
        self.lexer.match("per")

     #Procesa un ciclo y verifica que tenga la información correcta
    def while_loop(self):
        self.lexer.match("while")
        self.condition()
        self.block()
        self.lexer.match("od")

    #Procesa la invocación de una macro y verifica que tenga la información correcta
    def macro_invocation(self):
        macro_name = self.current_token[1]
        self.match("ID")
        self.match("LPAREN")
        params = []
        while self.current_token[0] != "RPAREN":
            if self.current_token[0] == "ID":
                if self.current_token[1] not in self.variables:
                    raise SyntaxError(f"Undefined variable: {self.current_token[1]}")
            params.append(self.current_token[1])
            self.match("ID" if self.current_token[0].isalpha() else "NUMBER")
            if self.current_token[0] == "COMMA":
                self.match("COMMA")
        self.match("RPAREN")
        print(f"Invocando macro {macro_name} con parámetros {params}")

    #Procesa una condición que puede ir tanto en condicionales como en ciclos
    def condition(self):
        cond = self.lexer.current_token[1]
        self.lexer.match("ID")
        self.lexer.match("LPAREN")
        self.lexer.match("ID")
        self.lexer.match("RPAREN")
        print(f"Condición: {cond}")


        cond = self.current_token[1]
        
        if cond in {"isBlocked?", "isFacing?"}:
            self.match("ID")
            self.match("LPAREN")
            direction_or_orientation = self.current_token[1]
            if cond == "isBlocked?" and direction_or_orientation not in {"left", "right", "front", "back"}:
                raise SyntaxError(f"Invalid direction in {cond}: {direction_or_orientation}")
            elif cond == "isFacing?" and direction_or_orientation not in {"north", "south", "east", "west"}:
                raise SyntaxError(f"Invalid orientation in {cond}: {direction_or_orientation}")
            self.match("ID")
            self.match("RPAREN")
        
        elif cond == "zero?":
            self.match("ID")
            self.match("LPAREN")
            if self.current_token[0] != "ID" and self.current_token[0] != "NUMBER":
                raise SyntaxError(f"Invalid parameter in {cond}: {self.current_token[1]}")
            self.match("ID" if self.current_token[0] == "ID" else "NUMBER")
            self.match("RPAREN")
        
        elif cond == "not":
            self.match("ID")
            self.match("LPAREN")
            self.parse_condition()
            self.match("RPAREN")
        
        else:
            raise SyntaxError(f"Unknown condition: {cond}")

        print(f"Condición: {cond}")

    #Identifica si se trata de una definición de variable o de macro y llama a la respectiva función
    def definition(self):
        self.lexer.match("NEW")
        if self.lexer.current_token[0] == "VAR":
            self.var_definition()
        elif self.lexer.current_token[0] == "MACRO":
            self.macro_definition()

    #Procesa la definición de una variable
    def var_definition(self):
        self.lexer.match("VAR")
        var_name = self.lexer.current_token[1]
        self.lexer.match("ID")
        self.lexer.match("ASSIGN")
        var_value = self.lexer.current_token[1]
        self.lexer.match("NUMBER")
        self.variables[var_name] = var_value
        print(f"Variable {var_name} definida con valor {var_value}")

    #Procesa la definición de una macro
    def macro_definition(self):
        self.lexer.match("MACRO")
        macro_name = self.lexer.current_token[1]
        self.lexer.match("ID")
        self.lexer.match("LPAREN")
        params = []
        while self.lexer.current_token[0] != "RPAREN":
            params.append(self.lexer.current_token[1])
            self.lexer.match("ID")
            if self.lexer.current_token[0] == "COMMA":
                self.lexer.match("COMMA")
        self.lexer.match("RPAREN")
        self.lexer.match("LBRACE")
        self.macros[macro_name] = {"params": params, "body": self.block()}
        self.lexer.match("RBRACE")
        print(f"Macro {macro_name} definida con parámetros {params}")


# Ejemplo de uso:
# El código del lexer y parser debe estar incluido aquí.
# A continuación, agregamos el ejemplo que quieres probar:

code_example = """
NEW VAR one=1;
NEW MACRO goend ()
{
if not (isBlocked?(front))
then { walk(one); goend(); }
else { nop; }
fi;
}
"""

# Correr el Lexer y Parser en el ejemplo:
lexer = Lexer(code_example)
parser = Parser(lexer)

resultado = parser.parse()

print(f"Resultado del análisis sintáctico: {resultado}")



