def promedio(*args):
    resultado=(sum(args))/len(args)
    return resultado if args else "No se puede calcular el promedio de una lista vacia"
entrada = input("Ingresar numeros separados por espacios: ")

entrada = entrada.split()
entrada = [float(i) for i in entrada]

resultado = promedio(*entrada)

print(" El promedio es:",resultado)