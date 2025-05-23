from CuentaAhorro import CuentaAhorro
# ejecutar desde aca

cuenta = CuentaAhorro("Juan Perez", "12345678", "2000/01/01", 1000)

cuenta.depositar(500)  #se espera que el saldo sea 1000 + 500 + interés (0.1%) = 1501.5
print("Saldo esperado: 1501.5")
print("Saldo real:", cuenta.obtener_saldo())

cuenta.extraer(500) #se espera que el saldo sea 1501.5 - 500 + interés (0.1%) = 1002.50
print("Saldo esperado: 1002.50 (aproximado)")
print("Saldo real:", cuenta.obtener_saldo())

saldo_antes = cuenta.obtener_saldo()
cuenta.depositar(0)
print("Saldo antes:", saldo_antes)
print("Saldo despues:", cuenta.obtener_saldo())
