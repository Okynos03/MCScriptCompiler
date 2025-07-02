from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from Compiler.main import *

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
automata = init_automata()

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
    print(repr(code))
    tokens, errors = main(automata, code)

    part1 = "\n".join([str(token.type) for token in tokens])
    part2 = "\n".join([f"{error.type} error: {error.value} at row {error.row} column {error.column}\n" for error in errors])
    result_string = f"{part1}\n\n{part2}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "code": code,
        "result": result_string # por ahora pasa code pq pasa lo mismo que tiene pero lo cambias por ejemplo por tokens_generados
    })
