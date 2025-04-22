def suma(*args):
    try:
        return sum(args) if len(args)>2 else "No se puede sumar menos de 2 numeros"
    except TypeError:
        print("No se puede sumar un numero y una cadena")

resultado = suma(10,10,10,20,30)
print(resultado)

resultado = suma(1)

print(resultado)
