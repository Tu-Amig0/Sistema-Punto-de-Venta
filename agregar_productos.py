from tkinter import *
import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry
from permissions_framework import PermissionLevel




class Agregar_Productos(tk.Frame):
    def __init__(self, padre, usuario_actual=None, rol_actual=None, permission_manager=None):
        super().__init__(padre)
        # Cuando creas la instancia de Inventario:
        # DEBUG: Verificar qué valores están llegando
        print(f"DEBUG Agregar_Productos - usuario_actual: {usuario_actual}")
        print(f"DEBUG Agregar_Productos - rol_actual: {rol_actual}") 
        print(f"DEBUG Agregar_Productos - permission_manager: {permission_manager}")
        
        self.usuario_actual = usuario_actual
        self.rol_actual = rol_actual
        self.permission_manager = permission_manager

        try:
            self.sqliteConnection = sqlite3.connect('PuntoVenta.db')
            self.cursor = self.sqliteConnection.cursor()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo conectar a la base de datos:\n{str(e)}")
            return
        
        self.widgets()

    def tiene_permiso_escritura(self):
        """Verifica si el usuario tiene permisos de escritura en productos"""
        if self.permission_manager and self.usuario_actual:
            return self.permission_manager.has_permission(
                self.usuario_actual, 'productos', PermissionLevel.WRITE
            )
        return False

    def widgets(self):
        # Mostrar información del usuario actual
        label_usuario = tk.Label(
            self, 
            text=f"Usuario: {self.usuario_actual} | Rol: {self.rol_actual}",
            font=("Arial", 10),
            bg="#C6D9E3"
        )
        label_usuario.place(x=10, y=10)

        # Si no tiene permisos de escritura, mostrar interfaz de solo lectura
        if not self.tiene_permiso_escritura():
            messagebox.showwarning(
                "Permisos limitados", 
                "Solo los administradores pueden modificar productos"
            )
            self.crear_interfaz_solo_lectura()
        else:
            # Crear la interfaz completa con campos editables
            self.crear_interfaz_completa()

    def crear_interfaz_solo_lectura(self):
        """Crea una interfaz solo de visualización para usuarios sin permisos"""
        label_info = tk.Label(
            self,
            text="⛔ Solo usuarios administradores pueden modificar productos",
            font=("Arial", 12),
            bg="#ffebee",
            fg="#d32f2f"
        )
        label_info.pack(pady=50)
    
        label_consulta = tk.Label(
            self,
            text="Contacta al administrador para solicitar permisos",
            font=("Arial", 10),
            bg="#f5f5f5"
        )
        label_consulta.pack()


    def formatear_precio(self, *args):
        """Formatea el precio con separadores de miles y símbolo de dólar"""
        # Obtener el texto actual sin formato
        texto = self.precio_var.get().replace('$', '').replace(',', '')
        
        # Si está vacío, mostrar nada
        if not texto:
            self.precio_var.set('')
            return
            
        try:
            # Convertir a número y formatear
            numero = float(texto)
            texto_formateado = f"${numero:,.2f}"
            
            # Evitar ciclo infinito al actualizar la variable
            if self.precio_var.get() != texto_formateado:
                self.precio_var.set(texto_formateado)
                
                # Mover el cursor al final
                self.entry_PrecioProducto.icursor(END)
        except ValueError:
            # Si no es un número válido, mantener el texto sin formato
            pass

    def on_focus_in_stock(self, event):
        """Cuando el campo stock recibe foco, eliminar el 0 si está presente"""
        if self.stock_var.get() == "0":
            self.stock_var.set("")
            
    def on_focus_out_stock(self, event):
        """Cuando el campo stock pierde foco, poner 0 si está vacío"""
        if not self.stock_var.get():
            self.stock_var.set("0")

    def crear_interfaz_completa(self):
        """Crea la interfaz completa con todos los campos editables"""
        # Estilo general
        bg_color = "#f5f5f5"
        entry_bg = "#ffffff"
        button_bg = "#4e73df"
        button_fg = "#ffffff"
        font_style = "Helvetica"
    
        self.configure(bg=bg_color)
    
        # Frame principal con sombra visual
        frame_principal = Frame(self, bg=bg_color, bd=2, relief=tk.GROOVE)
        frame_principal.pack(pady=20, padx=20, fill='x')
    
        # Título del formulario
        lbl_titulo = Label(frame_principal, text="REGISTRO DE PRODUCTOS", 
                          font=(font_style, 14, 'bold'), bg=bg_color, fg="#2e59d9")
        lbl_titulo.grid(row=0, column=0, columnspan=2, pady=(10, 20), sticky='w')
        
        # Estilo para los labels
        label_style = {'font': (font_style, 10, 'bold'), 'bg': bg_color, 'anchor': 'w'}
        
        # Estilo para los entries
        entry_style = {
            'font': (font_style, 11), 
            'bg': entry_bg, 
            'relief': tk.FLAT,
            'highlightbackground': '#d1d3e2',
            'highlightcolor': '#4e73df',
            'highlightthickness': 1,
            'bd': 0
        }
        
        # Código de barras
        lbl_CodigodeBarras = Label(frame_principal, text="Código de Barras:", **label_style)
        lbl_CodigodeBarras.grid(row=1, column=0, sticky='w', pady=5)
        self.entry_CodigodeBarras = Entry(frame_principal, **entry_style)
        self.entry_CodigodeBarras.grid(row=1, column=1, sticky='ew', pady=5, padx=5, ipady=4)
        
        # Nombre del cliente (no obligatorio)
        lbl_Cliente = Label(frame_principal, text="Nombre del Cliente (opcional):", **label_style)
        lbl_Cliente.grid(row=2, column=0, sticky='w', pady=5)
        self.entry_Cliente = Entry(frame_principal, **entry_style)
        self.entry_Cliente.grid(row=2, column=1, sticky='ew', pady=5, padx=5, ipady=4)
        
        # Stock
        lbl_Stock = Label(frame_principal, text="Stock Inicial:", **label_style)
        lbl_Stock.grid(row=8, column=0, sticky='w', pady=5)
        self.stock_var = StringVar(value="0")
        self.entry_Stock = Entry(frame_principal, textvariable=self.stock_var, **entry_style)
        self.entry_Stock.grid(row=8, column=1, sticky='ew', pady=5, padx=5, ipady=4)

        # Conectar eventos de foco al campo stock
        self.entry_Stock.bind("<FocusIn>", self.on_focus_in_stock)
        self.entry_Stock.bind("<FocusOut>", self.on_focus_out_stock)
        
        # Departamento (Combobox)
        lbl_Departamento = Label(frame_principal, text="Departamento:", **label_style)
        lbl_Departamento.grid(row=3, column=0, sticky='w', pady=5)
        self.departamentos = ['Zapatos', 'Cosmeticos', 'Ropa', 'Hogar',  'Oficina']
        self.combo_Departamento = ttk.Combobox(
            frame_principal, 
            values=self.departamentos, 
            font=(font_style, 11), 
            state="readonly",
            style='TCombobox'
        )
        self.combo_Departamento.grid(row=3, column=1, sticky='ew', pady=5, padx=5)
        self.combo_Departamento.set('Seleccione departamento')
        
        # Marca (Combobox)
        lbl_Marca = Label(frame_principal, text="Marca:", **label_style)
        lbl_Marca.grid(row=4, column=0, sticky='w', pady=5)
        self.marcas = ['Andrea', 'Impuls', 'Cklass', 'Betterware', 'Omnilife', 'Seytú', 'Blen', 'Ilusión', 'Tupperware', 'Terramar','Vianney', 'Stanhome', 'Cyzone','L´bel', 'Esika']
        self.combo_Marca = ttk.Combobox(
            frame_principal, 
            values=self.marcas, 
            font=(font_style, 11), 
            state="readonly",
            style='TCombobox'
        )
        self.combo_Marca.grid(row=4, column=1, sticky='ew', pady=5, padx=5)
        self.combo_Marca.set('Seleccione marca')
        
        # Color
        lbl_Color = Label(frame_principal, text="Color:", **label_style)
        lbl_Color.grid(row=5, column=0, sticky='w', pady=5)
        self.entry_Color = Text(
            frame_principal, 
            font=(font_style, 11), 
            bg=entry_bg, 
            height=4,
            relief=tk.FLAT,
            highlightbackground='#d1d3e2',
            highlightcolor='#4e73df',
            highlightthickness=1,
            bd=0
        )
        self.entry_Color.grid(row=5, column=1, sticky='ew', pady=5, padx=5)
        
        # Talla
        lbl_Talla = Label(frame_principal, text="Talla:", **label_style)
        lbl_Talla.grid(row=6, column=0, sticky='w', pady=5)
        self.entry_Talla = Entry(frame_principal, **entry_style)
        self.entry_Talla.grid(row=6, column=1, sticky='ew', pady=5, padx=5, ipady=4)
        
        # Precio
        lbl_PrecioProducto = Label(frame_principal, text="Precio ($):", **label_style)
        lbl_PrecioProducto.grid(row=7, column=0, sticky='w', pady=5)
        self.precio_var = StringVar()
        self.entry_PrecioProducto = Entry(frame_principal, textvariable=self.precio_var, **entry_style)
        self.entry_PrecioProducto.grid(row=7, column=1, sticky='ew', pady=5, padx=5, ipady=4)

        # Conectar la variable para formatear automáticamente
        self.precio_var.trace('w', self.formatear_precio)

        # Frame para fechas
        frame_fechas = Frame(frame_principal, bg=bg_color)
        frame_fechas.grid(row=9, column=0, columnspan=2, sticky='ew', pady=5)
        
        # Fecha de Ingreso
        lbl_FechaIngreso = Label(frame_fechas, text="Fecha de Ingreso:", **label_style)
        lbl_FechaIngreso.grid(row=0, column=0, sticky='w', padx=(0, 10))

        # Calendario para fecha de ingreso
        self.cal_ingreso = DateEntry(
            frame_fechas,
            selectmode='day',
            date_pattern='yyyy-mm-dd',
            font=(font_style, 11),
            background='#4e73df',
            foreground='white',
            borderwidth=1,
            locale='es_ES',
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day,
            mindate=datetime(2000, 1, 1),
            showothermonthdays=False
        )
        self.cal_ingreso.delete(0, 'end')
        self.cal_ingreso.grid(row=0, column=1, sticky='ew', padx=(0, 20))
        
        # Fecha de Vencimiento
        lbl_FechaVencimiento = Label(frame_fechas, text="Fecha de Vencimiento:", **label_style)
        lbl_FechaVencimiento.grid(row=0, column=2, sticky='w', padx=(0, 10))
        
        # Calendario para fecha de vencimiento
        self.cal_vencimiento = DateEntry(
            frame_fechas,
            selectmode='day',
            date_pattern='yyyy-mm-dd',
            font=(font_style, 11),
            background='#4e73df',
            foreground='white',
            borderwidth=1,
            locale='es_ES',
            showothermonthdays=False
        )
        self.cal_vencimiento.delete(0, 'end')
        self.cal_vencimiento.grid(row=0, column=3, sticky='ew')
        
        # Configurar el grid para que las columnas de fechas se expandan
        frame_fechas.columnconfigure(1, weight=1)
        frame_fechas.columnconfigure(3, weight=1)
        
        # Botones
        frame_botones = Frame(self, bg=bg_color)
        frame_botones.pack(pady=(10, 20))
        
        button_style = {
            'font': (font_style, 11, 'bold'),
            'fg': 'white',
            'bd': 0,
            'padx': 15,
            'pady': 8,
            'activebackground': '#2e59d9',
            'activeforeground': 'white'
        }
        
        btn_guardar = Button(frame_botones, text="Guardar Producto", 
                           command=self.guardar_producto, 
                           bg='#4CAF50', **button_style)
        btn_guardar.grid(row=0, column=0, padx=5)
        
        btn_actualizar = Button(frame_botones, text="Actualizar Producto", 
                              command=self.abrir_ventana_actualizar, 
                              bg='#FF9800', **button_style)
        btn_actualizar.grid(row=0, column=1, padx=5)
        
        btn_eliminar = Button(frame_botones, text="Eliminar Producto", 
                            command=self.abrir_ventana_eliminar, 
                            bg='#f44336', **button_style)
        btn_eliminar.grid(row=0, column=2, padx=5)
        
        btn_limpiar = Button(frame_botones, text="Limpiar Campos", 
                           command=self.limpiar_campos, 
                           bg='#6c757d', **button_style)
        btn_limpiar.grid(row=0, column=3, padx=5)
        
        # Configurar el grid
        frame_principal.columnconfigure(1, weight=1)
        
    def guardar_producto(self):
        CodigodeBarras = self.entry_CodigodeBarras.get()
        Cliente = self.entry_Cliente.get()
        Departamento = self.combo_Departamento.get()
        Marca = self.combo_Marca.get()
        Color = self.entry_Color.get("1.0", END).strip()
        Talla = self.entry_Talla.get()
        PrecioProducto = self.entry_PrecioProducto.get()
        Stock = self.entry_Stock.get()
        Fechaingreso = self.cal_ingreso.get()
        Fechavencimiento = self.cal_vencimiento.get()

        # Obtener y limpiar el precio para guardar en la base de datos
        precio_texto = self.precio_var.get().replace('$', '').replace(',', '')
        try:
            PrecioProducto = float(precio_texto) if precio_texto else 0.0
        except ValueError:
            PrecioProducto = 0.0

        Stock = self.stock_var.get()
        Fechaingreso = self.cal_ingreso.get()
        Fechavencimiento = self.cal_vencimiento.get()
        
        # Validación de campos obligatorios
        if not CodigodeBarras or Departamento == 'Seleccione departamento' or \
           Marca == 'Seleccione marca' or not PrecioProducto or not Fechaingreso or not Fechavencimiento:
            messagebox.showerror("Error", "Los campos obligatorios son: Código de Barras, Departamento, Marca, Precio y Fechas")
            return
            
            
        try:
            cursor = self.sqliteConnection.cursor()
            cursor.execute('''INSERT INTO registro_productos 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (None, CodigodeBarras, Cliente, Departamento, Marca, Color, Talla, 
                            PrecioProducto, Stock, Fechaingreso, Fechavencimiento))
            self.sqliteConnection.commit()

            messagebox.showinfo("Éxito", "Producto registrado correctamente")
            self.limpiar_campos()
            self.entry_CodigodeBarras.focus_set()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo guardar el producto:\n{str(e)}")

    def abrir_ventana_actualizar(self):
        self.ventana_actualizar = Toplevel()
        self.ventana_actualizar.title("Actualizar Producto")
        self.ventana_actualizar.geometry("500x200")
        self.ventana_actualizar.resizable(False, False)
        
        frame_principal = Frame(self.ventana_actualizar, padx=20, pady=20)
        frame_principal.pack(fill=BOTH, expand=True)
        
        lbl_codigo = Label(frame_principal, text="Escanear código de barras:", font=('sans 12'))
        lbl_codigo.grid(row=0, column=0, sticky='w', pady=10)
        
        self.entry_codigo_actualizar = Entry(frame_principal, font=('sans 12'), width=30)
        self.entry_codigo_actualizar.grid(row=0, column=1, padx=10)
        self.entry_codigo_actualizar.focus_set()
        
        btn_buscar = Button(frame_principal, text="Buscar Producto", font=('sans 10 bold'),
                           command=self.buscar_producto_actualizar, bg='#2196F3', fg='white')
        btn_buscar.grid(row=1, column=0, columnspan=2, pady=20)
        
        frame_principal.columnconfigure(1, weight=1)
        self.entry_codigo_actualizar.bind('<Return>', lambda event: self.buscar_producto_actualizar())
    
    def buscar_producto_actualizar(self):
        codigo = self.entry_codigo_actualizar.get().strip()
    
        if not codigo:
            messagebox.showwarning("Advertencia", "Ingrese un código de barras")
            return
            
        try:
            cursor = self.sqliteConnection.cursor()
            cursor.execute("SELECT * FROM registro_productos WHERE CodigodeBarras=?", (codigo,))
            producto = cursor.fetchone()
            
            if producto:
                print(f"ID del producto encontrado: {producto[0]}")
                self.ventana_actualizar.destroy()
                
                self.limpiar_campos()
                self.entry_CodigodeBarras.insert(0, producto[1])
                self.entry_Cliente.insert(0, producto[2])
                self.combo_Departamento.set(producto[3])
                self.combo_Marca.set(producto[4])
                self.entry_Color.insert("1.0", producto[5])
                self.entry_Talla.insert(0, producto[6])
                self.precio_var.set(str(producto[7]))
                self.stock_var.set(str(producto[8]))
                self.cal_ingreso.set_date(producto[9])
                self.cal_vencimiento.set_date(producto[10])
                
                self.btn_actualizar_temp = Button(self, text="Confirmar Actualización", font=('sans 11 bold'),
                                               command=lambda: self.confirmar_actualizacion(producto[0]), 
                                               bg='#FF9800', fg='white')
                self.btn_actualizar_temp.pack(pady=10)
                
                messagebox.showinfo("Éxito", "Producto encontrado. Modifique los campos necesarios y haga clic en 'Confirmar Actualización'")
            else:
                messagebox.showinfo("Información", "No se encontró un producto con ese código")
                
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo buscar el producto:\n{str(e)}")
    
    def confirmar_actualizacion(self, Id_productos):
        print(f"Intentando actualizar producto con ID: {Id_productos}")
        nuevos_valores = {
            'CodigodeBarras': self.entry_CodigodeBarras.get(),
            'Cliente': self.entry_Cliente.get(),
            'Departamento': self.combo_Departamento.get(),
            'Marca': self.combo_Marca.get(),
            'Color': self.entry_Color.get("1.0", END).strip(),
            'Talla': self.entry_Talla.get(),
            'PrecioProducto': self.entry_PrecioProducto.get(),
            'Stock': self.stock_var.get(),
            'Fechaingreso': self.cal_ingreso.get(),
            'Fechavencimiento': self.cal_vencimiento.get()
        }

        # Obtener y limpiar el precio para guardar en la base de datos
        precio_texto = self.precio_var.get().replace('$', '').replace(',', '')
        try:
            nuevos_valores['PrecioProducto'] = float(precio_texto) if precio_texto else 0.0
        except ValueError:
            nuevos_valores['PrecioProducto'] = 0.0
        
        
        if not nuevos_valores['CodigodeBarras'] or not nuevos_valores['Cliente'] or \
           nuevos_valores['Departamento'] == 'Seleccione departamento' or \
           nuevos_valores['Marca'] == 'Seleccione marca' or not nuevos_valores['PrecioProducto'] or not nuevos_valores['Fechaingreso'] or not nuevos_valores['Fechavencimiento']:
            messagebox.showerror("Error", "Todos los campos son obligatorios excepto color y talla")
            return
            
        try:
            nuevos_valores['PrecioProducto'] = float(nuevos_valores['PrecioProducto'])
            if nuevos_valores['PrecioProducto'] <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número válido mayor que cero")
            return
            
        try:
            cursor = self.sqliteConnection.cursor()
            cursor.execute('''UPDATE registro_productos SET
                           CodigodeBarras=?, Cliente=?, Departamento=?, Marca=?, 
                           Color=?, Talla=?, PrecioProducto=?, Stock=?, Fechaingreso=?, Fechavencimiento=?
                           WHERE Id_productos=?''',
                           (nuevos_valores['CodigodeBarras'], nuevos_valores['Cliente'],
                            nuevos_valores['Departamento'], nuevos_valores['Marca'],
                            nuevos_valores['Color'], nuevos_valores['Talla'],
                            nuevos_valores['PrecioProducto'], nuevos_valores['Stock'],
                            nuevos_valores['Fechaingreso'], nuevos_valores['Fechavencimiento'], int(Id_productos)))
            
            if cursor.rowcount == 0:
                messagebox.showerror("Error", "No se encontró el producto para actualizar")
            else:
                self.sqliteConnection.commit()
            
            self.btn_actualizar_temp.destroy()
            messagebox.showinfo("Éxito", "Producto actualizado correctamente")
            self.limpiar_campos()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo actualizar el producto:\n{str(e)}")
    
    def abrir_ventana_eliminar(self):
        self.ventana_eliminar = Toplevel()
        self.ventana_eliminar.title("Eliminar Producto")
        self.ventana_eliminar.geometry("500x200")
        self.ventana_eliminar.resizable(False, False)
        
        frame_principal = Frame(self.ventana_eliminar, padx=20, pady=20)
        frame_principal.pack(fill=BOTH, expand=True)
        
        lbl_codigo = Label(frame_principal, text="Escanear código de barras:", font=('sans 12'))
        lbl_codigo.grid(row=0, column=0, sticky='w', pady=10)
        
        self.entry_codigo_eliminar = Entry(frame_principal, font=('sans 12'), width=30)
        self.entry_codigo_eliminar.grid(row=0, column=1, padx=10)
        self.entry_codigo_eliminar.focus_set()
        
        btn_buscar = Button(frame_principal, text="Buscar Producto", font=('sans 10 bold'),
                           command=self.buscar_producto_eliminar, bg='#f44336', fg='white')
        btn_buscar.grid(row=1, column=0, columnspan=2, pady=20)
        
        frame_principal.columnconfigure(1, weight=1)
        self.entry_codigo_eliminar.bind('<Return>', lambda event: self.buscar_producto_eliminar())
    
    def buscar_producto_eliminar(self):
        codigo = self.entry_codigo_eliminar.get().strip()
    
        if not codigo:
            messagebox.showwarning("Advertencia", "Ingrese un código de barras")
            return
            
        try:
            cursor = self.sqliteConnection.cursor()
            cursor.execute("SELECT * FROM registro_productos WHERE CodigodeBarras=?", (codigo,))
            producto = cursor.fetchone()
            
            if producto:
                respuesta = messagebox.askyesno(
                    "Confirmar Eliminación", 
                    f"¿Está seguro que desea eliminar el producto:\n\n"
                    f"Código: {producto[1]}\n"
                    f"Color: {producto[5]}\n"
                    f"Talla: {producto[6]}\n"
                    f"Precio: ${producto[7]}\n\n"
                    f"Esta acción no se puede deshacer."
                )
                
                if respuesta:
                    cursor.execute("DELETE FROM registro_productos WHERE CodigodeBarras=?", (codigo,))
                    self.sqliteConnection.commit()
                    
                    if cursor.rowcount > 0:
                        messagebox.showinfo("Éxito", "Producto eliminado correctamente")
                        self.ventana_eliminar.destroy()
                    else:
                        messagebox.showerror("Error", "No se pudo eliminar el producto")
            else:
                messagebox.showinfo("Información", "No se encontró un producto con ese código")
                
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo eliminar el producto:\n{str(e)}")
        finally:
            self.ventana_eliminar.destroy()
            
    def limpiar_campos(self):
        self.entry_CodigodeBarras.delete(0, END)
        self.entry_Cliente.delete(0, END)
        self.combo_Departamento.set('Seleccione departamento')
        self.combo_Marca.set('Seleccione marca')
        self.entry_Color.delete("1.0", END)
        self.entry_Talla.delete(0, END)
        self.entry_PrecioProducto.delete(0, END)
        self.entry_Stock.delete(0, END)
        self.cal_ingreso.delete(0, 'end')
        self.cal_vencimiento.delete(0, 'end')
        self.entry_CodigodeBarras.focus_set()         