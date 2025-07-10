### C MCScript ###
import asyncio
import sys

# Variable global para la sesión de ejecución
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
    try:
        return float(x)
    except:
        return len(x)

async def main():
    await async_print("¿Hola cómo estás?")
    t0 = await async_input("ingresa tu respuesta:")
    MC_respuesta = t0
    await async_print(MC_respuesta)

### FIN MCScript ###
