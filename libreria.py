import flet as ft
import sqlite3
from datetime import datetime
from typing import List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = "biblioteca.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos y crea las tablas si no existen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crear tablas si no existen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_categoria TEXT NOT NULL UNIQUE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                dni TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS libros (
                id_libro INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                año INTEGER,
                id_categoria INTEGER,
                disponible BOOLEAN DEFAULT 1,
                link_imagen TEXT,
                FOREIGN KEY (id_categoria) REFERENCES categorias (id_categoria)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prestamos (
                id_prestamo INTEGER PRIMARY KEY AUTOINCREMENT,
                id_libro INTEGER,
                id_usuario INTEGER,
                fecha_prestamo TEXT NOT NULL,
                devuelto BOOLEAN DEFAULT 0,
                FOREIGN KEY (id_libro) REFERENCES libros (id_libro),
                FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Ejecuta una consulta y retorna los resultados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """Ejecuta una consulta de actualización"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Error en base de datos: {e}")
            return False

class CategoriasManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.selected_id = None
    
    def create_view(self, page: ft.Page) -> ft.Container:
        self.page = page
        
        # Campos del formulario
        self.nombre_field = ft.TextField(
            label="Nombre de la categoría",
            width=300,
            autofocus=True
        )
        
        # Botones
        self.save_btn = ft.ElevatedButton(
            "Guardar",
            on_click=self.save_categoria,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )
        
        self.cancel_btn = ft.ElevatedButton(
            "Cancelar",
            on_click=self.cancel_edit,
            bgcolor=ft.colors.GREY,
            color=ft.colors.WHITE
        )
        
        # Tabla de datos
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )
        
        # Mensaje de estado
        self.status_text = ft.Text("", color=ft.colors.GREEN)
        
        self.load_data()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Gestión de Categorías", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    self.nombre_field,
                    self.save_btn,
                    self.cancel_btn
                ]),
                self.status_text,
                ft.Divider(),
                ft.Container(
                    content=self.data_table,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=5,
                    padding=10
                )
            ]),
            padding=20
        )
    
    def load_data(self):
        """Carga los datos en la tabla"""
        categorias = self.db.execute_query("SELECT * FROM categorias ORDER BY nombre_categoria")
        
        self.data_table.rows.clear()
        for categoria in categorias:
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(categoria['nombre_categoria'])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    ft.icons.EDIT,
                                    tooltip="Editar",
                                    on_click=lambda e, cat_id=categoria['id_categoria']: self.edit_categoria(cat_id)
                                ),
                                ft.IconButton(
                                    ft.icons.DELETE,
                                    tooltip="Eliminar",
                                    on_click=lambda e, cat_id=categoria['id_categoria']: self.delete_categoria(cat_id)
                                )
                            ])
                        )
                    ]
                )
            )
        self.page.update()
    
    def save_categoria(self, e):
        """Guarda o actualiza una categoría"""
        nombre = self.nombre_field.value.strip()
        
        if not nombre:
            self.show_message("El nombre es requerido", ft.colors.RED)
            return
        
        if self.selected_id:
            # Actualizar
            success = self.db.execute_update(
                "UPDATE categorias SET nombre_categoria = ? WHERE id_categoria = ?",
                (nombre, self.selected_id)
            )
            message = "Categoría actualizada correctamente" if success else "Error al actualizar"
        else:
            # Crear
            success = self.db.execute_update(
                "INSERT INTO categorias (nombre_categoria) VALUES (?)",
                (nombre,)
            )
            message = "Categoría creada correctamente" if success else "Error al crear (posible nombre duplicado)"
        
        if success:
            self.clear_form()
            self.load_data()
            self.show_message(message, ft.colors.GREEN)
        else:
            self.show_message(message, ft.colors.RED)
    
    def edit_categoria(self, categoria_id):
        """Carga los datos para editar"""
        categoria = self.db.execute_query(
            "SELECT * FROM categorias WHERE id_categoria = ?",
            (categoria_id,)
        )
        
        if categoria:
            self.selected_id = categoria_id
            self.nombre_field.value = categoria[0]['nombre_categoria']
            self.save_btn.text = "Actualizar"
            self.page.update()
    
    def delete_categoria(self, categoria_id):
        """Elimina una categoría"""
        # Verificar si tiene libros asociados
        libros = self.db.execute_query(
            "SELECT COUNT(*) as count FROM libros WHERE id_categoria = ?",
            (categoria_id,)
        )
        
        if libros[0]['count'] > 0:
            self.show_message("No se puede eliminar: tiene libros asociados", ft.colors.RED)
            return
        
        success = self.db.execute_update(
            "DELETE FROM categorias WHERE id_categoria = ?",
            (categoria_id,)
        )
        
        if success:
            self.load_data()
            self.show_message("Categoría eliminada correctamente", ft.colors.GREEN)
        else:
            self.show_message("Error al eliminar", ft.colors.RED)
    
    def cancel_edit(self, e):
        """Cancela la edición"""
        self.clear_form()
    
    def clear_form(self):
        """Limpia el formulario"""
        self.selected_id = None
        self.nombre_field.value = ""
        self.save_btn.text = "Guardar"
        self.page.update()
    
    def show_message(self, message: str, color):
        """Muestra un mensaje de estado"""
        self.status_text.value = message
        self.status_text.color = color
        self.page.update()

class UsuariosManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.selected_id = None
    
    def create_view(self, page: ft.Page) -> ft.Container:
        self.page = page
        
        # Campos del formulario
        self.nombre_field = ft.TextField(label="Nombre", width=200)
        self.apellido_field = ft.TextField(label="Apellido", width=200)
        self.dni_field = ft.TextField(label="DNI", width=150)
        self.email_field = ft.TextField(label="Email", width=250)
        
        # Botones
        self.save_btn = ft.ElevatedButton(
            "Guardar",
            on_click=self.save_usuario,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )
        
        self.cancel_btn = ft.ElevatedButton(
            "Cancelar",
            on_click=self.cancel_edit,
            bgcolor=ft.colors.GREY,
            color=ft.colors.WHITE
        )
        
        # Tabla de datos
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Apellido")),
                ft.DataColumn(ft.Text("DNI")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )
        
        # Mensaje de estado
        self.status_text = ft.Text("", color=ft.colors.GREEN)
        
        self.load_data()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Gestión de Usuarios", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    self.nombre_field,
                    self.apellido_field,
                    self.dni_field,
                    self.email_field
                ]),
                ft.Row([
                    self.save_btn,
                    self.cancel_btn
                ]),
                self.status_text,
                ft.Divider(),
                ft.Container(
                    content=self.data_table,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=5,
                    padding=10
                )
            ]),
            padding=20
        )
    
    def load_data(self):
        """Carga los datos en la tabla"""
        usuarios = self.db.execute_query("SELECT * FROM usuarios ORDER BY apellido, nombre")
        
        self.data_table.rows.clear()
        for usuario in usuarios:
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(usuario['nombre'])),
                        ft.DataCell(ft.Text(usuario['apellido'])),
                        ft.DataCell(ft.Text(usuario['dni'])),
                        ft.DataCell(ft.Text(usuario['email'])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    ft.icons.EDIT,
                                    tooltip="Editar",
                                    on_click=lambda e, user_id=usuario['id_usuario']: self.edit_usuario(user_id)
                                ),
                                ft.IconButton(
                                    ft.icons.DELETE,
                                    tooltip="Eliminar",
                                    on_click=lambda e, user_id=usuario['id_usuario']: self.delete_usuario(user_id)
                                )
                            ])
                        )
                    ]
                )
            )
        self.page.update()
    
    def save_usuario(self, e):
        """Guarda o actualiza un usuario"""
        nombre = self.nombre_field.value.strip()
        apellido = self.apellido_field.value.strip()
        dni = self.dni_field.value.strip()
        email = self.email_field.value.strip()
        
        # Validaciones
        if not all([nombre, apellido, dni, email]):
            self.show_message("Todos los campos son requeridos", ft.colors.RED)
            return
        
        if '@' not in email:
            self.show_message("Email inválido", ft.colors.RED)
            return
        
        if self.selected_id:
            # Actualizar
            success = self.db.execute_update(
                "UPDATE usuarios SET nombre = ?, apellido = ?, dni = ?, email = ? WHERE id_usuario = ?",
                (nombre, apellido, dni, email, self.selected_id)
            )
            message = "Usuario actualizado correctamente" if success else "Error al actualizar (DNI duplicado?)"
        else:
            # Crear
            success = self.db.execute_update(
                "INSERT INTO usuarios (nombre, apellido, dni, email) VALUES (?, ?, ?, ?)",
                (nombre, apellido, dni, email)
            )
            message = "Usuario creado correctamente" if success else "Error al crear (DNI duplicado?)"
        
        if success:
            self.clear_form()
            self.load_data()
            self.show_message(message, ft.colors.GREEN)
        else:
            self.show_message(message, ft.colors.RED)
    
    def edit_usuario(self, usuario_id):
        """Carga los datos para editar"""
        usuario = self.db.execute_query(
            "SELECT * FROM usuarios WHERE id_usuario = ?",
            (usuario_id,)
        )
        
        if usuario:
            self.selected_id = usuario_id
            user_data = usuario[0]
            self.nombre_field.value = user_data['nombre']
            self.apellido_field.value = user_data['apellido']
            self.dni_field.value = user_data['dni']
            self.email_field.value = user_data['email']
            self.save_btn.text = "Actualizar"
            self.page.update()
    
    def delete_usuario(self, usuario_id):
        """Elimina un usuario"""
        # Verificar si tiene préstamos
        prestamos = self.db.execute_query(
            "SELECT COUNT(*) as count FROM prestamos WHERE id_usuario = ?",
            (usuario_id,)
        )
        
        if prestamos[0]['count'] > 0:
            self.show_message("No se puede eliminar: tiene préstamos asociados", ft.colors.RED)
            return
        
        success = self.db.execute_update(
            "DELETE FROM usuarios WHERE id_usuario = ?",
            (usuario_id,)
        )
        
        if success:
            self.load_data()
            self.show_message("Usuario eliminado correctamente", ft.colors.GREEN)
        else:
            self.show_message("Error al eliminar", ft.colors.RED)
    
    def cancel_edit(self, e):
        """Cancela la edición"""
        self.clear_form()
    
    def clear_form(self):
        """Limpia el formulario"""
        self.selected_id = None
        self.nombre_field.value = ""
        self.apellido_field.value = ""
        self.dni_field.value = ""
        self.email_field.value = ""
        self.save_btn.text = "Guardar"
        self.page.update()
    
    def show_message(self, message: str, color):
        """Muestra un mensaje de estado"""
        self.status_text.value = message
        self.status_text.color = color
        self.page.update()

class LibrosManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.selected_id = None
    
    def create_view(self, page: ft.Page) -> ft.Container:
        self.page = page
        
        # Campos del formulario
        self.titulo_field = ft.TextField(label="Título", width=300)
        self.autor_field = ft.TextField(label="Autor", width=200)
        self.año_field = ft.TextField(label="Año", width=100)
        self.categoria_dropdown = ft.Dropdown(label="Categoría", width=200)
        self.disponible_checkbox = ft.Checkbox(label="Disponible", value=True)
        self.imagen_field = ft.TextField(label="Link de imagen", width=300)
        
        # Cargar categorías
        self.load_categorias()
        
        # Botones
        self.save_btn = ft.ElevatedButton(
            "Guardar",
            on_click=self.save_libro,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )
        
        self.cancel_btn = ft.ElevatedButton(
            "Cancelar",
            on_click=self.cancel_edit,
            bgcolor=ft.colors.GREY,
            color=ft.colors.WHITE
        )
        
        # Tabla de datos
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Título")),
                ft.DataColumn(ft.Text("Autor")),
                ft.DataColumn(ft.Text("Año")),
                ft.DataColumn(ft.Text("Categoría")),
                ft.DataColumn(ft.Text("Disponible")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )
        
        # Mensaje de estado
        self.status_text = ft.Text("", color=ft.colors.GREEN)
        
        self.load_data()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Gestión de Libros", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    self.titulo_field,
                    self.autor_field,
                    self.año_field
                ]),
                ft.Row([
                    self.categoria_dropdown,
                    self.disponible_checkbox
                ]),
                ft.Row([
                    self.imagen_field
                ]),
                ft.Row([
                    self.save_btn,
                    self.cancel_btn
                ]),
                self.status_text,
                ft.Divider(),
                ft.Container(
                    content=self.data_table,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=5,
                    padding=10
                )
            ]),
            padding=20
        )
    
    def load_categorias(self):
        """Carga las categorías en el dropdown"""
        categorias = self.db.execute_query("SELECT * FROM categorias ORDER BY nombre_categoria")
        self.categoria_dropdown.options = [
            ft.dropdown.Option(str(cat['id_categoria']), cat['nombre_categoria'])
            for cat in categorias
        ]
    
    def load_data(self):
        """Carga los datos en la tabla"""
        libros = self.db.execute_query("""
            SELECT l.*, c.nombre_categoria 
            FROM libros l 
            LEFT JOIN categorias c ON l.id_categoria = c.id_categoria 
            ORDER BY l.titulo
        """)
        
        self.data_table.rows.clear()
        for libro in libros:
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(libro['titulo'])),
                        ft.DataCell(ft.Text(libro['autor'])),
                        ft.DataCell(ft.Text(str(libro['año']) if libro['año'] else "")),
                        ft.DataCell(ft.Text(libro['nombre_categoria'] or "Sin categoría")),
                        ft.DataCell(ft.Text("Sí" if libro['disponible'] else "No")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    ft.icons.EDIT,
                                    tooltip="Editar",
                                    on_click=lambda e, book_id=libro['id_libro']: self.edit_libro(book_id)
                                ),
                                ft.IconButton(
                                    ft.icons.DELETE,
                                    tooltip="Eliminar",
                                    on_click=lambda e, book_id=libro['id_libro']: self.delete_libro(book_id)
                                )
                            ])
                        )
                    ]
                )
            )
        self.page.update()
    
    def save_libro(self, e):
        """Guarda o actualiza un libro"""
        titulo = self.titulo_field.value.strip()
        autor = self.autor_field.value.strip()
        año_str = self.año_field.value.strip()
        categoria_id = self.categoria_dropdown.value
        disponible = self.disponible_checkbox.value
        imagen = self.imagen_field.value.strip()
        
        # Validaciones
        if not all([titulo, autor]):
            self.show_message("Título y autor son requeridos", ft.colors.RED)
            return
        
        año = None
        if año_str:
            try:
                año = int(año_str)
            except ValueError:
                self.show_message("El año debe ser un número", ft.colors.RED)
                return
        
        if self.selected_id:
            # Actualizar
            success = self.db.execute_update(
                "UPDATE libros SET titulo = ?, autor = ?, año = ?, id_categoria = ?, disponible = ?, link_imagen = ? WHERE id_libro = ?",
                (titulo, autor, año, categoria_id, disponible, imagen, self.selected_id)
            )
            message = "Libro actualizado correctamente" if success else "Error al actualizar"
        else:
            # Crear
            success = self.db.execute_update(
                "INSERT INTO libros (titulo, autor, año, id_categoria, disponible, link_imagen) VALUES (?, ?, ?, ?, ?, ?)",
                (titulo, autor, año, categoria_id, disponible, imagen)
            )
            message = "Libro creado correctamente" if success else "Error al crear"
        
        if success:
            self.clear_form()
            self.load_data()
            self.show_message(message, ft.colors.GREEN)
        else:
            self.show_message(message, ft.colors.RED)
    
    def edit_libro(self, libro_id):
        """Carga los datos para editar"""
        libro = self.db.execute_query(
            "SELECT * FROM libros WHERE id_libro = ?",
            (libro_id,)
        )
        
        if libro:
            self.selected_id = libro_id
            book_data = libro[0]
            self.titulo_field.value = book_data['titulo']
            self.autor_field.value = book_data['autor']
            self.año_field.value = str(book_data['año']) if book_data['año'] else ""
            self.categoria_dropdown.value = str(book_data['id_categoria']) if book_data['id_categoria'] else None
            self.disponible_checkbox.value = bool(book_data['disponible'])
            self.imagen_field.value = book_data['link_imagen'] or ""
            self.save_btn.text = "Actualizar"
            self.page.update()
    
    def delete_libro(self, libro_id):
        """Elimina un libro"""
        # Verificar si tiene préstamos
        prestamos = self.db.execute_query(
            "SELECT COUNT(*) as count FROM prestamos WHERE id_libro = ?",
            (libro_id,)
        )
        
        if prestamos[0]['count'] > 0:
            self.show_message("No se puede eliminar: tiene préstamos asociados", ft.colors.RED)
            return
        
        success = self.db.execute_update(
            "DELETE FROM libros WHERE id_libro = ?",
            (libro_id,)
        )
        
        if success:
            self.load_data()
            self.show_message("Libro eliminado correctamente", ft.colors.GREEN)
        else:
            self.show_message("Error al eliminar", ft.colors.RED)
    
    def cancel_edit(self, e):
        """Cancela la edición"""
        self.clear_form()
    
    def clear_form(self):
        """Limpia el formulario"""
        self.selected_id = None
        self.titulo_field.value = ""
        self.autor_field.value = ""
        self.año_field.value = ""
        self.categoria_dropdown.value = None
        self.disponible_checkbox.value = True
        self.imagen_field.value = ""
        self.save_btn.text = "Guardar"
        self.page.update()
    
    def show_message(self, message: str, color):
        """Muestra un mensaje de estado"""
        self.status_text.value = message
        self.status_text.color = color
        self.page.update()

class PrestamosManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.selected_id = None
    
    def create_view(self, page: ft.Page) -> ft.Container:
        self.page = page
        
        # Campos del formulario
        self.libro_dropdown = ft.Dropdown(label="Libro", width=300)
        self.usuario_dropdown = ft.Dropdown(label="Usuario", width=250)
        self.fecha_field = ft.TextField(
            label="Fecha (YYYY-MM-DD)",
            width=150,
            value=datetime.now().strftime("%Y-%m-%d")
        )
        self.devuelto_checkbox = ft.Checkbox(label="Devuelto", value=False)
        
        # Cargar datos para dropdowns
        self.load_libros()
        self.load_usuarios()
        
        # Botones
        self.save_btn = ft.ElevatedButton(
            "Guardar",
            on_click=self.save_prestamo,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )
        
        self.cancel_btn = ft.ElevatedButton(
            "Cancelar",
            on_click=self.cancel_edit,
            bgcolor=ft.colors.GREY,
            color=ft.colors.WHITE
        )
        
        # Tabla de datos
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Libro")),
                ft.DataColumn(ft.Text("Usuario")),
                ft.DataColumn(ft.Text("Fecha")),
                ft.DataColumn(ft.Text("Devuelto")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )
        
        # Mensaje de estado
        self.status_text = ft.Text("", color=ft.colors.GREEN)
        
        self.load_data()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Gestión de Préstamos", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    self.libro_dropdown,
                    self.usuario_dropdown,
                    self.fecha_field
                ]),
                ft.Row([
                    self.devuelto_checkbox
                ]),
                ft.Row([
                    self.save_btn,
                    self.cancel_btn
                ]),
                self.status_text,
                ft.Divider(),
                ft.Container(
                    content=self.data_table,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=5,
                    padding=10
                )
            ]),
            padding=20
        )
    
    def load_libros(self):
        """Carga los libros disponibles en el dropdown"""
        libros = self.db.execute_query("SELECT * FROM libros WHERE disponible = 1 ORDER BY titulo")
        self.libro_dropdown.options = [
            ft.dropdown.Option(str(libro['id_libro']), libro['titulo'])
            for libro in libros
        ]
    
    def load_usuarios(self):
        """Carga los usuarios en el dropdown"""
        usuarios = self.db.execute_query("SELECT * FROM usuarios ORDER BY apellido, nombre")
        self.usuario_dropdown.options = [
            ft.dropdown.Option(str(user['id_usuario']), f"{user['apellido']}, {user['nombre']}")
            for user in usuarios
        ]
    
    def load_data(self):
        """Carga los datos en la tabla"""
        prestamos = self.db.execute_query("""
            SELECT p.*, l.titulo, u.nombre, u.apellido 
            FROM prestamos p 
            JOIN libros l ON p.id_libro = l.id_libro 
            JOIN usuarios u ON p.id_usuario = u.id_usuario 
            ORDER BY p.fecha_prestamo DESC
        """)
        
        self.data_table.rows.clear()
        for prestamo in prestamos:
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(prestamo['titulo'])),
                        ft.DataCell(ft.Text(f"{prestamo['apellido']}, {prestamo['nombre']}")),
                        ft.DataCell(ft.Text(prestamo['fecha_prestamo'])),
                        ft.DataCell(ft.Text("Sí" if prestamo['devuelto'] else "No")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    ft.icons.EDIT,
                                    tooltip="Editar",
                                    on_click=lambda e, prest_id=prestamo['id_prestamo']: self.edit_prestamo(prest_id)
                                ),
                                ft.IconButton(
                                    ft.icons.DELETE,
                                    tooltip="Eliminar",
                                    on_click=lambda e, prest_id=prestamo['id_prestamo']: self.delete_prestamo(prest_id)
                                )
                            ])
                        )
                    ]
                )
            )
        self.page.update()
    
    def save_prestamo(self, e):
        """Guarda o actualiza un préstamo"""
        libro_id = self.libro_dropdown.value
        usuario_id = self.usuario_dropdown.value
        fecha = self.fecha_field.value.strip()
        devuelto = self.devuelto_checkbox.value
        
        # Validaciones
        if not all([libro_id, usuario_id, fecha]):
            self.show_message("Todos los campos son requeridos", ft.colors.RED)
            return
        
        # Validar formato de fecha
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            self.show_message("Formato de fecha inválido (YYYY-MM-DD)", ft.colors.RED)
            return
        
        if self.selected_id:
            # Actualizar
            success = self.db.execute_update(
                "UPDATE prestamos SET id_libro = ?, id_usuario = ?, fecha_prestamo = ?, devuelto = ? WHERE id_prestamo = ?",
                (libro_id, usuario_id, fecha, devuelto, self.selected_id)
            )
            message = "Préstamo actualizado correctamente" if success else "Error al actualizar"
        else:
            # Crear
            success = self.db.execute_update(
                "INSERT INTO prestamos (id_libro, id_usuario, fecha_prestamo, devuelto) VALUES (?, ?, ?, ?)",
                (libro_id, usuario_id, fecha, devuelto)
            )
            message = "Préstamo creado correctamente" if success else "Error al crear"
        
        if success:
            self.clear_form()
            self.load_data()
            self.load_libros()  # Recargar libros disponibles
            self.show_message(message, ft.colors.GREEN)
        else:
            self.show_message(message, ft.colors.RED)
    
    def edit_prestamo(self, prestamo_id):
        """Carga los datos para editar"""
        prestamo = self.db.execute_query(
            "SELECT * FROM prestamos WHERE id_prestamo = ?",
            (prestamo_id,)
        )
        
        if prestamo:
            self.selected_id = prestamo_id
            prest_data = prestamo[0]
            
            # Recargar libros incluyendo el del préstamo actual
            libros = self.db.execute_query("SELECT * FROM libros ORDER BY titulo")
            self.libro_dropdown.options = [
                ft.dropdown.Option(str(libro['id_libro']), libro['titulo'])
                for libro in libros
            ]
            
            self.libro_dropdown.value = str(prest_data['id_libro'])
            self.usuario_dropdown.value = str(prest_data['id_usuario'])
            self.fecha_field.value = prest_data['fecha_prestamo']
            self.devuelto_checkbox.value = bool(prest_data['devuelto'])
            self.save_btn.text = "Actualizar"
            self.page.update()
    
    def delete_prestamo(self, prestamo_id):
        """Elimina un préstamo"""
        success = self.db.execute_update(
            "DELETE FROM prestamos WHERE id_prestamo = ?",
            (prestamo_id,)
        )
        
        if success:
            self.load_data()
            self.load_libros()  # Recargar libros disponibles
            self.show_message("Préstamo eliminado correctamente", ft.colors.GREEN)
        else:
            self.show_message("Error al eliminar", ft.colors.RED)
    
    def cancel_edit(self, e):
        """Cancela la edición"""
        self.clear_form()
    
    def clear_form(self):
        """Limpia el formulario"""
        self.selected_id = None
        self.libro_dropdown.value = None
        self.usuario_dropdown.value = None
        self.fecha_field.value = datetime.now().strftime("%Y-%m-%d")
        self.devuelto_checkbox.value = False
        self.save_btn.text = "Guardar"
        self.load_libros()  # Recargar solo libros disponibles
        self.page.update()
    
    def show_message(self, message: str, color):
        """Muestra un mensaje de estado"""
        self.status_text.value = message
        self.status_text.color = color
        self.page.update()

class BibliotecaApp:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.categorias_manager = CategoriasManager(self.db_manager)
        self.usuarios_manager = UsuariosManager(self.db_manager)
        self.libros_manager = LibrosManager(self.db_manager)
        self.prestamos_manager = PrestamosManager(self.db_manager)
    
    def main(self, page: ft.Page):
        page.title = "Sistema de Biblioteca"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 1200
        page.window_height = 800
        
        # Crear las pestañas
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Categorías",
                    icon=ft.icons.CATEGORY,
                    content=self.categorias_manager.create_view(page)
                ),
                ft.Tab(
                    text="Usuarios",
                    icon=ft.icons.PEOPLE,
                    content=self.usuarios_manager.create_view(page)
                ),
                ft.Tab(
                    text="Libros",
                    icon=ft.icons.BOOK,
                    content=self.libros_manager.create_view(page)
                ),
                ft.Tab(
                    text="Préstamos",
                    icon=ft.icons.ASSIGNMENT,
                    content=self.prestamos_manager.create_view(page)
                ),
            ],
            expand=1,
        )
        
        # Layout principal
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text(
                            "Sistema de Gestión de Biblioteca",
                            size=30,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.WHITE
                        ),
                        bgcolor=ft.colors.BLUE,
                        padding=20,
                        alignment=ft.alignment.center
                    ),
                    tabs
                ]),
                expand=True
            )
        )

def main(page: ft.Page):
    app = BibliotecaApp()
    app.main(page)

if __name__ == "__main__":
    ft.app(target=main)