from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from Compiler.main import main as lexer

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#Aquí no te metas porque sólo carga el html inicial
@app.get("/", response_class=HTMLResponse)
def form(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "code": ""  # el primer cuadro vacío para cargar ambos en la vista
    })

#Aquí es donde ya vas a hacer todo el movimiento como mandar llamar la función que ocupes para procesar el code
############
#NOTA: El parametro code se pasa como un str normal
@app.post("/lex", response_class=HTMLResponse)
async def analyze(request: Request, code: str = Form(...)):
    #ejemplo de función y así, pasas el code que es str
    print(code)
    code = code.replace("\r", "")
    tokens, errors = lexer(code)

    type_names = {
        6000: "identifier",
        1000: "keyword",
        3000: "punctuation",
        2000: "operator",
        4000: "curly-brace",
        5000: "bracket",
        7000: "integer",
        8000: "float"
    }

    #Función para escapar HTML (evitar inyección)
    def escape_html(s: str) -> str:
        return (s.replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))

    #Construye el HTML coloreado
    highlighted_parts = []
    for tok in tokens:
        raw = escape_html(tok.value)

        cls = type_names.get((tok.type // 1000) * 1000)
        
        print(cls)
        if cls:
            highlighted_parts.append(f'<span class="token-{cls}">{raw}</span>')
        else:
            highlighted_parts.append(raw)
    highlighted_code = "".join(highlighted_parts)

    part1 = "\n".join([str(token.type) for token in tokens])
    part2 = "\n".join([f"{error.type} error: {error.value} at row {error.row} column {error.column}\n" for error in errors])
    result_string = f"{part1}\n\n{part2}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "code": code,
        "result": result_string,
        "highlighted": highlighted_code
    })
