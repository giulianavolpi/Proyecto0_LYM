import re

# Palabras clave y tokens del lenguaje
KEYWORDS = {"EXEC", "NEW", "VAR", "MACRO", "if", "then", "else", "fi", "do", "od", "rep", "times", "per", "while", "not", "nop", "balloonsHere"}
COMMANDS = {"M", "R", "C", "B", "c", "b", "P", "J", "G", "turnToMy", "turnToThe", "walk", "jump", "drop", "pick", "grab", "letGo", "pop", "moves", "nop", "move", "safeExe", "balloonsHere"}
PARAMS = {"left", "right", "forward", "back", "backwards"}  # Lista para parámetros específicos de movimiento
CONDITIONS = {"isBlocked?", "isFacing?", "zero?", "not"}
CONSTANTS = {"size", "myX", "myY", "myChips", "myBalloons", "balloonsHere", "chipsHere", "roomForChips"}  # Constantes del robot

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

# Regex para la tokenización
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
            if token_type == "ID" and (token_value in KEYWORDS or token_value in CONSTANTS):
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

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.variables = {}
        self.macros = {}

    def parse(self):
        try:
            self.program()
            return "si"
        except SyntaxError as e:
            print(f"Error de sintaxis: {e}")
            return "no"

    def program(self):
        while self.lexer.current_token[0] != "EOF":
            self.statement()

    def statement(self):
        if self.lexer.current_token[0] == "EXEC":
            self.exec_block()
        elif self.lexer.current_token[0] == "NEW":
            self.definition()
        else:
            raise SyntaxError(f"Unexpected token: {self.lexer.current_token[0]}")

    def exec_block(self):
        self.lexer.match("EXEC")
        self.lexer.match("LBRACE")
        self.block()
        self.lexer.match("RBRACE")

    def block(self):
        instructions = []
        while self.lexer.current_token[0] not in {"RBRACE", "EOF"}:
            instructions.append(self.instruction())

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
        elif token_value in self.macros:
            self.macro_invocation()
        else:
            raise SyntaxError(f"Unknown instruction: {token_value}")
        self.lexer.match("SEMI")

    def command(self):
        token_type, token_value = self.lexer.current_token
        self.lexer.match("ID")
        if token_value in COMMANDS:
            self.lexer.match("LPAREN")
            if token_value == "safeExe":
                # Manejar comandos dentro de safeExe
                inner_command_type, inner_command_value = self.lexer.current_token
                if inner_command_value in COMMANDS:
                    self.command()  # Llamada recursiva para manejar comandos internos
                else:
                    if self.lexer.current_token[0] == "NUMBER":
                        self.lexer.match("NUMBER")
                self.lexer.match("RPAREN")
            else:
                # Manejar parámetros para otros comandos
                while self.lexer.current_token[0] != "RPAREN":
                    if self.lexer.current_token[0] == "ID":
                        param_value = self.lexer.current_token[1]
                        if param_value not in PARAMS and param_value not in self.variables and param_value not in CONSTANTS:
                            raise SyntaxError(f"Undefined variable or constant: {param_value}")
                        self.lexer.match("ID")
                    elif self.lexer.current_token[0] == "NUMBER":
                        self.lexer.match("NUMBER")
                    if self.lexer.current_token[0] == "COMMA":
                        self.lexer.match("COMMA")
                self.lexer.match("RPAREN")

    def if_statement(self):
        self.lexer.match("if")
        self.condition()
        self.lexer.match("then")
        self.lexer.match("LBRACE")
        self.block()
        self.lexer.match("RBRACE")
        if self.lexer.current_token[0] == "else":
            self.lexer.match("else")
            self.lexer.match("LBRACE")
            self.block()
            self.lexer.match("RBRACE")
        self.lexer.match("fi")

    def repeat_times(self):
        self.lexer.match("rep")
        self.lexer.match("NUMBER")
        self.lexer.match("times")
        self.block()
        self.lexer.match("per")

    def while_loop(self):
        self.lexer.match("while")
        self.condition()
        self.block()
        self.lexer.match("od")

    def macro_invocation(self):
        macro_name = self.lexer.current_token[1]
        self.lexer.match("ID")
        self.lexer.match("LPAREN")
        while self.lexer.current_token[0] != "RPAREN":
            if self.lexer.current_token[0] == "ID" and self.lexer.current_token[1] not in self.variables:
                raise SyntaxError(f"Undefined variable: {self.lexer.current_token[1]}")
            self.lexer.match("ID" if self.lexer.current_token[0] == "ID" else "NUMBER")
            if self.lexer.current_token[0] == "COMMA":
                self.lexer.match("COMMA")
        self.lexer.match("RPAREN")
        print(f"Invocando macro {macro_name}")

    def condition(self):
        # Manejar condiciones que pueden incluir 'not' u otros modificadores
        if self.lexer.current_token[1] == "not":
            self.lexer.match("ID")  # 'not' se reconoce como ID en este contexto
        if self.lexer.current_token[1] in CONDITIONS:
            cond = self.lexer.current_token[1]
            self.lexer.match("ID")
            self.lexer.match("LPAREN")
            # Aceptar parámetros dentro de la condición, como identificadores o valores en PARAMS
            if self.lexer.current_token[0] == "ID" or self.lexer.current_token[1] in PARAMS:
                self.lexer.match("ID")
            self.lexer.match("RPAREN")
            print(f"Condición: {cond}")
        else:
            raise SyntaxError(f"Expected condition, found: {self.lexer.current_token[1]}")

    def definition(self):
        self.lexer.match("NEW")
        if self.lexer.current_token[0] == "VAR":
            self.var_definition()
        elif self.lexer.current_token[0] == "MACRO":
            self.macro_definition()

    def var_definition(self):
        self.lexer.match("VAR")
        var_name = self.lexer.current_token[1]
        self.lexer.match("ID")
        self.lexer.match("ASSIGN")
        var_value = self.lexer.current_token[1]
        self.lexer.match("NUMBER")
        self.variables[var_name] = var_value
        print(f"Variable {var_name} definida con valor {var_value}")

    def macro_definition(self):
        self.lexer.match("MACRO")
        macro_name = self.lexer.current_token[1]
        self.lexer.match("ID")
        self.lexer.match("LPAREN")
        while self.lexer.current_token[0] != "RPAREN":
            self.lexer.match("ID")
            if self.lexer.current_token[0] == "COMMA":
                self.lexer.match("COMMA")
        self.lexer.match("RPAREN")
        self.lexer.match("LBRACE")
        self.block()
        self.lexer.match("RBRACE")
        print(f"Macro {macro_name} definida")

# Ejemplo de uso:
code_example = """
EXEC {
    safeExe (walk(1) ) ;
    moves ( left , left , forward , right , back ) ;
}

"""

lexer = Lexer(code_example)
parser = Parser(lexer)
resultado = parser.parse()

print(f"Resultado del análisis sintáctico: {resultado}")






