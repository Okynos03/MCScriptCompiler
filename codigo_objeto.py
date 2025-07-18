### C MCScript ###
import asyncio
import sys

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
    text = str(message)
    #Agregué esto para que detectara bien los saltos
    for line in text.split("\n"):
        if _execution_session:
            await _execution_session.send_output(line)
        else:
            print(line)
def weak_arithmetic(x):
    try: 
        num_val = float(x)
        if num_val == int(num_val):
            return int(num_val)
        else:
            return num_val
    except: return len(x)

async def main():
    MC_run = 1
    t1 = await async_input("hola")
    MC_cf = ["Holaaa", t1, 1, [5, 3, "adios"]]
    t2 = MC_cf[1]
    await async_print(t2)
### FIN MCScript ###
