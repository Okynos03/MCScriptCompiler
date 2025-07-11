import subprocess
import asyncio
import os
import tempfile
from static.series import INT, FLOAT, COFRE

class PythonCode:
    def __init__(self, codigo_intermedio, execution_session=None):
        self.param_stack = []
        self.codigo_intermedio = codigo_intermedio
        self.execution_session = execution_session
        #aquí se va acumulando el script Python completo
        self.python_code = ""
        self.variables = {}
        self.warnings = []
        self.errors = []

    def translate(self):
        # 1) Emitir la cabecera (header + async def main())
        self._emitir_cabecera()

        indent = "    "
        ir = self.codigo_intermedio
        i, n = 0, len(ir)

        while i < n:
            if self._is_for_loop_start(ir, i):
                i = self._translate_for_loop(ir, i, indent)
                continue
            if self._is_while_loop_start(ir, i):
                i = self._translate_while_loop(ir, i, indent)
                continue
            if self._is_if_start(ir, i):
                i = self._translate_if_block(ir, i, indent)
                continue

            # Instrucciones atómicas
            line, _ = self._translate_single_ir_instruction(ir[i], 0)
            if line:
                self.python_code += indent + line.strip() + "\n"
            i += 1

        # 3) Pie de página (si necesitas algo tras main)
        self.python_code += "### FIN MCScript ###\n"



    # — Helpers para FOR numérico —
    def _is_for_loop_start(self, ir, idx):
        # La asignación inicial + etiqueta + UNA comparación (EQ/LT/LTE/GT/GTE) indican un for
        return (
            ir[idx].startswith("ASSIGN") and
            idx+1 < len(ir) and ir[idx+1].startswith("ETIQUETA FOR_START") and
            idx+2 < len(ir) and
            ir[idx+2].split()[0] in ("EQ","LT","LTE","GT","GTE")
        )

    def _translate_for_loop(self, ir, i, indent):
        # 1) Desempaquetar la asignación inicial (var = start)
        _, assign_args = ir[i].split(" ", 1)
        var, start = [s.strip() for s in assign_args.split("=", 1)]

        # 2) Extraer la etiqueta de inicio (FOR_STARTx:)
        _, label = ir[i + 1].split(" ", 1)
        start_label = label.rstrip(":")

        # 3) Encontrar el salto de retorno del for (GOTO FOR_STARTx)
        j_back = next(
            idx for idx in range(i + 2, len(ir))
            if ir[idx].startswith("GOTO ")
            and ir[idx].split(" ", 1)[1].strip() == start_label
        )

        # 4) Determinar el paso; puede venir en un ADD o un SUB justo antes de j_back
        step_instr = ir[j_back - 2]
        opcode_step, args_step = step_instr.split(" ", 1)  # p.ej. "ADD t1 = x, 1" o "SUB t1 = x, 1"
        _, ops = args_step.split("=", 1)
        op1, op2 = [s.strip() for s in ops.split(",", 1)]
        raw_step = op2  # p.ej. "1"
        if opcode_step == "ADD":
            step = raw_step
        elif opcode_step == "SUB":
            # decremento → paso negativo
            step = f"-{raw_step}"
        else:
            step = raw_step  # caso genérico

        # 5) Extraer la comparación que fija el límite (en ir[i+2])
        opcode_cmp, comp_args = ir[i + 2].split(" ", 1)  # p.ej. "LT t0 = x, 5" o "GT t0 = x, 0"
        _, rhs = comp_args.split("=", 1)
        parts = rhs.split()  # ["x", ">", "0"]
        end = parts[-1].strip()

        # 6) Calcular el end_expr según el comparador
        if opcode_cmp == "LT":
            end_expr = end
        elif opcode_cmp == "LTE":
            end_expr = f"{end} + 1"
        elif opcode_cmp == "GT":
            end_expr = end
        elif opcode_cmp == "GTE":
            end_expr = f"{end} - 1"
        else:
            end_expr = end  # otros comparadores

        # 7) Emitir el for en Python
        self.python_code += indent + f"for {var} in range({start}, {end_expr}, {step}):\n"

        # 8) Traducir el cuerpo (entre i+4 y j_back-2)
        k = i + 4
        body_end = j_back - 2
        while k < body_end:
            if self._is_for_loop_start(ir, k):
                k = self._translate_for_loop(ir, k, indent + "    "); continue
            if self._is_while_loop_start(ir, k):
                k = self._translate_while_loop(ir, k, indent + "    "); continue
            if self._is_if_start(ir, k):
                k = self._translate_if_block(ir, k, indent + "    "); continue

            line, _ = self._translate_single_ir_instruction(ir[k], 0)
            if line:
                self.python_code += indent + "    " + line.strip() + "\n"
            k += 1

        # 9) Saltar al final del for (después de ETIQUETA FOR_ENDx)
        return j_back + 2


    def _emitir_cabecera(self):
        # Aquí pones TODO ese string de la cabecera
        self.python_code = """### C MCScript ###
import asyncio
import sys

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
    try: return float(x)
    except: return len(x)

async def main():
"""

    # — Helpers para WHILE genérico —
    def _is_while_loop_start(self, ir, idx):
        return ir[idx].startswith("ETIQUETA WHILE_START")

    def _translate_while_loop(self, ir, i, indent):
        # --- 1) Encontrar y traducir la comparación ---
        comp_idx = next(
            j for j in range(i+1, len(ir))
            if ir[j].split()[0] in ("EQ","LT","GT","LTE","GTE")
        )
        comp_line, _ = self._translate_single_ir_instruction(ir[comp_idx], 0)
        # comp_line será algo como "t0 = MC_contador > 0"
        _, cond_expr = comp_line.split("=", 1)
        cond = cond_expr.strip()

        # --- 2) Encontrar la instrucción GOTO_IF_FALSE ---
        goto_idx = next(
            j for j in range(comp_idx+1, len(ir))
            if ir[j].startswith("GOTO_IF_FALSE")
        )
        # Extraer la etiqueta de fin
        _, rest = ir[goto_idx].split(" ", 1)        # "t0, WHILE_END1"
        _, end_label = [s.strip() for s in rest.split(",", 1)]

        # --- 3) Emitir el while con la condición correcta ---
        self.python_code += indent + f"while {cond}:\n"

        # --- 4) Traducir cuerpo hasta la etiqueta WHILE_END ---
        #    Buscamos índice de ETIQUETA ... WHILE_END1
        end_idx = next(
            j for j in range(goto_idx+1, len(ir))
            if ir[j].startswith("ETIQUETA") and end_label in ir[j]
        )

        k = goto_idx + 1
        while k < end_idx:
            # while anidado
            if self._is_while_loop_start(ir, k):
                k = self._translate_while_loop(ir, k, indent + "    ")
                continue
            # for anidado
            if self._is_for_loop_start(ir, k):
                k = self._translate_for_loop(ir, k, indent + "    ")
                continue
            # if anidado
            if self._is_if_start(ir, k):
                k = self._translate_if_block(ir, k, indent + "    ")
                continue

            # instrucción atómica
            body_line, _ = self._translate_single_ir_instruction(ir[k], 0)
            if body_line:
                self.python_code += indent + "    " + body_line.strip() + "\n"
            k += 1

        # --- 5) Continuar después del WHILE_END ---
        return end_idx + 1


    # — Detectar un “if” que empieza con GOTO_IF_FALSE —
    def _is_if_start(self, ir, idx):
        return ir[idx].split(" ", 1)[0] == "GOTO_IF_FALSE"

    def _translate_if_block(self, ir, i, indent):
        """
        Traduce desde GOTO_IF_FALSE cond, label_else
        hasta ETIQUETA ENDIF… saltando GOTO finales,
        y emite un if/else en Python con recursión para bloques anidados.
        Devuelve el nuevo índice tras haber consumido TODO el if/else.
        """
        # --- 1) extraer cond y label_else
        parts = ir[i].split(" ", 1)[1]
        cond_str, label_else = [s.strip() for s in parts.split(",", 1)]
        # traducimos operando si fuera literal
        cond_py = cond_str  # en tu caso MC_pr o literal "True"/"False"
        self.python_code += indent + f"if {cond_py}:\n"

        # --- 2) cuerpo THEN: desde i+1 hasta GOTO <label_end> o ETIQUETA <label_else> ---
        j = i + 1
        label_end = None
        while j < len(ir):
            instr = ir[j]
            # si es salto incondicional dentro del then, guarda el label_end y rompe
            if instr.startswith("GOTO "):
                label_end = instr.split(" ",1)[1].strip()
                j += 1
                break
            # si alcanzamos la etiqueta de else, terminamos then
            if instr.startswith("ETIQUETA") and instr.endswith(f"{label_else}:"):
                break

            # chequea anidamiento de estructuras
            if self._is_if_start(ir, j):
                j = self._translate_if_block(ir, j, indent + "    ")
                continue
            if self._is_for_loop_start(ir, j):
                j = self._translate_for_loop(ir, j, indent + "    ")
                continue
            if self._is_while_loop_start(ir, j):
                j = self._translate_while_loop(ir, j, indent + "    ")
                continue

            # instrucción atómica
            line, _ = self._translate_single_ir_instruction(instr, 0)
            if line:
                self.python_code += indent + "    " + line.strip() + "\n"
            j += 1

        print(label_else, ir[j], "dembele")
        # --- 3) ELSE? emitimos “else:” si existe etiqueta de else ---
        # si la siguiente instrucción es ETIQUETA <label_else> entonces hay else
        if label_else.startswith("ELSE") and \
           j < len(ir) and ir[j] == f"ETIQUETA {label_else}:":
            j += 1
            # — Cadena de elif —
            # Mientras veas GOTO_IF_FALSE, lo traducimos a "elif ..."
            print(ir[j])
            while j < len(ir) and (ir[j].startswith("GOTO_IF_FALSE") or ir[j].startswith("ETIQUETA ELSE")):
                print("dembo", j)
                if ir[j].startswith("ETIQUETA ELSE"):
                    j += 1
                    if not self._is_if_start(ir, j):
                        self.python_code += indent + "else:\n"
                        while j < len(ir) and ir[j] != f"ETIQUETA {label_end}:":
                            line, _ = self._translate_single_ir_instruction(ir[j], 0)
                            if line:
                                self.python_code += indent + "    " + line.strip() + "\n"
                            j += 1
                        return j

                print("2", ir[j])
                # extraer condición y siguiente etiqueta
                _, rest = ir[j].split(" ", 1)
                cond_i, next_else = [s.strip() for s in rest.split(",", 1)]
                self.python_code += indent + f"elif {cond_i}:\n"
                j += 1
                # traducir el bloque de este elif exactamente igual que un if
                while j < len(ir):
                    if ir[j].startswith("GOTO ") or ir[j].startswith("ETIQUETA ELSE") or ir[j].startswith("ETIQUETA ENDIF"):
                        j += 1
                        break
                    # detectar estructuras anidadas aquí...
                    if self._is_if_start(ir, j):
                        print("demebeeeeleee")
                        j = self._translate_if_block(ir, j, indent + "    ")
                        while ir[j].startswith("ETIQUETA ENDIF"):
                            j += 1
                        continue
                    if self._is_for_loop_start(ir, j):
                        j = self._translate_for_loop(ir, j, indent + "    "); continue
                    if self._is_while_loop_start(ir, j):
                        j = self._translate_while_loop(ir, j, indent + "    "); continue
                    line, _ = self._translate_single_ir_instruction(ir[j], 0)
                    if line:
                        self.python_code += indent + "    " + line.strip() + "\n"
                    j += 1

        #print(j, ir[j], "imporrtant")
        return j

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
            return None, False   # no emitimos nada aquí

        elif opcode == "GOTO_IF_FALSE" or opcode == "GOTO":
            return None, False

        elif opcode == "GOTO":
            # Si quieres ser más estricto, solo usa continue cuando sea salto a inicio del ciclo
            return "continue", False

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
