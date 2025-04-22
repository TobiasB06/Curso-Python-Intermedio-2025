def buscar_palabra(palabra, *args):
    return f"Palabra encontrada {palabra}" if palabra in args else "Palabra no encontrada"

entrada = input("Ingresar palabras separadas por espacios: ")
entrada = entrada.split()
palabra_a_buscar = input("Ingresar la palabra a buscar: ")

resultado = buscar_palabra(palabra_a_buscar, *entrada)
print(resultado)