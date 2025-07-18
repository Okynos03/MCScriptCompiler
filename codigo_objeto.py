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
    t0 = await async_input("ingresa +, -, *, /")
    MC_simbolo = t0
    t1 = MC_simbolo == "+"
    if t1:
        await async_print("escogiste suma")
        t2 = await async_input("ingresar numero")
        MC_a = t2
        t3 = await async_input("ingresar numero")
        MC_b = t3
        t4 = weak_arithmetic(MC_a) + weak_arithmetic(MC_b)
        MC_r = t4
        await async_print(MC_r)
    else:
        t5 = MC_simbolo == "-"
        if t5:
            await async_print("escogiste resta")
            t6 = await async_input("ingresar numero")
            MC_a = t6
            t7 = await async_input("ingresar numero")
            MC_b = t7
            t8 = weak_arithmetic(MC_a) - weak_arithmetic(MC_b)
            MC_r = t8
            await async_print(MC_r)
        else:
            t9 = MC_simbolo == "*"
            if t9:
                await async_print("escogiste multi")
                t10 = await async_input("ingresar numero")
                MC_a = t10
                t11 = await async_input("ingresar numero")
                MC_b = t11
                t12 = weak_arithmetic(MC_a) * weak_arithmetic(MC_b)
                MC_r = t12
                await async_print(MC_r)
            else:
                t13 = MC_simbolo == "/"
                if t13:
                    await async_print("escogiste division")
                    t14 = await async_input("ingresar numero")
                    MC_a = t14
                    t15 = await async_input("ingresar numero")
                    MC_b = t15
                    t16 = weak_arithmetic(MC_a) / weak_arithmetic(MC_b)
                    MC_r = t16
                    await async_print(MC_r)
### FIN MCScript ###
