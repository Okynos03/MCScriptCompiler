from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
    #tokens_generados = analisis_lex(code)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "code": code # por ahora pasa code pq pasa lo mismo que tiene pero lo cambias por ejemplo por tokens_generados
    })
