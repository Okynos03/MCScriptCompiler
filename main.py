from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from Compiler.main import init_automata, lexical, syntax, semantic, intermediate, optimize, trasnlation

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inicializamos nuestro autómata
automata = init_automata()

def clean_code(code: str) -> str:
    """
    - Quita '\r'
    - Reemplaza NBSP por espacio normal
    - Elimina saltos de línea al inicio y al final
    """
    code = code.replace("\r", "")
    code = code.replace("\xa0", " ")
    return code.strip("\n")

@app.get("/", response_class=HTMLResponse)
def form(request: Request):
    # Al cargar la página por primera vez, todas las pestañas van vacías
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

    #fase lex
    tokens, lex_errors = lexical(automata, code)
    # Para la pestaña "Tokens"
    tokens_console = "\n".join(str(t.type) for t in tokens)

    #fase sintactica
    string_ast, syntax_errors, ast = syntax(tokens)
    if syntax_errors:
        syntax_console = "\n".join(err.value for err in syntax_errors)
    else:
        syntax_console = string_ast

    #fase semantica
    semantic_console = ""
    sem_errors = []
    if not syntax_errors and not lex_errors:
        sem_output, sem_errors = semantic(ast, tokens)
        if sem_errors:
            semantic_console = "\n".join([error.value for error in sem_errors])
        else:
            semantic_console = sem_output

    #code intermedio
    intermediate_console = ""
    if not lex_errors and not syntax_errors and not sem_errors:
        interm = intermediate(ast)
        intermediate_console = "\n".join(interm)
    #opt
        opt_code = optimize(interm)
        #que se vea el optimizado
    #obj
        exe = trasnlation(opt_code)
        exe.save_n_exec() #ya modifica tu apra que se descargue el archivo python y tu ves como haces que los mesnajes los muestre en consola


    #Colorear en tiempo real
    simple_tokens = [
        {"index": t.index, "length": t.length, "type": (t.type // 1000) * 1000}
        for t in tokens
    ]
    simple_errors = [
        {"index": e.index, "length": e.length}
        for e in lex_errors
    ]
    syn_errors_l = [
        {"index": tokens[err.index].index, "length": tokens[err.index].length}
        for err in syntax_errors
    ]

    #Renderizar la plantilla con las cuatro pestañas
    return templates.TemplateResponse("index.html", {
        "request": request,
        "code": code,
        "tokens_console": tokens_console,
        "syntax_console": syntax_console,
        "semantic_console": semantic_console,
        "intermediate_console": intermediate_console,
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
    simple_errors = [
        {"index": e.index, "length": e.length}
        for e in lex_errors
    ]

    _, syntax_errors, _ = syntax(tokens)
    syn_errors_l = [
        {"index": tokens[err.index].index, "length": tokens[err.index].length}
        for err in syntax_errors
    ]

    return JSONResponse({
        "tokens": simple_tokens,
        "errors": simple_errors,
        "errors_s_json": syn_errors_l
    })
