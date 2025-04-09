
def division(Num1,Num2):
    try:
        return Num1 / Num2
    except ZeroDivisionError:
        print("No se puede dividir por 0")

resultado = division(10,5)
print(resultado)

resultado = division(10,0)
