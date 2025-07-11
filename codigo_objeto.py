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
    if _execution_session:
        await _execution_session.send_output(str(message))
    else:
        print(message)

def weak_arithmetic(x):
    try: return float(x)
    except: return len(x)

async def main():
    t0 = 1
    MC_pr = t0
    if MC_pr:
        await async_print("hola")
        MC_pr = 1
    elif MC_pr:
        await async_print("sino")
    else:
        await async_print("sino2")
    await async_print(MC_pr)
### FIN MCScript ###
