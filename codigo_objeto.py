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
    await async_print("------CALCULADORA MCS----------")
    MC_flag = 1
    while MC_flag:
        t0 = str("MENÚ:\n") + str("1. ingresa + para sumar\n")
        t1 = str(t0) + str("2. ingresa - para restar\n")
        t2 = str(t1) + str("3. ingresa * para multiplicar\n")
        t3 = str(t2) + str("4. ingresa / para dividir\n")
        t4 = str(t3) + str("5. ingresa s para terminar el programa")
        await async_print(t4)
        t5 = await async_input("ingresa la operación a realizar")
        MC_ingreso = t5
        t6 = MC_ingreso == "+"
        if t6:
            t7 = await async_input("ingresa operando 1:")
            MC_op1 = t7
            t8 = await async_input("ingresa operando 2:")
            MC_op2 = t8
            t9 = weak_arithmetic(MC_op1) + weak_arithmetic(MC_op2)
            MC_resultado = t9
            t10 = str("resultado: ") + str(MC_resultado)
            await async_print(t10)
        else:
            t11 = MC_ingreso == "-"
            if t11:
                t12 = await async_input("ingresa operando 1:")
                MC_op1 = t12
                t13 = await async_input("ingresa operando 2:")
                MC_op2 = t13
                t14 = weak_arithmetic(MC_op1) - weak_arithmetic(MC_op2)
                MC_resultado = t14
                t15 = str("resultado: ") + str(MC_resultado)
                await async_print(t15)
            else:
                t16 = MC_ingreso == "*"
                if t16:
                    t17 = await async_input("ingresa operando 1:")
                    MC_op1 = t17
                    t18 = await async_input("ingresa operando 2:")
                    MC_op2 = t18
                    t19 = weak_arithmetic(MC_op1) * weak_arithmetic(MC_op2)
                    MC_resultado = t19
                    t20 = str("resultado: ") + str(MC_resultado)
                    await async_print(t20)
                else:
                    t21 = MC_ingreso == "/"
                    if t21:
                        t22 = await async_input("ingresa operando 1:")
                        MC_op1 = t22
                        t23 = await async_input("ingresa operando 2:")
                        MC_op2 = t23
                        t24 = weak_arithmetic(MC_op1) / weak_arithmetic(MC_op2)
                        MC_resultado = t24
                        t25 = str("resultado: ") + str(MC_resultado)
                        await async_print(t25)
                    else:
                        t26 = MC_ingreso == "s"
                        if t26:
                            await async_print("Adios...")
                            MC_flag = 0
                        else:
                            await async_print("Por favor ingresa una opción valida")
### FIN MCScript ###
