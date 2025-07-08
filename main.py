from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from Compiler.main import init_automata, lexical, syntax, semantic, intermediate
from Compiler.optimizer import OptimizadorCodigoIntermedio
from Compiler.backend import PythonCode
import asyncio
import threading
import json
import uuid
from typing import Dict, Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

automata = init_automata()

# Diccionario para manejar las sesiones de ejecución
execution_sessions: Dict[str, dict] = {}

class ExecutionSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.websocket: Optional[WebSocket] = None
        self.input_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()
        self.is_running = False
        self.is_waiting_input = False
        self.current_prompt = ""

    async def wait_for_input(self, prompt: str = "") -> str:
        """Función que reemplaza input() - espera respuesta del frontend"""
        self.is_waiting_input = True
        self.current_prompt = prompt
        
        # Enviar solicitud de input al frontend
        if self.websocket:
            await self.websocket.send_json({
                "type": "input_request",
                "prompt": prompt
            })
        
        # Esperar la respuesta del usuario
        response = await self.input_queue.get()
        self.is_waiting_input = False
        return response

    async def send_output(self, message: str):
        """Envía output al frontend"""
        if self.websocket:
            await self.websocket.send_json({
                "type": "output",
                "message": message
            })

def clean_code(code: str) -> str:
    """
    - Quita '\r'
    - Reemplaza NBSP por espacio normal
    - Elimina saltos de línea al inicio y al final
    """
    code = code.replace("\r", "").replace("\xa0", " ")
    return code.strip("\n")

@app.get("/", response_class=HTMLResponse)
def form(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "code": "",
        "tokens_console": "",
        "syntax_console": "",
        "semantic_console": "",
        "intermediate_console": "",
        "opti_console": "",
        "output_console": "",
        "tokens_json": [],
        "errors_json": [],
        "errors_s_json": [],
        "session_id": None,
    })

@app.post("/lex", response_class=HTMLResponse)
async def analyze(request: Request, code: str = Form(...)):
    code = clean_code(code)

    # 1) LEX
    tokens, lex_errors = lexical(automata, code)
    tokens_console = "\n".join(str(t.type) for t in tokens)

    # 2) SYNTAX
    string_ast, syntax_errors, ast = syntax(tokens)
    syntax_console = (
        "\n".join(err.value for err in syntax_errors)
        if syntax_errors else
        string_ast
    )

    # 3) SEMANTIC
    semantic_console = ""
    sem_errors = []
    if not lex_errors and not syntax_errors:
        sem_out, sem_errors = semantic(ast, tokens)
        semantic_console = (
            "\n".join(err.value for err in sem_errors)
            if sem_errors else
            sem_out
        )

    # 4) INTERMEDIATE / OPTIMIZE / TRANSLATE
    intermediate_console = ""
    opti_console = ""
    output_console = ""
    
    if not lex_errors and not syntax_errors and not sem_errors:
        # 4a) Código intermedio
        instrs = intermediate(ast)
        intermediate_console = "\n".join(instrs)

        # 4b) Optimización
        optimizador = OptimizadorCodigoIntermedio(instrs)
        optimized = optimizador.optimizar()
        opti_console = "\n".join(optimized)

        # 4c) Preparar para ejecución asíncrona
        # Crear session ID único para esta ejecución
        session_id = str(uuid.uuid4())
        execution_sessions[session_id] = {
            "code": optimized,
            "status": "ready"
        }
        
        output_console = f"Código listo para ejecución. Session ID: {session_id}"

    # 5) Preparar datos para resaltado en tiempo real
    simple_tokens = [
        {"index": t.index, "length": t.length, "type": (t.type // 1000) * 1000}
        for t in tokens
    ]
    simple_errors = [{"index": e.index, "length": e.length} for e in lex_errors]
    syn_errors_l = [
        {"index": tokens[e.index].index, "length": tokens[e.index].length}
        for e in syntax_errors
    ]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "code": code,
        "tokens_console": tokens_console,
        "syntax_console": syntax_console,
        "semantic_console": semantic_console,
        "intermediate_console": intermediate_console,
        "opti_console": opti_console,
        "output_console": output_console,
        "tokens_json": simple_tokens,
        "errors_json": simple_errors,
        "errors_s_json": syn_errors_l,
        "session_id": session_id if not lex_errors and not syntax_errors and not sem_errors else None
    })

@app.post("/lex/json")
async def lex_json(code: str = Form(...)):
    code = clean_code(code)
    tokens, lex_errors = lexical(automata, code)
    simple_tokens = [
        {"index": t.index, "length": t.length, "type": (t.type // 1000) * 1000}
        for t in tokens
    ]
    simple_errors = [{"index": e.index, "length": e.length} for e in lex_errors]
    _, syntax_errors, _ = syntax(tokens)
    syn_errors_l = [
        {"index": tokens[e.index].index, "length": tokens[e.index].length}
        for e in syntax_errors
    ]
    return JSONResponse({
        "tokens": simple_tokens,
        "errors": simple_errors,
        "errors_s_json": syn_errors_l
    })

#######
#Cada que se reqiera ejecutar código se va a tener que compilar antes
########
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if session_id not in execution_sessions:
        await websocket.send_json({
            "type": "error",
            "message": "Sesión no encontrada"
        })
        return

    #creamos la session de ejecución
    session = ExecutionSession(session_id)
    session.websocket = websocket
    execution_sessions[session_id]["session_obj"] = session

    try:#si detecta la sesiónse crea un solo hilo para evitar crear más y fast recibe el mensaje
        while True:
            data = await websocket.receive_json()
            if data["type"] == "start_execution":
                asyncio.create_task(execute_code_async(
                    session, execution_sessions[session_id]["code"]
                ))
            elif data["type"] == "input_response":
                if session.is_waiting_input:
                    await session.input_queue.put(data["value"])
    except WebSocketDisconnect:
        # limpia sesión
        if session_id in execution_sessions:
            del execution_sessions[session_id]

#esto se conecta con el back y genera la cadena con translator que a suvez llama
# a async_input y print junto con main
async def execute_code_async(session: ExecutionSession, optimized_code):
    translator = PythonCode(optimized_code, session)
    translator.translate()

    # Mensajes iniciales
    await session.send_output("Código generado: codigo_objeto.py")
    await session.send_output("Iniciando ejecución…")

    #ejecuta y gestiona inputs/outputs en el mismo loop
    await translator._execute_with_session("codigo_objeto.py")

    await session.send_output("Ejecución terminada.")