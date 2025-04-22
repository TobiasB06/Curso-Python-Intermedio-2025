
contraseña_nueva = "12345"

try:
    with open("Contraseñas.txt", "r+") as archivo:
        archivo.write(contraseña_nueva)
    
except FileNotFoundError:
    
    print("No se encuentra el archivo")
    
    with open("Contraseñas.txt", "w") as archivo:
        archivo.write(contraseña_nueva)
finally:
    archivo.close()
    