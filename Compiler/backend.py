import subprocess
from static.series import INT, FLOAT, COFRE

#booleano es 0 o 1 pero si hay pedos avisan y lo cambio a True y Flase para que no haya pedos
#MUCHO CUIDADO CON LA INDEXACION, SOLO SE PEUDE CON COFRE E ITEM, PERO NO SE SABE HASTA ESTE PUNTO SI ITEM SI ES LISTA
#TIENEN QUE REVISAR QUE SI ES UN STRING NO HAY BRONCA, PERO SI ES UN NUMERO O BOOLEANO QUE MARQUE ERROR
# LA TRADUCCION (self.errors) Y NO TRATE DE EJECUTAR

class PythonCode:
    def __init__(self, codigo_intermedio):
        self.codigo_intermedio = codigo_intermedio
        self.python_code = '### C MCScript ###\ndef weak_arithmetic(x):\n\ttry:\n\t\treturn float(x)\n\texcept:\n\t\treturn len(x)\n\n'
        self.variables = {}
        self.warnings = []
        self.errors = []

    def translate(self):
        for ins in self.codigo_intermedio:
            code, _ = self._translate_single_ir_instruction(ins, 0)
            self.python_code += code + "\n"

        #varias otras cosas

        self.python_code += "### FIN MCScript ###\n"

    def _translate_single_ir_instruction(self, instruccion, indent_level): #indent pq pues python super imp indent
        parts = instruccion.split(" ", 1)
        opcode = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        def _translate_operand(operand_str, type=None):#a for type aritmetic, c for concat,
            operand_str = operand_str.strip()
            if operand_str in ["true", "false"]: #habria que normalizar esto yo digo que ya directo True False no??
                return "True" if operand_str == "true" else "False"
            elif operand_str in ["encendido", "apagado"]:
                return "True" if operand_str == "encendido" else "False"
            elif operand_str.startswith('"') and operand_str.endswith('"'):
                return operand_str

            try:
                num_val = float(operand_str)
                if num_val == int(num_val):
                    return str(int(num_val))
                else:
                    return str(num_val)
            except ValueError:
                pass #then its a varr

            return operand_str

        translated_line = ""
        is_special_flow = False

        if opcode == "ASSIGN":
            dest, src = [s.strip() for s in args.split("=", 1)]
            translated_line = f"{dest} = {_translate_operand(src)}"
        elif opcode == "ADD":
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1, op2 = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = weak_arithmetic({_translate_operand(op1)}) + weak_arithmetic({_translate_operand(op2)})"
        elif opcode == "SUB":
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1, op2 = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = weak_arithmetic({_translate_operand(op1)}) - weak_arithmetic({_translate_operand(op2)})"
        elif opcode == "MUL":
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1, op2 = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = weak_arithmetic({_translate_operand(op1)}) * weak_arithmetic({_translate_operand(op2)})"
        elif opcode == "DIV":
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1, op2 = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = weak_arithmetic({_translate_operand(op1)}) / weak_arithmetic({_translate_operand(op2)})"
        elif opcode == "POW":
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1, op2 = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = weak_arithmetic({_translate_operand(op1)}) ** weak_arithmetic({_translate_operand(op2)})"
        elif opcode == "MOD":
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1, op2 = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = weak_arithmetic({_translate_operand(op1)}) % weak_arithmetic({_translate_operand(op2)})"
        elif opcode in ["EQ", "LT", "GT", "LTE", "GTE"]:  # Comparisons
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1, op2 = [s.strip() for s in ops.split(",")]
            op_map = {"EQ": "==", "LT": "<", "GT": ">", "LTE": "<=", "GTE": ">="}
            translated_line = f"{dest} = {_translate_operand(op1)} {op_map[opcode]} {_translate_operand(op2)}"
        elif opcode == "AND":
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1, op2 = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = {_translate_operand(op1)} and {_translate_operand(op2)}"
        elif opcode == "OR":
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1, op2 = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = {_translate_operand(op1)} or {_translate_operand(op2)}"
        elif opcode == "CON":
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1, op2 = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = str({_translate_operand(op1)}) + str({_translate_operand(op2)})"
        elif opcode == "NOT":
            dest, op = [s.strip() for s in args.split("=", 1)]
            translated_line = f"{dest} = not {_translate_operand(op)}"
        elif opcode == "PRINT":
            translated_line = f"print({_translate_operand(args)})"
        elif opcode == "INPUT":
            temp, message = args.split(', ')
            translated_line = f"{temp} = input({message})"
        elif opcode.startswith("ETIQUETA"):
            pass
        elif opcode == "GOTO":
            pass
        elif opcode == "GOTO_IF_FALSE":
            pass
        elif opcode == "CALL": #siempre van primero los push apram para que los acumulen si es que hay y los pongan en la llamada
            pass
        elif opcode == "PUSH_PARAM":
            pass
        elif opcode == "POP_RETVAL": #creo que no se usa pq ya le ajuste
            pass
        elif opcode == "RETURN":
            pass
        elif opcode == "PARAM_DECL":
            pass
        elif opcode == "FIN_FUNC":
            pass
        elif opcode == "GET_LIST_ITEM":
            pass
        elif opcode == "SET_LIST_ITEM":
            pass

        return translated_line, is_special_flow


    def save_n_exec(self, nombre_archivo="codigo_objeto.py"):
        try:
            with open(nombre_archivo, "w") as f:
                f.write(self.python_code)
            print(f"Código Python generado y guardado en: {nombre_archivo}")
        except IOError as e:
            print(f"Error al escribir el archivo Python '{nombre_archivo}': {e}")
            return False

        try:
            print(f"\n--- Ejecutando {nombre_archivo} ---")
            if len(self.errors) > 0:
                print("SE ENCONTRARON ERRORES: \n")
                for error in self.errors:
                    print(error + "\n")
                print(f"--- Ejecución de {nombre_archivo} finalizada ---")
                return False
            else:
                for warning in self.warnings:
                    print(warning + "\n")
                result = subprocess.run(["python", nombre_archivo], capture_output=False, check=True)
                print(f"--- Ejecución de {nombre_archivo} finalizada ---")
                return True
        except subprocess.CalledProcessError as e:
            print(f"El código Python ejecutado terminó con un error (Código de salida: {e.returncode}).")
            print(f"   Salida de error (stderr):")
            return False
        except FileNotFoundError:
            print(f"Error: El comando 'python' no fue encontrado.")
            print(f"   Asegúrate de que Python esté instalado y en tu variable de entorno PATH.")
            return False
        except Exception as e:
            print(f"Ocurrió un error inesperado durante la ejecución: {e}")
            return False