from CuentaBancaria import CuentaBancaria  as cb

class CuentaAhorro(cb):
    def __init__(self, nombre_titular, dni_titular, fecha_nacimiento, saldo=0):
        super().__init__(nombre_titular, dni_titular, fecha_nacimiento, saldo)
        self._tasa_interes=0.001
    
    def validar_depositar(func):
        def wrapper(self, monto):
            if monto > 0:
                return func(self, monto)
            else:
                print("El monto a depositar debe ser mayor a 0")
        return wrapper
    
    def validar_extraccion(func):
        def wrapper(self, monto):
            if monto <= self.obtener_saldo():
                return func(self, monto)
            else:
                print("No posee saldo suficiente para esta operación")
        return wrapper
    
    @validar_depositar
    def depositar(self, monto):
        self.set_saldo(self.obtener_saldo() + monto)
        print(f"Se ha depositado {monto} a la cuenta de {self._nombre_titular}, su saldo es de: {self.obtener_saldo()}")
        interes=self.aplicar_tasa_de_interes(self.obtener_tasa_interes(), self.obtener_saldo())
        print(f"Se ha aplicado una tasa de interes de {interes} a la cuenta de {self._nombre_titular}, su saldo es de: {self.obtener_saldo()}")
        
    @validar_extraccion   
    def extraer(self, monto):
        self.set_saldo(self.obtener_saldo() - monto) 
        print(f"Se ha extraido {monto} de la cuenta de {self._nombre_titular}, su saldo es de: {self.obtener_saldo()}")
        interes=self.aplicar_tasa_de_interes(self.obtener_tasa_interes(), self.obtener_saldo())
        print(f"Se ha aplicado una tasa de interes de {interes} a la cuenta de {self._nombre_titular}, su saldo es de: {self.obtener_saldo()}")
    
    def aplicar_tasa_de_interes(self,interes,monto):
        self.set_saldo(self.obtener_saldo() + monto * interes)
        return monto * interes
        
    def obtener_tasa_interes(self):
        return self._tasa_interes
