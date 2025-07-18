import subprocess
import asyncio
import os
import tempfile
from static.series import INT, FLOAT, COFRE

class PythonCode:
    def __init__(self, codigo_intermedio, execution_session=None):
        self.predefined_code_len = 781
        self.param_stack = []
        self.codigo_intermedio = codigo_intermedio
        self.execution_session = execution_session
        #aquí se va acumulando el script Python completo
        self.python_code = ""
        self.variables = {}
        self.warnings = []
        self.errors = []

    def _translate_function_block(self, ir, i, indent):
        func_name_ir = ir[i].split(" ")[1].rstrip(":")  # "FUNC_MC_p"

        j = i + 1
        params = []
        while ir[j].startswith("PARAM_DECL"):
            param_name = ir[j].split(" ", 1)[1]
            params.append(param_name)
            j += 1

        params_str = ", ".join(params)
        self.python_code += f"{indent}async def {func_name_ir}({params_str}):\n"

        func_indent = indent + "    "
        i = j
        while not ir[i].startswith("FIN_FUNC"):
            if self._is_for_loop_start(ir, i):
                i = self._translate_for_loop(ir, i, indent + "    ")
                continue
            if self._is_while_loop_start(ir, i):
                i = self._translate_while_loop(ir, i, indent + "    ")
                continue
            if self._is_if_start(ir, i):
                i = self._translate_if_block(ir, i, indent + "    ")
                continue
            if ir[i].startswith("ETIQUETA FUNC_"):
                i = self._translate_function_block(ir, i, indent + "    ")
                continue

            line, _ = self._translate_single_ir_instruction(ir[i], 0)
            if line:
                self.python_code += func_indent + line.strip() + "\n"
            i += 1

        return i + 1

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

            if ir[i].startswith("ETIQUETA FUNC_"):
                i = self._translate_function_block(ir, i, indent)
                continue

            line, _ = self._translate_single_ir_instruction(ir[i], 0)
            if line:
                self.python_code += indent + line.strip() + "\n"

            i += 1

        self.python_code += "### FIN MCScript ###\n"

    def _emitir_cabecera(self):
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
    text = str(message)
    #Agregué esto para que detectara bien los saltos
    for line in text.split("\\n"):
        if _execution_session:
            await _execution_session.send_output(line)
        else:
            print(line)
def weak_arithmetic(x):
    try: 
        num_val = float(x)
        if num_val == int(num_val):
            return int(num_val)
        else:
            return num_val
    except: return len(x)

async def main():
    MC_run = 1
"""

    def _is_for_loop_start(self, ir, idx):
            # Verifico ASSIGN inicial y la etiqueta FOR_START contigua
            if not (ir[idx].startswith("ASSIGN") and
                    idx+1 < len(ir) and ir[idx+1].startswith("ETIQUETA FOR_START")):
                return False

            # Busco un GOTO_IF_FALSE antes de la siguiente etiqueta
            p = idx + 2
            while p < len(ir) and not ir[p].startswith("ETIQUETA"):
                if ir[p].startswith("GOTO_IF_FALSE"):
                    return True     # hallado ⇒ es un for
                p += 1
            return False


    def _translate_for_loop(self, ir, i, indent):
            #contador y valor inicial
            _, assign_args = ir[i].split(" ", 1)
            var, start = [s.strip() for s in assign_args.split("=", 1)]

            #etiqueta FOR_STARTN
            _, label = ir[i+1].split(" ", 1)
            start_label = label.rstrip(":")

            #localizo el GOTO_IF_FALSE que rompe el bucle
            p = i + 2
            while not ir[p].startswith("GOTO_IF_FALSE"):
                p += 1
            goto_idx  = p
            cond_line = ir[p-1]

            #se recupera la comparación que se hace y posible aritmética para el límite
            BIN_OPS = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/", "MOD": "%"}
            scan, arith_line = i + 2, None
            while ir[scan].split()[0] not in {"EQ","LT","LTE","GT","GTE"}:
                op = ir[scan].split()[0]
                if op in BIN_OPS:
                    arith_line = ir[scan]
                scan += 1
            cmp_idx = scan
            opcode_cmp, cmp_args = ir[cmp_idx].split(" ", 1)
            _, rhs     = cmp_args.split("=", 1)
            _, end_raw = rhs.split(",", 1)
            end_raw    = end_raw.strip()

            #aquí reconstruye end_expr
            if arith_line:
                op_code, expr = arith_line.split(" ", 1)
                dest, ops     = [s.strip() for s in expr.split("=", 1)]
                a, b          = [s.strip() for s in ops.split(",")]
                end_expr = f"{a} {BIN_OPS[op_code]} {b}" if dest == end_raw else end_raw
            else:
                end_expr = end_raw

            #ajusta inclusividad para range()
            if opcode_cmp == "LTE":
                end_expr = f"({end_expr}) + 1"
            elif opcode_cmp == "GTE":
                end_expr = f"({end_expr}) - 1"

            #se detecta cada instrucción de paso (ADD/SUB contador, 1)
            j_back = next(idx for idx in range(cmp_idx+1, len(ir))
                        if ir[idx].startswith("GOTO ") and
                            ir[idx].split()[1] == start_label)
            step_instr       = ir[j_back-2]
            op_step, s_args  = step_instr.split(" ", 1)
            _, ops_step      = s_args.split("=", 1)
            _, step_val      = [s.strip() for s in ops_step.split(",", 1)]
            step = step_val if op_step == "ADD" else f"-{step_val}"

            #encabezado del for
            self.python_code += indent + f"for {var} in range({start}, {end_expr}, {step}):\n"

            #para cuando se usa condiciones complejas 
            for q in range(i+2, goto_idx):
                line, _ = self._translate_single_ir_instruction(ir[q], 0)
                if line:
                    self.python_code += indent + "    " + line.strip() + "\n"

            #break si la condición final es falsa
            cond_var = cond_line.split(" ",1)[1].split("=",1)[0].strip()
            self.python_code += indent + f"    if not {cond_var}: break\n"

            #traduce el cuerpo real del for
            body_start, body_end = goto_idx + 1, j_back - 2
            k = body_start
            STEP = "    "
            while k < body_end:
                if self._is_for_loop_start(ir, k):
                    k = self._translate_for_loop(ir, k, indent + STEP); continue
                if self._is_while_loop_start(ir, k):
                    k = self._translate_while_loop(ir, k, indent + STEP); continue
                if self._is_if_start(ir, k):
                    k = self._translate_if_block(ir, k, indent + STEP); continue
                if ir[k].startswith("ETIQUETA FUNC_"):
                    k = self._translate_function_block(ir, k, indent + "    "); continue

                line, _ = self._translate_single_ir_instruction(ir[k], 0)
                if line:
                    self.python_code += indent + STEP + line.strip() + "\n"
                k += 1

            return j_back + 2

    # — Helpers para WHILE genérico —
    def _is_while_loop_start(self, ir, idx):
        return ir[idx].startswith("ETIQUETA WHILE_START")

    def _translate_while_loop(self, ir, i, indent):
        """
        Traduce un bloque while tanto si viene con comparación explícita
        como si sólo aparece el GOTO_IF_FALSE.
        """
        recalculate = ""
        # 1) Ver si la instrucción siguiente es GOTO_IF_FALSE o una comparación
        if ir[i+1].startswith("GOTO_IF_FALSE"):
            # Caso simple: condición directa en el salto
            # Formato IR: "GOTO_IF_FALSE MC_flag, WHILE_END1"
            _, rest = ir[i+1].split(" ", 1)           # rest == "MC_flag, WHILE_END1"
            cond, end_label = [s.strip() for s in rest.split(",", 1)]
            body_start = i + 2
        else:
            # Caso comparación+salto
            #  a) traducir la comparación (ej. "LT t0 = MC_x, 10")
            next_break = False
            comp_line = ""
            while i < len(ir):
                i += 1
                if next_break:
                    break
                print(ir[i])
                comp_line, _ = self._translate_single_ir_instruction(ir[i], 0)
                if not ir[i+1].startswith("GOTO_IF_FALSE"):
                    self.python_code += indent + comp_line + "\n"
                    recalculate += indent + "    " + comp_line + "\n"
                else:
                    next_break = True

            _, cond_expr = comp_line.split("=", 1)
            cond = cond_expr.strip()
            _, rest = ir[i].split(" ", 1)  # rest == "t0, WHILE_END1"
            _, end_label = [s.strip() for s in rest.split(",", 1)]
            body_start = i + 1

        # 2) Emitir el while con la condición correcta
        self.python_code += indent + f"while {cond}:\n"

        # 3) Encontrar dónde termina el while
        end_idx = next(
            j for j in range(body_start, len(ir))
            if ir[j].startswith("ETIQUETA") and end_label in ir[j]
        )

        # 4) Traducir todo el cuerpo entre body_start y end_idx
        k = body_start
        while k < end_idx:
            if self._is_while_loop_start(ir, k):
                k = self._translate_while_loop(ir, k, indent + "    ")
                continue
            if self._is_for_loop_start(ir, k):
                k = self._translate_for_loop(ir, k, indent + "    ")
                continue
            if self._is_if_start(ir, k):
                k = self._translate_if_block(ir, k, indent + "    ")
                continue
            if ir[k].startswith("ETIQUETA FUNC_"):
                k = self._translate_function_block(ir, k, indent + "    ")
                continue

            body_line, _ = self._translate_single_ir_instruction(ir[k], 0)
            if body_line:
                self.python_code += indent + "    " + body_line.strip() + "\n"
            k += 1

        # 5) Retornar índice justo después del WHILE_END
        self.python_code += recalculate
        return end_idx + 1


    # — Detectar un “if” que empieza con GOTO_IF_FALSE —
    def _is_if_start(self, ir, idx):
        rebo = ir[idx].split(" ")
        return rebo[0] == "GOTO_IF_FALSE" and (rebo[-1][:4] == "ELSE" or rebo[-1][:5] == "ENDIF")

    def _translate_if_block(self, ir, i, indent, is_if=True, is_else=False, label_end=None):
        """
        Traduce desde GOTO_IF_FALSE cond, label_else
        hasta ETIQUETA ENDIF… saltando GOTO finales,
        y emite un if/else en Python con recursión para bloques anidados.
        Devuelve el nuevo índice tras haber consumido TODO el if/else.
        """
        # --- 1) extraer cond y label_else
        if is_if:
            parts = ir[i].split(" ", 1)[1]
            cond_str, label_else = [s.strip() for s in parts.split(",", 1)]
            has_else = label_else[0:4] == "ELSE"
            # traducimos operando si fuera literal
            cond_py = cond_str  # en tu caso MC_pr o literal "True"/"False"
            self.python_code += indent + f"if {cond_py}:\n" if not is_else else  indent + f"elif {cond_py}:\n"
            j = i + 1
        else:
            has_else = False
            label_else = label_end
            self.python_code += indent + f"else:\n"
            j = i

        # --- 2) cuerpo THEN: desde i+1 hasta GOTO <label_end> o ETIQUETA <label_else> ---
        while j < len(ir):
            instr = ir[j]
            # si es salto incondicional dentro del then, guarda el label_end
            if has_else and instr[0:10] == "GOTO ENDIF":
                label_end = instr.split(" ",1)[1].strip() if label_end is None else label_end
                j += 1
                continue
            # si alcanzamos la etiqueta de else, terminamos then
            if (instr.startswith("ETIQUETA") and instr.endswith(f"{label_else}:")) \
                    or \
                    (not has_else and instr.startswith("ETIQUETA") and instr.endswith(f"{label_else}")):
                j += 1
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
            if ir[j].startswith("ETIQUETA FUNC_"):
                j = self._translate_function_block(ir, j, indent + "    ")
                continue

            # instrucción atómica
            line, _ = self._translate_single_ir_instruction(instr, 0)
            if line:
                self.python_code += indent + "    " + line.strip() + "\n"
            j += 1

        if has_else:
            j = self._translate_if_block(ir, j, indent, self._is_if_start(ir, j), is_else=True, label_end=label_end)

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
            val = _translate_operand(src)
            translated_line = f"{dest} = {val}"
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
            temp, message = args.split(', ', 1)
            translated_line = f"{temp} = await async_input({message})"
        elif opcode.startswith("ETIQUETA"):
            return None, False   # no emitimos nada aquí

        elif opcode == "GOTO_IF_FALSE" or opcode == "GOTO":
            return None, False

        elif opcode == "CALL":
            # Asume el formato: "nombre_func, var_retorno"
            parts = [s.strip() for s in args.split(",")]
            func_name = parts[0]
            dest = parts[1] if len(parts) > 1 else None

            params = ", ".join(self.param_stack)
            self.param_stack.clear()

            call_str = f"await {func_name}({params})"

            if dest:
                # Si hay variable de retorno, asigna el resultado
                translated_line = f"{dest} = {call_str}"
            else:
                # Si no, solo llama a la función
                translated_line = call_str

            return translated_line, True
        elif opcode == "PUSH_PARAM":
            self.param_stack.append(_translate_operand(args))
            return None, False
        elif opcode == "POP_RETVAL":
            return None, is_special_flow
            #call ya asigna el valor de retorno pero checalo jesus
        elif opcode == "RETURN":
            return f"return {_translate_operand(args)}" if args else "return", is_special_flow
        elif opcode == "PARAM_DECL":
            return None, is_special_flow
        elif opcode == "FIN_FUNC":
            indent_level -= 1
            return None, is_special_flow
        elif opcode == "GET_LIST_ITEM":
            dest, ops = [s.strip() for s in args.split("=")]
            list_var, index_var = [s.strip() for s in ops.split(",")]
            translated_line = f"{dest} = {_translate_operand(list_var)}[{_translate_operand(index_var)}]"
        elif opcode == "SET_LIST_ITEM":
            list_var, ops = [s.strip() for s in args.split(",", 1)]
            index_var, value = [s.strip() for s in ops.split(",", 1)]
            translated_line = f"{_translate_operand(list_var)}[{_translate_operand(index_var)}] = {_translate_operand(value)}"

        elif opcode == "PORTAL":
            func_name = args.split("(", 1)[0].strip()
            params_part = args.split("(", 1)[1].rstrip(")")
            params = [p.strip() for p in params_part.split(",")] if params_part else []
            translated_line = f"async def {func_name}({', '.join(params)}):"
            indent_level += 1

        return translated_line, is_special_flow

    def save_n_exec(self, nombre_archivo="codigo_objeto.py"):
        print(len(self.python_code))
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
