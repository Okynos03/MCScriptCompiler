from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from Compiler.main import *
from fastapi.responses import JSONResponse
import re

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
automata = init_automata()

def clean_code(code: str) -> str:
    """
    - Elimina todos los '\r'
    - Sustituye NBSP (U+00A0) por espacio normal
    - Quita saltos de línea al inicio y final, pero respeta los intermedios
    """
    # 1) Quitar retornos de carro
    code = code.replace("\r", "")
    # 2) Sustituir NBSP por espacio (si quieres borrarlo por completo, usa "")
    code = code.replace("\xa0", " ")
    # 3) Eliminar saltos de línea sobrantes al principio y al final
    code = code.strip("\n")
    return code

#Aquí no te metas porque sólo carga el html inicial
@app.get("/", response_class=HTMLResponse)
def form(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tokens_json": [],
        "errors_json": [],
        "errors_s_json": [],
        "code": ""  # el primer cuadro vacío para cargar ambos en la vista
    })

#Aquí es donde ya vas a hacer todo el movimiento como mandar llamar la función que ocupes para procesar el code
############
#NOTA: El parametro code se pasa como un str normal
@app.post("/lex", response_class=HTMLResponse)
async def analyze(request: Request, code: str = Form(...)):
    #ejemplo de función y así, pasas el code que es str
    code = code.replace("\r", "")
    code = code.replace("\xa0", "")
    tokens, errors = lexical(automata, code)

    part1 = "\n".join([str(token.type) for token in tokens])
    part2 = "\n".join([f"{error.type} error: {error.value} at row {error.row} column {error.column}\n" for error in errors])
    result_string = f"{part1}\n\n{part2}"

    # Prepara tokens mínimos para el cliente
    simple_tokens = [
      {"index": t.index, "length": t.length, "type": (t.type // 1000)*1000}
      for t in tokens
    ]

    for t in tokens:
        # Serie: 1000, 2000, 3000…
        serie = (t.type // 1000) * 1000
        # El substring real desde el código
        snippet = code[t.index : t.index + t.length]
        print(f"Token en índice {t.index} (longitud {t.length}): "
            f"'{snippet}' → serie {serie}")

    simple_errors = [{"index": err.index, "length": err.length} for err in errors]


    string_ast, syntax_errors = syntax(tokens)
    syn_errors_l = [{"index": tokens[err.index].index, "length": tokens[err.index].length} for err in syntax_errors]

    string_syntax_errors = ""
    for error in syntax_errors:
        string_syntax_errors += error.value + "\n"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "code": code,
        "result": string_syntax_errors if len(syntax_errors) > 0 else string_ast,
        "tokens_json": simple_tokens,
        "errors_json": simple_errors,
        "errors_s_json": syn_errors_l
    })

@app.post("/lex/json")
async def lex_json(code: str = Form(...)):
    code = code.replace("\r", "")
    #print(repr(code))
    tokens, errors = lexical(automata, code)

    simple_tokens = [
        {"index": t.index, "length": t.length, "type": (t.type // 1000) * 1000}
        for t in tokens
    ]
    simple_errors = [
        {"index": e.index, "length": e.length}
        for e in errors
    ]

    string_ast, syntax_errors = syntax(tokens)
    syn_errors_l = [{"index": tokens[err.index].index, "length": tokens[err.index].length} for err in syntax_errors]

    return JSONResponse({
        "tokens": simple_tokens,
        "errors": simple_errors,
        "errors_s_json": syn_errors_l
    })
