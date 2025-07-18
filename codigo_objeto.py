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
    try: return float(x)
    except: return len(x)

async def main():
    MC_run = 1
    MC_b = 0
    t0 = MC_b == 0
    if t0:
        async def FUNC_MC_p1():
            await async_print("1")
    while MC_b < 10:
        t2 = weak_arithmetic(MC_b) + weak_arithmetic(1)
        MC_b = t2
### FIN MCScript ###
