
from tkinter import *

from tkinter import ttk


from login import Login
from login import Registro
from container import Container
from permissions_framework import RoleManager, PermissionManager


import sys
import os


class Construction_Information(Tk):  # Se define una clase que usará las funciones de Tk de tkinter
    def __init__(self, *args, **kwargs):  # Constructor de la clase
        super().__init__(*args, **kwargs) 
        self.title("Punto de Venta v1.13")
        self.geometry("1100x650+110+20")  # Tamaño de la ventana del programa
        self.resizable(False, False)  # La ventana no será redimensionable
        
        self.usuario_actual = None  
        self.rol_actual = None
        # Inicializar sistema de permisos
        self.role_manager = RoleManager()
        self.permission_manager = PermissionManager(self.role_manager)


        # Contenedor principal
        container = Frame(self)
        container.pack(side=TOP, fill=BOTH, expand=True)
        container.configure(bg="#C6D9E3")

        # Diccionario para almacenar los frames
        self.frames = {}
        for i in (Login, Registro):  # Recorre las clases de los frames
            frame = i(container, self)  # Crea una instancia del frame
            self.frames[i] = frame

        # Muestra inicialmente la primera pagina que quieres que aparesca en la aplicacion
        self.show_frame(Login)

        # Configuración del estilo ttk
        self.style = ttk.Style()
        self.style.theme_use("clam")

    def show_frame(self, container):
        # Si es Container y aún no se ha creado, crearlo ahora
        if container == Container and (container not in self.frames or self.frames[container] is None):
            print("DEBUG: Creando Container dinámicamente")
            self.frames[Container] = Container(self, self)  # ← Crear con self como controlador
    
        frame = self.frames[container]
    
        if frame is not None:
            frame.tkraise()
        else:
            print(f"ERROR: El frame {container} es None")


def main():  # Función principal que inicia la aplicación
    app = Construction_Information()
    app.mainloop()


# Punto de entrada de la aplicación
if __name__ == "__main__":
    main()
