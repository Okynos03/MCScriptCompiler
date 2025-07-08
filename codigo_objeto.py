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

async def async_print(message):
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
    t1 = await async_input("ingresa:")
    resp = t1
    t2 = str("respuesta: ") + str(resp)
    await async_print(t2)
    await async_print("adios")

### FIN MCScript ###
