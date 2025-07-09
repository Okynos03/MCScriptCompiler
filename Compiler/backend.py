import subprocess
import asyncio
import os
import tempfile
from static.series import INT, FLOAT, COFRE

class PythonCode:
    def __init__(self, codigo_intermedio, execution_session=None):
        self.param_stack = None
        self.codigo_intermedio = codigo_intermedio
        self.execution_session = execution_session
        #aquí se va acumulando el script Python completo
        self.python_code = '''### C MCScript ###
import asyncio
import sys

# Variable global para la sesión de ejecución
_execution_session = None

def set_execution_session(session):
    global _execution_session
    _execution_session = session

async def async_input(prompt=""):
    """Función input asíncrona que se comunica con el frontend"""
    global _execution_session
    if _execution_session:
        return await _execution_session.wait_for_input(prompt)
    else:
        # Fallback a input normal si no hay sesión
        return input(prompt)

async def async_print(message=""):
    """Función print asíncrona que envía al frontend"""
    global _execution_session
    if _execution_session:
        await _execution_session.send_output(str(message))
    else:
        print(message)

def weak_arithmetic(x):
    try:
        return float(x)
    except:
        return len(x)

'''
        self.variables = {}
        self.warnings = []
        self.errors = []

    def translate(self):
        #_execution_session guarda la sesión actual el WebSocket
        #set_execution_session es el setter para inyectar la sesión _tras_ ejecutar el código
        #async_input/async_print son wrappers sobre input/print que envían/reciben datos al frontend
        #weak_arithmetic es el helper para operaciones aritméticas débiles pasa strings → len
        self.python_code = """### C MCScript ###
import asyncio
import sys

# Variable global para la sesión de ejecución
_execution_session = None

def set_execution_session(session):
    global _execution_session
    _execution_session = session

async def async_input(prompt=""):
    global _execution_session
    if _execution_session:
        return await _execution_session.wait_for_input(prompt)
    else:
        return input(prompt)

async def async_print(message=""):
    global _execution_session
    if _execution_session:
        await _execution_session.send_output(str(message))
    else:
        print(message)

def weak_arithmetic(x):
    try:
        return float(x)
    except:
        return len(x)

"""
        #firma main() y abrir su bloque
        self.python_code += "async def main():\n"
        if not self.codigo_intermedio:
            # si no hay nada que hacer pone al menos un pass
            self.python_code += "    pass\n"
        else:
            # por cada instrucción IR, traducirla e indentarla dentro de main()
            for ins in self.codigo_intermedio:
                code, _ = self._translate_single_ir_instruction(ins, 0)
                if code:
                    self.python_code += f"    {code}\n"
        self.python_code += """
### FIN MCScript ###
"""



    def _translate_single_ir_instruction(self, instruccion, indent_level):
        parts = instruccion.split(" ", 1)
        opcode = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        def _translate_operand(operand_str, type=None):
            operand_str = operand_str.strip()
            if operand_str in ["true", "false"]:
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
                pass

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
        elif opcode == "NEG":
            dest, ops = [s.strip() for s in args.split("=", 1)]
            op1 = ops.strip()
            translated_line = f"{dest} = (-1 * weak_arithmetic({_translate_operand(op1)}))"
        elif opcode in ["EQ", "LT", "GT", "LTE", "GTE"]:
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
            translated_line = f"await async_print({_translate_operand(args)})"
        elif opcode == "INPUT":
            temp, message = args.split(', ')
            translated_line = f"{temp} = await async_input({message})"
        elif opcode.startswith("ETIQUETA"):
            return f"{args}:"
        elif opcode == "GOTO":
            return "continue"
        elif opcode == "GOTO_IF_FALSE":
            cond, label = [s.strip() for s in args.split(",")]
            return f"if {_translate_operand(cond)}:"
        elif opcode == "CALL":
            if '=' in args:
                dest, func_name = [s.strip() for s in args.split("=")]
                params = ", ".join(self.param_stack)
                self.param_stack.clear()
                return f"{dest} = {func_name}({params})"
            else:
                func_name = args.strip()
                params = ", ".join(self.param_stack)
                self.param_stack.clear()
                return f"{func_name}({params})"
        elif opcode == "PUSH_PARAM":
            self.param_stack.append(_translate_operand(args))
            return None
        elif opcode == "POP_RETVAL":
            return None, is_special_flow
            #call ya asigna el valor de retorno pero checalo jesus
        elif opcode == "RETURN":
            return f"return {_translate_operand(args)}" if args else "return", is_special_flow
        elif opcode == "PARAM_DECL":
            return None, is_special_flow
        elif opcode == "FIN_FUNC":
            return None, is_special_flow
        elif opcode == "GET_LIST_ITEM":
            dest, ops = [s.strip() for s in args.split("=")]
            list_var, index_var = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = safe_get({_translate_operand(list_var)}, {_translate_operand(index_var)})"
        elif opcode == "SET_LIST_ITEM":
            ops, value = [s.strip() for s in args.split("=")]
            list_var, index_var = [s.strip() for s in ops.split(",")]
            translated_line = f"safe_set({_translate_operand(list_var)}, {_translate_operand(index_var)}, {_translate_operand(value)})"

        return translated_line, is_special_flow

    def save_n_exec(self, nombre_archivo="codigo_objeto.py"):
        try:
            with open(nombre_archivo, "w", encoding="utf-8") as f:
                f.write(self.python_code)
            print(f"Código Python generado y guardado en: {nombre_archivo}")
        except IOError as e:
            print(f"Error al escribir el archivo Python '{nombre_archivo}': {e}")
            return f"ERROR al escribir archivo: {e}"

        try:
            print(f"\n--- Ejecutando {nombre_archivo} ---")
            if self.errors:
                return "\n".join(self.errors)

            proc = subprocess.run(
                ["python", nombre_archivo],
                capture_output=True,
                text=True,
                check=False
            )
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()

            print(f"--- Ejecución de {nombre_archivo} finalizada ---")
            if proc.returncode != 0:
                return f"ERROR [{proc.returncode}]: {stderr}"
            return stdout

        except FileNotFoundError:
            return "ERROR: comando 'python' no encontrado"
        except Exception as e:
            return f"ERROR inesperado durante ejecución: {e}"

    async def save_n_exec_async(self, nombre_archivo="codigo_objeto.py"):
        try:
            #abre para escritura en UTF-8 porque agregaba simbolos raros si no
            with open(nombre_archivo, "w", encoding="utf-8") as f:
                f.write(self.python_code)
            if self.execution_session:
                await self.execution_session.send_output(
                    "=== SCRIPT GENERADO ===\n" + self.python_code + "\n=== FIN SCRIPT ==="
                )
        except IOError as e:
            error_msg = f"Error al escribir el archivo Python '{nombre_archivo}': {e}"
            if self.execution_session:
                await self.execution_session.send_output(error_msg)
            return error_msg
        
        try:
            if self.execution_session:
                await self.execution_session.send_output(f"Iniciando ejecución...")
            
            if self.errors:
                error_output = "\n".join(self.errors)
                if self.execution_session:
                    await self.execution_session.send_output(error_output)
                return error_output

            #ejecuta el código Python de forma especial para manejar los inputs
            await self._execute_with_session(nombre_archivo)
            
            return "Ejecución completada exitosamente"

        except Exception as e:
            error_msg = f"ERROR inesperado durante ejecución: {e}"
            if self.execution_session:
                await self.execution_session.send_output(error_msg)
            return error_msg

    async def _execute_with_session(self, nombre_archivo):
        """Ejecuta el código Python con manejo de sesión para inputs"""
        try:
            #Preparo sólo lo mínimo voy a dejar que el script importe todo
            namespace = {'__name__': '__main__'}

            #lee el código (UTF-8)
            with open(nombre_archivo, 'r', encoding='utf-8') as f:
                codigo = f.read()

            #Compila y ejecuta en el namespace
            compiled = compile(codigo, nombre_archivo, 'exec')
            exec(compiled, namespace)

            # aqui inyecta directamente la sesión en el namespace así async_input y async_print verán el objeto correcto.
            namespace['_execution_session'] = self.execution_session

            #invoca main() y lo espera
            main_func = namespace.get('main')
            if main_func and asyncio.iscoroutinefunction(main_func):
                await main_func()

        except Exception as e:
            if self.execution_session:
                await self.execution_session.send_output(f"Error de ejecución: {e}")
            raise
