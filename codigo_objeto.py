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
    MC_x = 0
    while MC_x < 10:
        await async_print("while")
        t1 = weak_arithmetic(MC_x) + weak_arithmetic(1)
        MC_x = t1
### FIN MCScript ###
