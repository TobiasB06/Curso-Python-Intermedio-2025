
def suma(x,y):
    try:
        return x+y
    except TypeError:
        print("No se puede sumar un numero y una cadena")

resultado = suma(10,10)
print(resultado)

resultado = suma(1,"1")