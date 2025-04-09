dic = {
    "Nombre":"John",
    "Edad":"25"
    }

try:
    print("Nombre: ",dic["Nombre"],
          "Apellido: ",dic["Apellido"]
          )
except KeyError:
    print("No se encuentra la clave en el diccionario")
