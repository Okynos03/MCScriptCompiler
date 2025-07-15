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
    MC_arr = [5, 2, 4]
    for MC_i in range(0, 3, 1):
        t0 = MC_i < 3
        if not t0: break
        for MC_j in range(0, 3 - MC_i, 1):
            t1 = weak_arithmetic(3) - weak_arithmetic(MC_i)
            t2 = MC_j < t1
            if not t2: break
            t3 = MC_arr[MC_j]
            t4 = weak_arithmetic(MC_j) + weak_arithmetic(1)
            t5 = MC_arr[t4]
            t6 = t3 > t5
            if t6:
                t7 = MC_arr[MC_j]
                MC_tmp = t7
                t8 = weak_arithmetic(MC_j) + weak_arithmetic(1)
                t9 = MC_arr[t8]
                MC_arr[MC_j] = t9
                t10 = weak_arithmetic(MC_j) + weak_arithmetic(1)
                MC_arr[t10] = MC_tmp
    for MC_k in range(0, 3, 1):
        t13 = MC_k < 3
        if not t13: break
        t14 = MC_arr[MC_k]
        await async_print(t14)
### FIN MCScript ###
