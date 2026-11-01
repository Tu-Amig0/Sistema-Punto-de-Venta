from tkinter import*
import tkinter as tk
from ventas import Ventas
from inventario import Inventario
from clientes import Clientes 
from agregar_productos import Agregar_Productos
from tkinter import ttk, messagebox
from permissions_framework import PermissionLevel
import sys
import os


class Container(tk.Frame):
    def __init__(self, padre, controlador):
        super().__init__(padre)

          # DEBUG: Verificar qué valores llegan del controlador
        print(f"DEBUG Container - controlador.usuario_actual: {controlador.usuario_actual}")
        print(f"DEBUG Container - controlador.rol_actual: {controlador.rol_actual}")
        print(f"DEBUG Container - controlador.permission_manager: {controlador.permission_manager}")
        
        self.usuario_actual = controlador.usuario_actual
        self.rol_actual = controlador.rol_actual
        self.controlador = controlador
        
        # Inicializar el sistema de permisos
        self.permission_manager = controlador.permission_manager

        self.pack()
        self.place(x=0, y=0, width=1100, height=650)
        self.widgets()
        self.frames = {}
        self.buttons = []


        # Crear los frames normales (Ventas, Inventario, Clientes) sin usuario
        for i in (Ventas, Inventario, Clientes):
            if i == Inventario:
                # Pasar usuario_actual solo al frame de Inventario
                frame = i(self, usuario_actual=self.usuario_actual)
            else:
                frame = i(self)
            self.frames[i] = frame
            frame.config(bg="#C6D9E3", highlightbackground="gray", highlightthickness=1)
            frame.place(x=0, y=40, width=1100, height=610)
        

        self.show_frames(Ventas)

         # Actualizar la interfaz según los permisos
        self.actualizar_permisos_interfaz()

    def actualizar_permisos_interfaz(self):
        # Usar el framework de permisos para verificar acceso a productos
        if not self.permission_manager.has_permission(self.usuario_actual, 'productos', PermissionLevel.READ):
            self.button_agregar_productos.config(state="disabled", bg="#cccccc")
        else:
            self.button_agregar_productos.config(state="normal", bg="#4CAF50")
            
        # Mostrar información del usuario actual
        info_label = tk.Label(
        self, 
        text=f"Usuario: {self.usuario_actual} | Rol: {self.rol_actual}",
        font=("Arial", 10),
        bg="#f0f0f0"
        )
        info_label.place(x=730, y=10)

        # Botón de Sesión - agregado
        self.button_sesion = Button(
            self,
            text="Sesión",
            font=("Arial", 10, "bold"),
            bg="#4CAF50",  # Color verde
            fg="white",
            command=self.accion_sesion  # Función a ejecutar al hacer clic
            )
        self.button_sesion.place(x=950, y=8, width=80, height=25)  # Posicionado al lado derecho


    def show_frames(self, container):
        frame = self.frames[container]
        frame.tkraise()

    # Función para manejar la acción del botón Sesión
    def accion_sesion(self):
        # Aquí puedes agregar la funcionalidad que quieras para el botón
        # Por ejemplo: cerrar sesión, mostrar información de sesión, etc.
        print(f"Botón Sesión presionado - Usuario: {self.usuario_actual}, Rol: {self.rol_actual}")
        # Ejemplo: mostrar un mensaje informativo
        messagebox.showinfo(
            "Información de Sesión", 
            f"Usuario: {self.usuario_actual}\nRol: {self.rol_actual}\n\nBotón de sesión configurado"
        )

    # Función para abrir el frame de Agregar Productos
    def agregar_productos(self):
          # Verificar permisos usando el framework
          if not self.permission_manager.has_permission(self.usuario_actual, 'productos', PermissionLevel.READ):
               messagebox.showerror("Permiso denegado", 
                              "Solo los administradores pueden acceder a esta función")
               return
        
          # Crear el frame si no existe
          if Agregar_Productos not in self.frames:
               self.frames[Agregar_Productos] = Agregar_Productos(
                    self, 
                    usuario_actual=self.usuario_actual,
                    rol_actual=self.rol_actual,
                    permission_manager=self.permission_manager  # Pasar el gestor de permisos
               )
          self.frames[Agregar_Productos].config(
               bg="#C6D9E3", 
               highlightbackground="gray", 
               highlightthickness=1
          )  
          self.frames[Agregar_Productos].place(x=0, y=40, width=1100, height=610)
        
          self.show_frames(Agregar_Productos)

    def ventas(self):
        self.show_frames(Ventas)

    def inventario(self):
        self.show_frames(Inventario)

    def clientes(self):
        self.show_frames(Clientes)
    
        
    def widgets(self):
        frame_container = tk.Frame(self)
        frame_container.place(x=0, y=0, width=1100, height=40)

        self.button_ventas = Button(frame_container, text="Ventas", font="sans 11 bold", command=self.ventas)
        self.button_ventas.place(x=5, y=0, width=150, height=40)

        self.button_inventario = Button(frame_container, text="Inventario", font="sans 11 bold", command=self.inventario)
        self.button_inventario.place(x=155, y=0, width=150, height=40)

        self.button_clientes = Button(frame_container, text="Clientes", font="sans 11 bold", command=self.clientes)
        self.button_clientes.place(x=305, y=0, width=150, height=40)

        self.button_agregar_productos = Button(frame_container, text="Productos", font="sans 11 bold", command=self.agregar_productos)
        self.button_agregar_productos.place(x=455, y=0, width=150, height=40) 

        self.buttons = [self.button_ventas, self.button_inventario, self.button_clientes, self.button_agregar_productos]