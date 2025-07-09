import re


class OptimizadorCodigoIntermedio:
    def __init__(self, codigo_intermedio):
        self.codigo_intermedio = list(codigo_intermedio)
        self.optimizacion_aplicada = False

    def optimizar(self):
        cambios_realizados = True
        while cambios_realizados:
            cambios_realizados = False
            if self._plegar_constantes():
                cambios_realizados = True
            if self._eliminar_asignaciones_redundantes():
                cambios_realizados = True
            #fusion de etiquetas
            if self._eliminar_codigo_muerto():
                cambios_realizados = True

        return self.codigo_intermedio

    def _eliminar_asignaciones_redundantes(self):
        cambios = False
        nuevo_codigo = []

        for instruccion in self.codigo_intermedio:
            parts = instruccion.split(" ", 1)
            opcode = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            match_assign = re.match(r'([a-zA-Z_]\w*)\s*=\s*([a-zA-Z_]\w*)', args)

            if opcode == "ASSIGN" and match_assign:
                dest_var = match_assign.group(1).strip()
                src_var = match_assign.group(2).strip()
                if dest_var == src_var:
                    cambios = True
                    continue
            nuevo_codigo.append(instruccion)

        if cambios:
            self.codigo_intermedio = nuevo_codigo
        return cambios

    def _plegar_constantes(self):
        cambios = False
        instrucciones_nuevas = []
        valores_conocidos = {}

        for instruccion in self.codigo_intermedio:
            if instruccion[0] == "#":
                #instrucciones_nuevas.append(instruccion)
                continue
            partes = instruccion.split(" ", 1)
            opcode = partes[0]
            args = partes[1] if len(partes) > 1 else ""

            if "=" in args:
                destino, operacion = args.split("=", 1)
                destino = destino.strip()
                operacion = operacion.strip()

                if opcode in ["ADD", "SUB", "MUL", "DIV", "MOD", "POW", "AND", "OR", "NEG", "NOT", "EQ", "GT", "GTE", "LT", "LTE", "CON"]:
                    try:
                        if opcode in ["NEG", "NOT"]:
                            op1_str = operacion
                            op1_val = valores_conocidos.get(op1_str, None)
                            if op1_val is None:
                                op1_val = float(op1_str) if '.' in op1_str else int(op1_str)

                            resultado = None
                            if opcode == "NEG":
                                resultado = -op1_val
                            elif opcode == "NOT":
                                resultado = int(not bool(op1_val))

                            if resultado is not None:
                                instrucciones_nuevas.append(f"ASSIGN {destino} = {resultado}")
                                valores_conocidos[destino] = resultado
                                cambios = True
                                continue
                        else:
                            op_partes = operacion.split(', ', 1)
                            if len(op_partes) != 2:
                                pass

                            op1_str, op2_str = op_partes[0].strip(), op_partes[1].strip()
                            op1_val = valores_conocidos.get(op1_str, None)
                            if op1_val is None:
                                if opcode != "CON":
                                    try:
                                        op1_val = float(op1_str) if '.' in op1_str else int(op1_str)
                                    except ValueError:
                                        pass
                                else:
                                    op1_val = op1_str

                            op2_val = valores_conocidos.get(op2_str, None)
                            if op2_val is None:
                                if opcode != "CON":
                                    try:
                                        op2_val = float(op2_str) if '.' in op2_str else int(op2_str)
                                    except ValueError:
                                        pass  #
                                else:
                                    op2_val = op2_str

                            if op1_val is not None and op2_val is not None:
                                resultado = None
                                if opcode == "ADD":
                                    resultado = op1_val + op2_val
                                elif opcode == "SUB":
                                    resultado = op1_val - op2_val
                                elif opcode == "MUL":
                                    resultado = op1_val * op2_val
                                elif opcode == "DIV":
                                    if op2_val != 0:
                                        resultado = op1_val / op2_val
                                    else:
                                        pass
                                elif opcode == "MOD":
                                    if op2_val != 0:
                                        resultado = op1_val % op2_val
                                    else:
                                        pass
                                elif opcode == "POW":
                                    resultado = op1_val ** op2_val
                                elif opcode == "AND":
                                    resultado = int(bool(op1_val) and bool(op2_val))
                                elif opcode == "OR":
                                    resultado = int(bool(op1_val) or bool(op2_val))
                                elif opcode == "EQ":
                                    resultado = int(op1_val == op2_val)
                                elif opcode == "GT":
                                    resultado = int(op1_val > op2_val)
                                elif opcode == "GTE":
                                    resultado = int(op1_val >= op2_val)
                                elif opcode == "LT":
                                    resultado = int(op1_val < op2_val)
                                elif opcode == "LTE":
                                    resultado = int(op1_val <= op2_val)
                                elif opcode == "CON" and op1_val[0] == '"' and op2_val[0] == '"':
                                    resultado = f' "{op1_val[1:-1]}{op2_val[1:-1]}"'

                                if resultado is not None:
                                    instrucciones_nuevas.append(f"ASSIGN {destino} = {resultado}")
                                    valores_conocidos[destino] = resultado
                                    cambios = True
                                    continue

                    except ValueError:
                        pass

                #gemini me dice que tenia que checar lo de pop no se donde ponerlo, pero es como una asignacion creo hay que revisar
                #por coo maneje el pop en la instruccion, no lo puse como opcode
                if opcode in ["ASSIGN", "POP_RETVAL"]:
                    try:
                        valor_directo = float(operacion) if '.' in operacion else int(operacion)
                        valores_conocidos[destino] = valor_directo
                    except ValueError:
                        pass
            instrucciones_nuevas.append(instruccion)

        self.codigo_intermedio = instrucciones_nuevas
        return cambios

    def _eliminar_codigo_muerto(self):
        cambios = False

        # --- Step 1: Identify Basic Blocks and their properties ---
        blocks = []  # List of dictionaries, each representing a basic block
        # { 'start_idx': int, 'end_idx': int, 'gen': set(), 'kill': set(),
        #   'successors': list of block_indices, 'predecessors': list of block_indices,
        #   'live_in': set(), 'live_out': set() }

        label_to_block_idx = {}  # Map label name to block index
        block_starts = []  # List of instruction indices where blocks start

        # Identify block start points
        if len(self.codigo_intermedio) > 0:
            block_starts.append(0)  # Program start is always a block start

        for i, instruccion in enumerate(self.codigo_intermedio):
            parts = instruccion.split(" ", 1)
            opcode = parts[0]

            if opcode.startswith("ETIQUETA"):
                label_name = parts[1].replace(":", "")
                if i not in block_starts:  # Ensure it's not already marked
                    block_starts.append(i)
                # Any instruction *after* a jump is also a new block start
                # This is implicitly handled by the next instruction check, but good to note.
                label_to_block_idx[label_name] = len(block_starts) - 1  # provisional block idx

            # If current instruction is a jump, the next instruction starts a new block
            elif opcode in ["GOTO", "GOTO_IF_FALSE", "RETURN", "FIN_FUNC"]:
                if i + 1 < len(self.codigo_intermedio) and (i + 1) not in block_starts:
                    block_starts.append(i + 1)

        block_starts.sort()  # Ensure sorted order of block start indices

        # Create basic block objects
        for i in range(len(block_starts)):
            start_idx = block_starts[i]
            end_idx = (block_starts[i + 1] - 1) if (i + 1 < len(block_starts)) else (len(self.codigo_intermedio) - 1)

            blocks.append({
                'start_idx': start_idx,
                'end_idx': end_idx,
                'gen': set(),  # Variables used before defined in this block
                'kill': set(),  # Variables defined in this block
                'successors': [],
                'predecessors': [],
                'live_in': set(),
                'live_out': set(),
                'instructions': self.codigo_intermedio[start_idx: end_idx + 1]
                # Store actual instructions for easier processing
            })
            # Update label_to_block_idx for correct block indices
            if self.codigo_intermedio[start_idx].startswith("ETIQUETA"):
                label_name = self.codigo_intermedio[start_idx].split(" ")[1].replace(":", "")
                label_to_block_idx[label_name] = len(blocks) - 1

        # --- Step 2: Populate GEN, KILL, Successors/Predecessors for each block ---

        # Helper to get defined and used variables for a single instruction
        def get_def_use(instruction):
            defined = set()
            used = set()
            parts = instruction.split(" ", 1)
            opcode = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            # Define variables
            if '=' in args:
                defined.add(args.split("=", 1)[0].strip())
            elif opcode in ["ASSIGN", "POP_RETVAL"]:
                if '=' in args:
                    defined.add(args.split("=", 1)[0].strip())
                elif args:
                    defined.add(args.strip())
            elif opcode == "PARAM_DECL":# Treat params as defined here for local liveness in block
                defined.add(args.split(" ")[0].strip())

                # Use variables (general pattern)
            operand_str = args.split("=", 1)[1] if '=' in args else args
            candidate_operands = re.findall(r'\b[a-zA-Z_]\w*\b', operand_str)
            for op in candidate_operands:
                if not (op in ["true", "false", "encendido", "apagado"] or \
                        (op.startswith('"') and op.endswith('"')) or \
                        (op.startswith("'") and op.endswith("'"))):
                    try:
                        float(op)
                    except ValueError:
                        used.add(op)

            # Use variables (specific opcodes)
            if opcode == "PUSH_PARAM":
                val = args.strip()
                try:
                    float(val)
                except ValueError:
                    used.add(val)
            elif opcode == "PRINT" or (opcode == "RETURN" and args):
                val = args.strip()
                try:
                    float(val)
                except ValueError:
                    used.add(val)
            elif opcode == "INPUT":
                val = args.split(', ')
                for v in val:
                    try:
                        float(v)
                    except ValueError:
                        used.add(v)
            elif opcode == "GOTO_IF_FALSE":
                used.add(args.split(',')[0].strip())
            elif opcode == "SET_LIST_ITEM":
                parts_set = [p.strip() for p in args.split(',')]
                used.add(parts_set[0])  # list reference
                try:
                    float(parts_set[1])
                except ValueError:
                    used.add(parts_set[1])  # index
                try:
                    float(parts_set[2])
                except ValueError:
                    used.add(parts_set[2])  # value
            elif opcode == "GET_LIST_ITEM":
                parts_get = args.split('=', 1)[1].split(',')
                used.add(parts_get[0].strip())  # list reference
                try:
                    float(parts_get[1])
                except ValueError:
                    used.add(parts_get[1])  # index

            return defined, used

        # Populate GEN and KILL sets for each block
        for block_idx, block in enumerate(blocks):
            for i in range(block['start_idx'], block['end_idx'] + 1):
                inst = self.codigo_intermedio[i]
                defined, used = get_def_use(inst)

                for u_var in used:
                    if u_var not in block['kill']:  # Only add to GEN if not killed within the block before use
                        block['gen'].add(u_var)

                for d_var in defined:
                    block['kill'].add(d_var)

            # Determine successors
            last_inst = self.codigo_intermedio[block['end_idx']]
            opcode = last_inst.split(" ", 1)[0]
            args = last_inst.split(" ", 1)[1] if len(last_inst.split(" ", 1)) > 1 else ""

            if opcode == "GOTO":
                target_label = args.strip()
                if target_label in label_to_block_idx:
                    succ_idx = label_to_block_idx[target_label]
                    block['successors'].append(succ_idx)
                    blocks[succ_idx]['predecessors'].append(block_idx)
            elif opcode == "GOTO_IF_FALSE":
                target_label = args.split(',')[1].strip()
                if target_label in label_to_block_idx:
                    succ_idx = label_to_block_idx[target_label]
                    block['successors'].append(succ_idx)
                    blocks[succ_idx]['predecessors'].append(block_idx)
                # Fall-through to next block
                if block_idx + 1 < len(blocks):
                    block['successors'].append(block_idx + 1)
                    blocks[block_idx + 1]['predecessors'].append(block_idx)
            elif opcode in ["RETURN", "FIN_FUNC"]:
                # No fall-through, no explicit successors (function exit)
                pass
            else:  # Fall-through to next block
                if block_idx + 1 < len(blocks):
                    block['successors'].append(block_idx + 1)
                    blocks[block_idx + 1]['predecessors'].append(block_idx)

        # --- Step 3: Iterative Dataflow Analysis (Backward) ---
        # Calculate LiveIn and LiveOut until convergence

        # Initialize all LiveIn/LiveOut to empty sets
        for block in blocks:
            block['live_in'] = set()
            block['live_out'] = set()

        changed = True
        while changed:
            changed = False
            for block_idx in reversed(range(len(blocks))):  # Iterate backward for liveness
                block = blocks[block_idx]

                old_live_in = block['live_in'].copy()
                old_live_out = block['live_out'].copy()

                # Calculate LiveOut[Block] = Union of LiveIn[Succ] for all successors
                new_live_out = set()
                for succ_idx in block['successors']:
                    new_live_out.update(blocks[succ_idx]['live_in'])
                block['live_out'] = new_live_out

                # Calculate LiveIn[Block] = Uses[Block] U (LiveOut[Block] - Defs[Block])
                # Uses[Block] is block['gen'] in our terminology (vars used before defined)
                # Defs[Block] is block['kill']
                new_live_in = block['gen'].union(block['live_out'] - block['kill'])
                block['live_in'] = new_live_in

                if new_live_in != old_live_in or new_live_out != old_live_out:
                    changed = True

        # --- Step 4: Determine which instructions to keep ---
        # Now, iterate through instructions with the final LiveIn/LiveOut sets.

        instrucciones_a_mantener_indices = set()

        for block_idx, block in enumerate(blocks):
            # Start with live_out for the last instruction in the block
            # Then work backwards within the block using instruction-level liveness

            # Initialize current_live_within_block with block's live_out
            current_live_within_block = block['live_out'].copy()

            for i in reversed(range(block['start_idx'], block['end_idx'] + 1)):
                instruccion = self.codigo_intermedio[i]
                parts = instruccion.split(" ", 1)
                opcode = parts[0]
                args = parts[1] if len(parts) > 1 else ""

                # # Special handling for PARAM_DECL: Completely ignore for liveness, remove by default
                # if opcode == "PARAM_DECL":
                #     cambios = True
                #     continue  # Skip this instruction entirely if we don't want it

                # Get defined and used for this instruction
                defined_by_inst, used_by_inst = get_def_use(instruccion)

                # Determine if this instruction has a side effect or is control flow
                is_side_effect_or_control_flow = False
                if opcode in ["PRINT", "INPUT", "GOTO", "GOTO_IF_FALSE", "CALL", "RETURN", "FIN_FUNC", "PARAM_DECL"] or \
                        opcode.startswith("ETIQUETA"):
                    is_side_effect_or_control_flow = True
                elif opcode == "SET_LIST_ITEM" or opcode == "PUSH_PARAM":
                    is_side_effect_or_control_flow = True

                # Is this instruction needed?
                is_needed = False
                if is_side_effect_or_control_flow:
                    is_needed = True
                # If any variable defined by *this specific instruction* is live *after* this instruction
                elif any(var in current_live_within_block for var in defined_by_inst):
                    is_needed = True

                if is_needed:
                    instrucciones_a_mantener_indices.add(i)

                    # Update current_live_within_block:
                    # Remove variables defined by this instruction
                    for var in defined_by_inst:
                        if var in current_live_within_block:
                            current_live_within_block.remove(var)
                    # Add variables used by this instruction
                    for var in used_by_inst:
                        current_live_within_block.add(var)
                else:
                    cambios = True  # This instruction is dead

        # Build the final optimized code
        codigo_optimizado = [self.codigo_intermedio[idx] for idx in sorted(list(instrucciones_a_mantener_indices))]

        if len(codigo_optimizado) != len(self.codigo_intermedio):
            cambios = True

        self.codigo_intermedio = codigo_optimizado
        return cambios