from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from Compiler.main      import init_automata, lexical, syntax, semantic, intermediate
from Compiler.optimizer import OptimizadorCodigoIntermedio
from Compiler.backend   import PythonCode

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

automata = init_automata()

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
        "errors_s_json": []
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
    opti_console        = ""
    output_console      = ""
    if not lex_errors and not syntax_errors and not sem_errors:
        # 4a) Código intermedio
        instrs = intermediate(ast)
        intermediate_console = "\n".join(instrs)

        # 4b) Optimización
        optimizador  = OptimizadorCodigoIntermedio(instrs)
        optimized    = optimizador.optimizar()
        opti_console = "\n".join(optimized)

        # 4c) Traducción a Python y ejecución
        translator      = PythonCode(optimized)
        translator.translate()
        # modificar save_n_exec para que retorne el stdout como string
        output_console = translator.save_n_exec()

    # 5) Preparar datos para resaltado en tiempo real
    simple_tokens = [
        {"index": t.index, "length": t.length, "type": (t.type // 1000) * 1000}
        for t in tokens
    ]
    simple_errors = [{"index": e.index, "length": e.length} for e in lex_errors]
    syn_errors_l  = [
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
        "errors_s_json": syn_errors_l
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
