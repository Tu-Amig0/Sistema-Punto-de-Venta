# permissions_framework.py
import json
import sqlite3
from functools import wraps
from enum import Enum

class PermissionLevel(Enum):
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3

class RoleManager:
    def __init__(self, db_name="PuntoVenta.db"):  # Usar tu misma base de datos
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos de permisos usando tu estructura existente"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Verificar si la tabla de roles ya existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roles'")
            roles_table_exists = cursor.fetchone()
            
            # Verificar si la tabla de user_roles ya existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_roles'")
            user_roles_table_exists = cursor.fetchone()
            
            # Crear tabla de roles si no existe
            if not roles_table_exists:
                cursor.execute('''
                    CREATE TABLE roles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        permissions TEXT NOT NULL DEFAULT '{}'
                    )
                ''')
            
            # Crear tabla de user_roles si no existe
            if not user_roles_table_exists:
                cursor.execute('''
                    CREATE TABLE user_roles (
                        user_id TEXT NOT NULL,
                        role_id INTEGER NOT NULL,
                        FOREIGN KEY (role_id) REFERENCES roles (id),
                        PRIMARY KEY (user_id, role_id)
                    )
                ''')
            
            # Insertar roles por defecto
            default_roles = {
                'Administrador': {
                    'productos': PermissionLevel.ADMIN.value,
                    'ventas': PermissionLevel.ADMIN.value,
                    'inventario': PermissionLevel.ADMIN.value,
                    'clientes': PermissionLevel.ADMIN.value
                },
                'Usuario': {
                    'productos': PermissionLevel.NONE.value,
                    'ventas': PermissionLevel.WRITE.value,
                    'inventario': PermissionLevel.READ.value,
                    'clientes': PermissionLevel.READ.value
                }
            }
            
            for role_name, permissions in default_roles.items():
                # Verificar si el rol ya existe
                cursor.execute('SELECT id FROM roles WHERE name = ?', (role_name,))
                existing_role = cursor.fetchone()
                
                if not existing_role:
                    cursor.execute(
                        'INSERT INTO roles (name, permissions) VALUES (?, ?)',
                        (role_name, json.dumps(permissions))
                    )
            
            # Sincronizar usuarios existentes con el sistema de roles
            self.sincronizar_usuarios_existentes()
            
            conn.commit()
    
    def sincronizar_usuarios_existentes(self):
        """Sincroniza los usuarios de tu tabla 'usuarios' con el sistema de roles"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Obtener todos los usuarios de tu tabla
            cursor.execute("SELECT username, rol FROM usuarios")
            usuarios = cursor.fetchall()
            
            for username, rol in usuarios:
                if rol:  # Si el usuario tiene un rol asignado
                    # Verificar si el rol existe en la tabla roles
                    cursor.execute('SELECT id FROM roles WHERE name = ?', (rol,))
                    role_id = cursor.fetchone()
                    
                    if role_id:
                        # Asignar el rol al usuario en user_roles
                        cursor.execute(
                            'INSERT OR REPLACE INTO user_roles (user_id, role_id) VALUES (?, ?)',
                            (username, role_id[0])
                        )
            
            conn.commit()

class PermissionManager:
    def __init__(self, role_manager):
        self.role_manager = role_manager
    
    def get_user_permissions(self, user_id):
        """Obtiene todos los permisos de un usuario desde tu base de datos"""
        with sqlite3.connect(self.role_manager.db_name) as conn:
            cursor = conn.cursor()
            
            # Primero intentar obtener permisos del sistema de roles
            cursor.execute('''
                SELECT r.permissions 
                FROM roles r 
                JOIN user_roles ur ON r.id = ur.role_id 
                WHERE ur.user_id = ?
            ''', (user_id,))
            
            results = cursor.fetchall()
            all_permissions = {}
            
            for result in results:
                role_permissions = json.loads(result[0])
                for resource, level in role_permissions.items():
                    current_level = all_permissions.get(resource, PermissionLevel.NONE.value)
                    all_permissions[resource] = max(current_level, level)
            
            # Si no tiene permisos en el sistema de roles, verificar el rol directo en usuarios
            if not all_permissions:
                cursor.execute("SELECT rol FROM usuarios WHERE username = ?", (user_id,))
                user_role = cursor.fetchone()
                
                if user_role and user_role[0]:
                    # Asignar permisos basados en el rol de la tabla usuarios
                    role_permissions = self.get_default_permissions_for_role(user_role[0])
                    for resource, level in role_permissions.items():
                        all_permissions[resource] = level
            
            return all_permissions
    
    def get_default_permissions_for_role(self, role_name):
        """Devuelve permisos por defecto basados en el nombre del rol"""
        default_permissions = {
            'Administrador': {
                'productos': PermissionLevel.ADMIN.value,
                'ventas': PermissionLevel.ADMIN.value,
                'inventario': PermissionLevel.ADMIN.value,
                'clientes': PermissionLevel.ADMIN.value
            },
            'Usuario': {
                'productos': PermissionLevel.NONE.value,
                'ventas': PermissionLevel.WRITE.value,
                'inventario': PermissionLevel.READ.value,
                'clientes': PermissionLevel.READ.value
            }
        }
        
        return default_permissions.get(role_name, {})
    
    def has_permission(self, user_id, resource, required_level):
        """Verifica si un usuario tiene un permiso específico"""
        permissions = self.get_user_permissions(user_id)
        user_level = permissions.get(resource, PermissionLevel.NONE.value)
        return user_level >= required_level.value
    
    def assign_role(self, user_id, role_name):
        """Asigna un rol a un usuario y actualiza ambas tablas"""
        with sqlite3.connect(self.role_manager.db_name) as conn:
            cursor = conn.cursor()
            
            # 1. Actualizar la tabla usuarios
            cursor.execute(
                "UPDATE usuarios SET rol = ? WHERE username = ?",
                (role_name, user_id)
            )
            
            # 2. Actualizar la tabla user_roles
            cursor.execute('SELECT id FROM roles WHERE name = ?', (role_name,))
            role = cursor.fetchone()
            
            if role:
                cursor.execute(
                    'INSERT OR REPLACE INTO user_roles (user_id, role_id) VALUES (?, ?)',
                    (user_id, role[0])
                )
            
            conn.commit()
            return True
    
    def get_user_role(self, user_id):
        """Obtiene el rol de un usuario desde tu tabla usuarios"""
        with sqlite3.connect(self.role_manager.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rol FROM usuarios WHERE username = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None

def requires_permission(resource, required_level):
    """Decorador para verificar permisos en funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'usuario_actual') and hasattr(self, 'permission_manager'):
                if self.permission_manager.has_permission(
                    self.usuario_actual, resource, required_level
                ):
                    return func(self, *args, **kwargs)
                else:
                    from tkinter import messagebox
                    messagebox.showerror(
                        "Permiso denegado", 
                        f"No tienes permisos para acceder a {resource}"
                    )
                    return None
            else:
                from tkinter import messagebox
                messagebox.showerror("Error", "Sistema de permisos no configurado")
                return None
        return wrapper
    return decorator