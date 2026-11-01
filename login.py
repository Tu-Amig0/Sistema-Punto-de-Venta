from tkinter import*
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from container import Container
from PIL import Image, ImageTk


class Login(tk.Frame):
    db_name = "PuntoVenta.db"
    def __init__(self, padre, controlador):
        super().__init__(padre)
        self.pack()
        self.place(x=0, y=0, width=1100, height=650)
        self.controlador = controlador
        self.widgets()
    
    def Validacion_Datos(self, user, password):
        return len(user) > 0 and len(password) > 0
    
    def login(self):
        user = self.username.get()
        password = self.password.get()

        if self.Validacion_Datos(user, password):
            consulta = "SELECT username, rol FROM usuarios WHERE username = ? AND password = ?"
            parametros = (user, password)

            try:
                with sqlite3.connect(self.db_name) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(consulta, parametros)
                    result = cursor.fetchone()

                    if result:
                        # ✅ CORREGIDO: Flujo correcto
                        # 1. Primero asignar valores al controlador
                        self.controlador.usuario_actual = result["username"]
                        self.controlador.rol_actual = result["rol"]

                         # 2. Luego asignar el rol en el sistema de permisos
                        if hasattr(self.controlador, 'permission_manager'):
                            success = self.controlador.permission_manager.assign_role(
                                result["username"], 
                                result["rol"]
                            )
                            print(f"DEBUG: Rol asignado - {success}")  # Para verificar
                            print(f"DEBUG Login - assign_role exitoso: {success}")
                        
                        # 3. FINALMENTE cambiar de frame (solo una vez)
                        self.control1()

                    else:
                        self.username.delete(0, "end")
                        self.password.delete(0, "end")
                        messagebox.showerror(title= "Error", message = " Usuario y/o Contraseña Incorrecta")
            except sqlite3.Error as e:
                messagebox.showerror(title= "Error", message = " No se conecto a la base de Datos: {}".format(e))
        else:
            messagebox.showerror(title = "Error", message = "Porfavor llene Todas Las Casillas")
    

    def control1(self):
        self.controlador.show_frame(Container)

    def control2(self):
        self.controlador.show_frame(Registro)

    def widgets(self):
        fondo = tk.Frame(self, bg="#f0f0f0")
        fondo.pack()
        fondo.place(x=0, y=0, width=1100, height=650)

        # Cargar la imagen de fondo
        self.bg_image = Image.open("Imagenes/imagen2.png")  # Cambia esto por la ruta de tu imagen
        self.bg_image = self.bg_image.resize((1100, 650))
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        
        # Crear un label para la imagen de fondo
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        bg_label.image = self.bg_photo  # Mantener una referencia

        # Frame con color azul claro semitransparente (simulado)
        frame1 = tk.Frame(self, bg="#f5f5f5", bd=2, relief="groove")  # Color sólido
        frame1.place(relx=0.5, rely=0.5, anchor="center", width=350, height=400)

        frame1.config(bg='#f5f5f5')  # El más cercano a transparente

        # El resto del código permanece igual...
        titulo = ttk.Label(frame1, text="Multimarcas Turquesa", font=("Arial", 18, "bold"), background=frame1['bg'])
        titulo.place(relx=0.5, y=40, anchor="center")

        email_label = ttk.Label(frame1, text="Ingresa tu Usuario", font=("Arial", 11), background=frame1['bg'])
        email_label.place(relx=0.5, y=90, anchor="center")
        self.username = ttk.Entry(frame1, font=("Arial", 11))
        self.username.place(relx=0.5, y=120, anchor="center", width=250, height=30)

        password_label = ttk.Label(frame1, text="Ingresa tu contraseña", font=("Arial", 11), background=frame1['bg'])
        password_label.place(relx=0.5, y=170, anchor="center")
        self.password = ttk.Entry(frame1, font=("Arial", 12), show="*")
        self.password.place(relx=0.5, y=200, anchor="center", width=250, height=30)

        # Reemplazar el checkbox "Remember me" por "Mostrar contraseña"
        self.show_password = tk.IntVar()  # Variable para controlar el estado
    
        def toggle_password():
            if self.show_password.get() == 1:
                self.password.config(show='')  # Mostrar contraseña
            else:
                self.password.config(show='*')  # Ocultar contraseña
    
        password_check = ttk.Checkbutton(
        frame1, 
        text="Mostrar contraseña", 
        variable=self.show_password,
        command=toggle_password,  # Función que se ejecuta al cambiar el estado
        style='TCheckbutton'
        )
        password_check.place(relx=0.3, y=240, anchor="center")


        login_btn = tk.Button(frame1, text="Iniciar Sesion", command=self.login, bg="#4CAF50", fg="white", relief="flat", font=("Arial", 11, "bold"))
        login_btn.place(relx=0.5, y=290, anchor="center", width=250, height=35)

        registro_text = ttk.Label(frame1, text="¿No tienes una cuenta? ", font=("Arial", 10), background=frame1['bg'])
        registro_text.place(relx=0.4, y=340, anchor="center")
        registro_link = ttk.Label(frame1, text="Registrarse", font=("Arial", 10, "underline"), foreground="blue", cursor="hand2", background=frame1['bg'])
        registro_link.place(relx=0.70, y=340, anchor="center")
        registro_link.bind("<Button-1>", lambda e: self.control2())

class Registro(tk.Frame):
    
    db_name = "PuntoVenta.db"
    
    def __init__(self, padre, controlador):
        super().__init__(padre)
        self.pack()
        self.place(x=0, y=0, width=1100, height=650)
        self.controlador = controlador
        self.widgets()

    def Validacion_Datos(self, user, password):
     return len(user) > 0 and len(password) > 0
    

    def eje_consulta(self, consulta, parametros=()):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(consulta, parametros)
                conn.commit
        except sqlite3.Error as e:
            messagebox.showerror(title= "Error", message = " No se conecto a la base de Datos: {}".format(e))




    def registro(self): 
        user = self.username.get()
        password = self.password.get()
        key = self.key.get()
        rol = self.rol.get()   # <--- nuevo
        if self.Validacion_Datos(user,password):
            if len(password) < 6:
               messagebox.showinfo(title="Error", message="Contraseña demasiada corta")
               self.username.delete(0, 'end')
               self.password.delete(0, 'end')
            else:
                if key == "1234":
                    consulta = "INSERT INTO usuarios VALUES (?,?,?,?)"
                    parametros = (None, user, password, rol)
                    self.eje_consulta(consulta,parametros)
                    messagebox.showinfo(title="Registro", message="Usuario Registrado Con Exito :)")

                    self.username.delete(0,'end')
                    self.password.delete(0, 'end')
                    self.key.delete(0, 'end')
                else:
                    messagebox.showinfo(title="Registro", message="Error al ingresar el codigo de registro")
        else:
            messagebox.showerror(title="Error", message="LLene sus datos") 
        

    
    def control2(self):
        self.controlador.show_frame(Container)
    
    def control3(self):
      self.controlador.show_frame(Login)
    

    def widgets(self):
        # Fondo con imagen (igual que en Login)
        self.bg_image = Image.open("Imagenes/imagen2.png")  # Usar la misma imagen que Login
        self.bg_image = self.bg_image.resize((1100, 650))
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        bg_label.image = self.bg_photo

        # Frame principal (estilo igual que Login)
        frame1 = tk.Frame(self, bg="#f5f5f5", bd=2, relief="groove")
        frame1.place(relx=0.5, rely=0.5, anchor="center", width=350, height=500)  # Más alto para los campos extra

        # Título
        titulo = ttk.Label(frame1, text="Registro de Usuario", font=("Arial", 18, "bold"), background=frame1['bg'])
        titulo.place(relx=0.5, y=40, anchor="center")

        # Campo de usuario
        user_label = ttk.Label(frame1, text="Nombre de usuario", font=("Arial", 11), background=frame1['bg'])
        user_label.place(relx=0.5, y=90, anchor="center")
        self.username = ttk.Entry(frame1, font=("Arial", 11))
        self.username.place(relx=0.5, y=120, anchor="center", width=250, height=30)

        # Campo de contraseña
        pass_label = ttk.Label(frame1, text="Contraseña", font=("Arial", 11), background=frame1['bg'])
        pass_label.place(relx=0.5, y=170, anchor="center")
        self.password = ttk.Entry(frame1, font=("Arial", 11), show="*")
        self.password.place(relx=0.5, y=200, anchor="center", width=250, height=30)

        # Checkbox para mostrar contraseña (como en Login)
        self.show_password = tk.IntVar()
        def toggle_password():
            if self.show_password.get() == 1:
                self.password.config(show='')
                self.key.config(show='')
            else:
                self.password.config(show='*')
                self.key.config(show='*')
        
        show_pass = ttk.Checkbutton(
            frame1, 
            text="Mostrar contraseña", 
            variable=self.show_password,
            command=toggle_password,
            style='TCheckbutton'
        )
        show_pass.place(relx=0.5, y=240, anchor="center")

        # Menú desplegable para seleccionar rol
        rol_label = ttk.Label(frame1, text="Seleccionar Rol", font=("Arial", 11), background=frame1['bg'])
        rol_label.place(relx=0.5, y=270, anchor="center")

        self.rol = ttk.Combobox(frame1, state="readonly", values=["Administrador", "Usuario"], font=("Arial", 11))
        self.rol.place(relx=0.5, y=300, anchor="center", width=250, height=29)
        self.rol.current(1)  # Por defecto "Usuario"

        # Campo de código de registro
        key_label = ttk.Label(frame1, text="Código de Registro", font=("Arial", 11), background=frame1['bg'])
        key_label.place(relx=0.5, y=330, anchor="center")
        self.key = ttk.Entry(frame1, font=("Arial", 11), show="*")
        self.key.place(relx=0.5, y=360, anchor="center", width=250, height=29)

        # Botones (manteniendo la misma funcionalidad)
        button3 = tk.Button(
            frame1, 
            text="Registrarse", 
            command=self.registro, 
            bg="#4CAF50", 
            fg="white", 
            relief="flat", 
            font=("Arial", 11, "bold")
        )
        button3.place(relx=0.5, y=410, anchor="center", width=250, height=35)

        button4 = tk.Button(
            frame1, 
            text="Regresar", 
            command=self.control3, 
            bg="#f44336", 
            fg="white", 
            relief="flat", 
            font=("Arial", 11, "bold")
        )
        button4.place(relx=0.5, y=460, anchor="center", width=250, height=35)
    
     