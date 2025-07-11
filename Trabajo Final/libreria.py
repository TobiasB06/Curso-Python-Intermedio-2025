import flet as ft
import sqlite3
from datetime import datetime
import re

class BibliotecaApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Sistema de Gestión de Biblioteca"
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        self.categorias = []
        self.usuarios = []
        self.libros = []
        self.prestamos = []
        
        self.editando_libro = None
        self.editando_usuario = None
        self.editando_categoria = None
        self.editando_prestamo = None
        
        self.setup_database()
        self.setup_ui()
        
    def setup_database(self):
        self.conn = sqlite3.connect('Libreria.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
    def ejecutar_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.mostrar_mensaje(f"Error en base de datos: {str(e)}", es_error=True)
            return False
    
    def obtener_datos(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            self.mostrar_mensaje(f"Error al obtener datos: {str(e)}", es_error=True)
            return []
    
    def mostrar_mensaje(self, mensaje, es_error=False):
        snackbar = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=ft.Colors.RED_400 if es_error else ft.Colors.GREEN_400
        )
        self.page.snack_bar = snackbar
        self.page.overlay.append(self.page.snack_bar)
        self.page.snack_bar.open = True
        self.page.update()
    
    def validar_email(self, email):
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, email) is not None
    
    def validar_dni_unico(self, dni, id_usuario=None):
        query = "SELECT COUNT(*) FROM usuarios WHERE dni = ?"
        params = [dni]
        
        if id_usuario:
            query += " AND id_usuario != ?"
            params.append(id_usuario)
            
        result = self.obtener_datos(query, params)
        return result[0][0] == 0
    
    
    def cargar_categorias(self):
        """Carga las categorías desde la base de datos"""
        query = "SELECT id_categoria, nombre_categoria FROM categorias ORDER BY nombre_categoria"
        self.categorias = self.obtener_datos(query)
        self.actualizar_tabla_categorias()
        self.actualizar_dropdown_categorias()
    
    def actualizar_tabla_categorias(self):
        """Actualiza la tabla de categorías"""
        rows = []
        for categoria in self.categorias:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(categoria[0]))),
                        ft.DataCell(ft.Text(categoria[1])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar",
                                    on_click=lambda e, cat=categoria: self.editar_categoria(cat)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Eliminar",
                                    on_click=lambda e, cat=categoria: self.eliminar_categoria(cat[0])
                                )
                            ])
                        )
                    ]
                )
            )
        
        self.tabla_categorias.rows = rows
        self.page.update()
    
    def actualizar_dropdown_categorias(self):
        """Actualiza el dropdown de categorías en el formulario de libros"""
        if hasattr(self, 'categoria_dropdown'):
            self.categoria_dropdown.options = [
                ft.dropdown.Option(key=str(cat[0]), text=cat[1]) for cat in self.categorias
            ]
            self.page.update()
    
    def agregar_categoria(self, e):
        """Agrega una nueva categoría"""
        nombre = self.categoria_nombre_field.value.strip()
        
        if not nombre:
            self.mostrar_mensaje("El nombre de la categoría no puede estar vacío", es_error=True)
            return
        
        if self.editando_categoria:
            query = "UPDATE categorias SET nombre_categoria = ? WHERE id_categoria = ?"
            params = (nombre, self.editando_categoria[0])
            mensaje = "Categoría actualizada exitosamente"
        else:
            query = "INSERT INTO categorias (nombre_categoria) VALUES (?)"
            params = (nombre,)
            mensaje = "Categoría agregada exitosamente"
        
        if self.ejecutar_query(query, params):
            self.mostrar_mensaje(mensaje)
            self.limpiar_formulario_categoria()
            self.cargar_categorias()
    
    def editar_categoria(self, categoria):
        self.editando_categoria = categoria
        self.categoria_nombre_field.value = categoria[1]
        self.categoria_btn.text = "Actualizar Categoría"
        self.page.update()
    
    def eliminar_categoria(self, id_categoria):

        query = "SELECT COUNT(*) FROM libros WHERE id_categoria = ?"
        result = self.obtener_datos(query, (id_categoria,))
        
        if result[0][0] > 0:
            self.mostrar_mensaje("No se puede eliminar la categoría porque tiene libros asociados", es_error=True)
            return
        
        query = "DELETE FROM categorias WHERE id_categoria = ?"
        if self.ejecutar_query(query, (id_categoria,)):
            self.mostrar_mensaje("Categoría eliminada exitosamente")
            self.cargar_categorias()
    
    def limpiar_formulario_categoria(self):
        """Limpia el formulario de categorías"""
        self.categoria_nombre_field.value = ""
        self.categoria_btn.text = "Agregar Categoría"
        self.editando_categoria = None
        self.page.update()
    
    
    def cargar_usuarios(self):
        query = "SELECT id_usuario, nombre, apellido, dni, email FROM usuarios ORDER BY apellido, nombre"
        self.usuarios = self.obtener_datos(query)
        self.actualizar_tabla_usuarios()
        self.actualizar_dropdown_usuarios()
    
    def actualizar_tabla_usuarios(self):

        rows = []
        for usuario in self.usuarios:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(usuario[0]))),
                        ft.DataCell(ft.Text(usuario[1])),
                        ft.DataCell(ft.Text(usuario[2])),
                        ft.DataCell(ft.Text(usuario[3])),
                        ft.DataCell(ft.Text(usuario[4])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar",
                                    on_click=lambda e, user=usuario: self.editar_usuario(user)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Eliminar",
                                    on_click=lambda e, user=usuario: self.eliminar_usuario(user[0])
                                )
                            ])
                        )
                    ]
                )
            )
        
        self.tabla_usuarios.rows = rows
        self.page.update()
    
    def actualizar_dropdown_usuarios(self):

        if hasattr(self, 'usuario_dropdown'):
            self.usuario_dropdown.options = [
                ft.dropdown.Option(key=str(user[0]), text=f"{user[1]} {user[2]} - {user[3]}") 
                for user in self.usuarios
            ]
            self.page.update()
    
    def agregar_usuario(self, e):
        nombre = self.usuario_nombre_field.value.strip()
        apellido = self.usuario_apellido_field.value.strip()
        dni = self.usuario_dni_field.value.strip()
        email = self.usuario_email_field.value.strip()
        
        if not all([nombre, apellido, dni, email]):
            self.mostrar_mensaje("Todos los campos son obligatorios", es_error=True)
            return
        
        if not self.validar_email(email):
            self.mostrar_mensaje("El formato del email no es válido", es_error=True)
            return
        
        if not self.validar_dni_unico(dni, self.editando_usuario[0] if self.editando_usuario else None):
            self.mostrar_mensaje("Ya existe un usuario con ese DNI", es_error=True)
            return
        
        if self.editando_usuario:
            query = "UPDATE usuarios SET nombre = ?, apellido = ?, dni = ?, email = ? WHERE id_usuario = ?"
            params = (nombre, apellido, dni, email, self.editando_usuario[0])
            mensaje = "Usuario actualizado exitosamente"
        else:
            query = "INSERT INTO usuarios (nombre, apellido, dni, email) VALUES (?, ?, ?, ?)"
            params = (nombre, apellido, dni, email)
            mensaje = "Usuario agregado exitosamente"
        
        if self.ejecutar_query(query, params):
            self.mostrar_mensaje(mensaje)
            self.limpiar_formulario_usuario()
            self.cargar_usuarios()
    
    def editar_usuario(self, usuario):
        self.editando_usuario = usuario
        self.usuario_nombre_field.value = usuario[1]
        self.usuario_apellido_field.value = usuario[2]
        self.usuario_dni_field.value = usuario[3]
        self.usuario_email_field.value = usuario[4]
        self.usuario_btn.text = "Actualizar Usuario"
        self.page.update()
    
    def eliminar_usuario(self, id_usuario):
        query = "SELECT COUNT(*) FROM prestamos WHERE id_usuario = ? AND devuelto = 0"
        result = self.obtener_datos(query, (id_usuario,))
        
        if result[0][0] > 0:
            self.mostrar_mensaje("No se puede eliminar el usuario porque tiene préstamos pendientes", es_error=True)
            return
        
        query = "DELETE FROM usuarios WHERE id_usuario = ?"
        if self.ejecutar_query(query, (id_usuario,)):
            self.mostrar_mensaje("Usuario eliminado exitosamente")
            self.cargar_usuarios()
    
    def limpiar_formulario_usuario(self):
        self.usuario_nombre_field.value = ""
        self.usuario_apellido_field.value = ""
        self.usuario_dni_field.value = ""
        self.usuario_email_field.value = ""
        self.usuario_btn.text = "Agregar Usuario"
        self.editando_usuario = None
        self.page.update()
    
    
    def cargar_libros(self):
        query = """
        SELECT l.id_libro, l.titulo, l.autor, l.año, l.id_categoria, c.nombre_categoria, 
               l.disponible, l.link_imagen
        FROM libros l
        LEFT JOIN categorias c ON l.id_categoria = c.id_categoria
        ORDER BY l.titulo
        """
        self.libros = self.obtener_datos(query)
        self.actualizar_tabla_libros()
        self.actualizar_dropdown_libros()
    
    def mostrar_imagen_modal(self, link_imagen):
        print(f"Mostrando imagen: {link_imagen}")
        if not link_imagen:
            self.mostrar_mensaje("No hay imagen disponible", es_error=True)
            print("No hay imagen disponible")
            return
        def cerrar_dialogo(e):
            self.dialog.open = False
            self.page.update()
        dlg = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=ft.Image(src=link_imagen, width=500, height=700, fit=ft.ImageFit.CONTAIN),
                padding=20,
                alignment=ft.alignment.center
            ),
            actions=[ft.TextButton("Cerrar", on_click=cerrar_dialogo)]
        )
        self.dialog = dlg
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()
    
    def actualizar_tabla_libros(self):
        rows = []
        for libro in self.libros:
            disponible_text = "Sí" if libro[6] else "No"
            # Imagen en miniatura (80x80), click para modal
            def crear_click_imagen(link_imagen):
                def mostrar_modal(e):
                    self.mostrar_imagen_modal(link_imagen)
                return mostrar_modal
            img_widget = ft.Container(
                content=ft.Image(
                    src=libro[7] if libro[7] else "",
                    width=80,
                    height=80,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(8),
                    tooltip="Ver imagen"
                ),
                on_click=crear_click_imagen(libro[7]),
                ink=True,
                bgcolor=ft.Colors.BROWN_100,
                border_radius=ft.border_radius.all(8),
                padding=2
            )
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(libro[0]))),
                        ft.DataCell(ft.Text(libro[1])),
                        ft.DataCell(ft.Text(libro[2])),
                        ft.DataCell(ft.Text(str(libro[3]))),
                        ft.DataCell(ft.Text(libro[5] if libro[5] else "Sin categoría")),
                        ft.DataCell(ft.Text(disponible_text)),
                        ft.DataCell(img_widget),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar",
                                    on_click=lambda e, lib=libro: self.editar_libro(lib)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Eliminar",
                                    on_click=lambda e, lib=libro: self.eliminar_libro(lib[0])
                                )
                            ])
                        )
                    ]
                )
            )
        self.tabla_libros.rows = rows
        self.page.update()
    
    def actualizar_dropdown_libros(self):

        if hasattr(self, 'libro_dropdown'):
            libros_disponibles = [libro for libro in self.libros]  # Solo disponibles
            self.libro_dropdown.options = [
                ft.dropdown.Option(key=str(libro[0]), text=f"{libro[1]} - {libro[2]}") 
                for libro in libros_disponibles
            ]
            self.page.update()
    
    def agregar_libro(self, e):
        titulo = self.libro_titulo_field.value.strip()
        autor = self.libro_autor_field.value.strip()
        año = self.libro_año_field.value.strip()
        categoria_id = self.categoria_dropdown.value
        disponible = self.libro_disponible_checkbox.value
        link_imagen = self.libro_imagen_field.value.strip()
        
        # Validación de campos vacíos
        campos_vacios = []
        if not titulo:
            campos_vacios.append("Título")
        if not autor:
            campos_vacios.append("Autor")
        if not año:
            campos_vacios.append("Año")
        if not categoria_id:
            campos_vacios.append("Categoría")
            
        if campos_vacios:
            self.mostrar_mensaje(f"Los siguientes campos son obligatorios: {', '.join(campos_vacios)}", es_error=True)
            return
        
        # Validación del año
        try:
            año_int = int(año)
            if año_int <= 0 or año_int > 10000:
                self.mostrar_mensaje("El año debe ser un número entre 1 y 10000", es_error=True)
                return
        except ValueError:
            self.mostrar_mensaje("El año debe ser un número válido", es_error=True)
            return
        
        if self.editando_libro:
            query = """UPDATE libros SET titulo = ?, autor = ?, año = ?, id_categoria = ?, 
                      disponible = ?, link_imagen = ? WHERE id_libro = ?"""
            params = (titulo, autor, año_int, categoria_id, disponible, link_imagen, self.editando_libro[0])
            mensaje = "Libro actualizado exitosamente"
        else:
            query = """INSERT INTO libros (titulo, autor, año, id_categoria, disponible, link_imagen) 
                      VALUES (?, ?, ?, ?, ?, ?)"""
            params = (titulo, autor, año_int, categoria_id, disponible, link_imagen)
            mensaje = "Libro agregado exitosamente"
        
        if self.ejecutar_query(query, params):
            self.mostrar_mensaje(mensaje)
            self.limpiar_formulario_libro()
            self.cargar_libros()
    
    def editar_libro(self, libro):
        self.editando_libro = libro
        self.libro_titulo_field.value = libro[1]
        self.libro_autor_field.value = libro[2]
        self.libro_año_field.value = str(libro[3])
        self.categoria_dropdown.value = str(libro[4]) if libro[4] else None
        self.libro_disponible_checkbox.value = libro[6]
        self.libro_imagen_field.value = libro[7] if libro[7] else ""
        self.libro_btn.text = "Actualizar Libro"
        self.page.update()
    
    def eliminar_libro(self, id_libro):

        query = "SELECT COUNT(*) FROM prestamos WHERE id_libro = ? AND devuelto = 0"
        result = self.obtener_datos(query, (id_libro,))
        
        if result[0][0] > 0:
            self.mostrar_mensaje("No se puede eliminar el libro porque tiene préstamos pendientes", es_error=True)
            return
        
        query = "DELETE FROM libros WHERE id_libro = ?"
        if self.ejecutar_query(query, (id_libro,)):
            self.mostrar_mensaje("Libro eliminado exitosamente")
            self.cargar_libros()
    
    def limpiar_formulario_libro(self):
        self.libro_titulo_field.value = ""
        self.libro_autor_field.value = ""
        self.libro_año_field.value = ""
        self.categoria_dropdown.key = "Select"
        self.categoria_dropdown.value = ""
        self.libro_disponible_checkbox.value = True
        self.libro_imagen_field.value = ""
        self.libro_btn.text = "Agregar Libro"
        self.editando_libro = None
        self.page.update()
    
    
    def cargar_prestamos(self):
        query = """
        SELECT p.id_prestamo, p.id_libro, l.titulo, l.autor, p.id_usuario, 
               u.nombre || ' ' || u.apellido as usuario, p.fecha_prestamo, p.devuelto
        FROM prestamos p
        JOIN libros l ON p.id_libro = l.id_libro
        JOIN usuarios u ON p.id_usuario = u.id_usuario
        ORDER BY p.fecha_prestamo DESC
        """
        self.prestamos = self.obtener_datos(query)
        self.actualizar_tabla_prestamos()
    
    def actualizar_tabla_prestamos(self):
        rows = []
        for prestamo in self.prestamos:
            estado_text = "Devuelto" if prestamo[7] else "Pendiente"
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(prestamo[0]))),
                        ft.DataCell(ft.Text(f"{prestamo[2]} - {prestamo[3]}")),
                        ft.DataCell(ft.Text(prestamo[5])),
                        ft.DataCell(ft.Text(prestamo[6])),
                        ft.DataCell(ft.Text(estado_text)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.ASSIGNMENT_RETURN,
                                    tooltip="Devolver",
                                    on_click=lambda e, prest=prestamo: self.devolver_libro(prest[0]),
                                    disabled=prestamo[7]  
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Eliminar",
                                    on_click=lambda e: self.eliminar_prestamo(prestamo[0])
                                )
                            ])
                        )
                    ]
                )
            )
        
        self.tabla_prestamos.rows = rows
        self.page.update()
    
    def agregar_prestamo(self, e):

        libro_id = self.libro_dropdown.value
        usuario_id = self.usuario_dropdown.value
        fecha = self.fecha_prestamo_field.value.strip()
        if not libro_id or not usuario_id:
            self.mostrar_mensaje("Debe seleccionar un libro y un usuario", es_error=True)
            return
        
        

        query = "INSERT INTO prestamos (id_libro, id_usuario, fecha_prestamo, devuelto) VALUES (?, ?, ?, 0)"
        params = (libro_id, usuario_id, fecha)
        

        query_libro = "UPDATE libros SET disponible = 0 WHERE id_libro = ?"
        
        if self.ejecutar_query(query, params) and self.ejecutar_query(query_libro, (libro_id,)):
            self.mostrar_mensaje("Préstamo registrado exitosamente")
            self.limpiar_formulario_prestamo()
            self.cargar_prestamos()
            self.cargar_libros()  
    
    def devolver_libro(self, id_prestamo):
        query = "SELECT id_libro FROM prestamos WHERE id_prestamo = ?"
        result = self.obtener_datos(query, (id_prestamo,))
        
        if not result:
            self.mostrar_mensaje("Préstamo no encontrado", es_error=True)
            return
        
        id_libro = result[0][0]

        query_prestamo = "UPDATE prestamos SET devuelto = 1 WHERE id_prestamo = ?"

        query_libro = "UPDATE libros SET disponible = 1 WHERE id_libro = ?"
        
        if self.ejecutar_query(query_prestamo, (id_prestamo,)) and self.ejecutar_query(query_libro, (id_libro,)):
            self.mostrar_mensaje("Libro devuelto exitosamente")
            self.cargar_prestamos()
            self.cargar_libros() 
    
    def eliminar_prestamo(self, id_prestamo):
        query = "SELECT id_libro, devuelto FROM prestamos WHERE id_prestamo = ?"
        result = self.obtener_datos(query, (id_prestamo,))
        if not result:
            self.mostrar_mensaje("Préstamo no encontrado", es_error=True)
            return
        
        id_libro, devuelto = result[0]
        
        if not devuelto:
            query_libro = "UPDATE libros SET disponible = 1 WHERE id_libro = ?"
            self.ejecutar_query(query_libro, (id_libro,))
        

        query = "DELETE FROM prestamos WHERE id_prestamo = ?"
        if self.ejecutar_query(query, (id_prestamo,)):
            self.mostrar_mensaje("Préstamo eliminado exitosamente")
            
            self.cargar_prestamos()
            self.cargar_libros() 
    
    def limpiar_formulario_prestamo(self):
        self.libro_dropdown.key = "Select"
        self.usuario_dropdown.key = "Select"
        self.libro_dropdown.value = ""
        self.usuario_dropdown.value = ""
        self.fecha_prestamo_field.value = datetime.now().strftime("%Y-%m-%d")
        self.page.update()
    
    def setup_ui(self):
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Libros", content=self.crear_tab_libros()),
                ft.Tab(text="Usuarios", content=self.crear_tab_usuarios()),
                ft.Tab(text="Categorías", content=self.crear_tab_categorias()),
                ft.Tab(text="Préstamos", content=self.crear_tab_prestamos()),
            ],
            tab_alignment=ft.TabAlignment.CENTER
            
        )
        
        self.page.add(
            ft.Container(
                content=self.tabs,
                padding=20,
                expand=True,
                bgcolor=ft.Colors.BROWN_100
            )
        )
        self.page.bgcolor = ft.Colors.BROWN_100
   
        self.cargar_categorias()
        self.cargar_usuarios()
        self.cargar_libros()
        self.cargar_prestamos()
    
    def crear_tab_libros(self):

        self.libro_titulo_field = ft.TextField(label="Título", width=300)
        self.libro_autor_field = ft.TextField(label="Autor", width=300)
        self.libro_año_field = ft.TextField(label="Año", width=150)
        self.categoria_dropdown = ft.Dropdown(label="Categoría", width=200)
        self.libro_disponible_checkbox = ft.Checkbox(label="Disponible", value=True, width=150)
        self.libro_imagen_field = ft.TextField(label="Link de imagen", width=400)

        self.libro_btn = ft.ElevatedButton(text="Agregar Libro", on_click=self.agregar_libro,
                                           style=ft.ButtonStyle(
                                               color=ft.Colors.WHITE, 
                                               bgcolor=ft.Colors.BROWN_200,
                                                  shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8))
                                               ))

        self.tabla_libros = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Título")),
                ft.DataColumn(ft.Text("Autor")),
                ft.DataColumn(ft.Text("Año")),
                ft.DataColumn(ft.Text("Categoría")),
                ft.DataColumn(ft.Text("Disponible")),
                ft.DataColumn(ft.Text("Imagen")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[],
           horizontal_lines= ft.border.BorderSide(3,color=ft.Colors.GREY_300),
           vertical_lines= ft.border.BorderSide(3,color=ft.Colors.GREY_300)
        )
        
        return ft.Column([
            ft.Text("Gestión de Libros", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Divider(),
            ft.Row([
                ft.Column([
                    ft.Row([
                        self.libro_titulo_field,
                        self.libro_autor_field,
                        self.libro_año_field,
                        self.categoria_dropdown
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([
                        self.libro_disponible_checkbox,
                        self.libro_imagen_field,
                        self.libro_btn,
                        ft.ElevatedButton(text="Limpiar", on_click=lambda e: self.limpiar_formulario_libro(),
                                          style=ft.ButtonStyle(
                                               color=ft.Colors.WHITE, 
                                               bgcolor=ft.Colors.BROWN_200,
                                                  shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8))
                                               ))
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Row([
                ft.Column(
                    [self.tabla_libros],
                    scroll=True,
                    expand=1
                )
            ], scroll=True, expand=1, vertical_alignment=ft.CrossAxisAlignment.START)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    def crear_tab_usuarios(self):

        self.usuario_nombre_field = ft.TextField(label="Nombre", width=200)
        self.usuario_apellido_field = ft.TextField(label="Apellido", width=200)
        self.usuario_dni_field = ft.TextField(label="DNI", width=150)
        self.usuario_email_field = ft.TextField(label="Email", width=250)
        
        self.usuario_btn = ft.ElevatedButton(text="Agregar Usuario", on_click=self.agregar_usuario,
                                          style=ft.ButtonStyle(
                                               color=ft.Colors.WHITE, 
                                               bgcolor=ft.Colors.BROWN_200,
                                                  shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8))
                                               ))

        self.tabla_usuarios = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Apellido")),
                ft.DataColumn(ft.Text("DNI")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[],
            horizontal_lines=ft.border.BorderSide(3, color=ft.Colors.GREY_300),
            vertical_lines=ft.border.BorderSide(3, color=ft.Colors.GREY_300)
        )
        
        return ft.Column([
            ft.Text("Gestión de Usuarios", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Divider(),
            ft.Row([
                ft.Column([
                    ft.Row([self.usuario_nombre_field, self.usuario_apellido_field], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.usuario_dni_field, self.usuario_email_field], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([
                        self.usuario_btn,
                        ft.ElevatedButton(text="Limpiar", on_click=lambda e: self.limpiar_formulario_usuario(),
                                          style=ft.ButtonStyle(
                                               color=ft.Colors.WHITE, 
                                               bgcolor=ft.Colors.BROWN_200,
                                                  shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8))
                                               ))
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Row([
                ft.Column(
                    [self.tabla_usuarios],
                    scroll=True,
                    expand=1
                )
            ], scroll=True, expand=1, vertical_alignment=ft.CrossAxisAlignment.START)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    def crear_tab_categorias(self):

        self.categoria_nombre_field = ft.TextField(label="Nombre de la categoría", width=300)
        

        self.categoria_btn = ft.ElevatedButton(text="Agregar Categoría", on_click=self.agregar_categoria,
                                          style=ft.ButtonStyle(
                                               color=ft.Colors.WHITE, 
                                               bgcolor=ft.Colors.BROWN_200,
                                                  shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8))
                                               ))
        

        self.tabla_categorias = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[],
            horizontal_lines=ft.border.BorderSide(3, color=ft.Colors.GREY_300),
            vertical_lines=ft.border.BorderSide(3, color=ft.Colors.GREY_300)
        )
        
        return ft.Column([
            ft.Text("Gestión de Categorías", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Divider(),
            ft.Row([
                ft.Column([
                    self.categoria_nombre_field,
                    ft.Row([
                        self.categoria_btn,
                        ft.ElevatedButton(text="Limpiar", on_click=lambda e: self.limpiar_formulario_categoria(),
                                          style=ft.ButtonStyle(
                                               color=ft.Colors.WHITE, 
                                               bgcolor=ft.Colors.BROWN_200,
                                                  shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8))
                                               ))
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Row([
                ft.Column(
                    [self.tabla_categorias],
                    scroll=True,
                    expand=1
                )
            ], scroll=True, expand=1, vertical_alignment=ft.CrossAxisAlignment.START)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    def handle_change(self, e, es_fecha=True):
        fecha_str = e.data[:10] 
        self.fecha_prestamo_field.value = datetime.strptime(fecha_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        self.page.update()


    def crear_tab_prestamos(self):
        self.libro_dropdown = ft.Dropdown(
            label="Seleccionar libro", 
            width=300,
            enable_filter=True,
            editable=True
        )
        self.usuario_dropdown = ft.Dropdown(label="Seleccionar usuario", width=300)
        self.fecha_prestamo_field = ft.TextField(label="Fecha del préstamo", width=200, read_only=True)
        self.fecha = ft.ElevatedButton(
            "Elegir fecha",
            icon=ft.Icons.DATE_RANGE,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE, 
                bgcolor=ft.Colors.BROWN_200,
                    shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8))
                ),
            color=ft.Colors.WHITE,
            height=50,
            
            on_click=lambda e: self.page.open(
                ft.DatePicker(
                    on_change=lambda e:self.handle_change(e,False),
                )
            ),
        )

        self.prestamo_btn = ft.ElevatedButton(text="Registrar Préstamo", on_click=self.agregar_prestamo,
                                          style=ft.ButtonStyle(
                                               color=ft.Colors.WHITE, 
                                               bgcolor=ft.Colors.BROWN_200,
                                                  shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8))
                                               ))
        

        self.tabla_prestamos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Libro")),
                ft.DataColumn(ft.Text("Usuario")),
                ft.DataColumn(ft.Text("Fecha Préstamo")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[],
            horizontal_lines=ft.border.BorderSide(3, color=ft.Colors.GREY_300),
            vertical_lines=ft.border.BorderSide(3, color=ft.Colors.GREY_300)
        )
        
        return ft.Column([
            ft.Text("Gestión de Préstamos", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Divider(),
            ft.Row([
                ft.Column([ 
                    ft.Row([self.libro_dropdown, self.usuario_dropdown, self.fecha, self.fecha_prestamo_field], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([
                        self.prestamo_btn,
                        ft.ElevatedButton(text="Limpiar", on_click=lambda e: self.limpiar_formulario_prestamo(),
                                          style=ft.ButtonStyle(
                                               color=ft.Colors.WHITE, 
                                               bgcolor=ft.Colors.BROWN_200,
                                                  shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8))
                                               ))
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Row([
                ft.Column(
                    [self.tabla_prestamos],
                    scroll=True,
                    expand=1
                )
            ], scroll=True, expand=1, vertical_alignment=ft.CrossAxisAlignment.START)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)


def main(page: ft.Page):
    app = BibliotecaApp(page)


if __name__ == "__main__":
    ft.app(target=main)