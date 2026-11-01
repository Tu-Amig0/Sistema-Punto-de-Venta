from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from datetime import datetime, timedelta  # Para manejar fechas y calcular el vencimiento
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from tempfile import gettempdir
from reportlab.lib.pagesizes import mm
from pdf2image import convert_from_path
from PIL import Image, ImageTk
import tempfile
import win32api
import win32print
import fnmatch

# Configuración de SQLAlchemy
Base = declarative_base()

class RegistroProductos(Base):
    __tablename__ = 'registro_productos'
    Id_productos = Column(Integer, primary_key=True)
    CodigodeBarras = Column(String)
    Cliente = Column(String)
    Departamento = Column(String)
    Marca = Column(String)
    Color = Column(String)
    PrecioProducto = Column(Float)
    Stock = Column(Integer)
    Fechaingreso=Column(String)
    Fechavencimiento=Column(String)

class TransferenciasDiferencias(Base):
    __tablename__ = 'transferencias_diferencias'
    Id_transferencias = Column(Integer, primary_key=True)
    Monto = Column(Float)
    CodigodeBarras = Column(String)
    Cliente = Column(String)
    Marca = Column(String)
    PrecioProducto = Column(Float)
    Id_productos = Column(Integer, ForeignKey('registro_productos.Id_productos'))
    producto = relationship("RegistroProductos")

class InventarioModel(Base):
    __tablename__ = 'Inventario'
    Id_inventario = Column(Integer, primary_key=True)
    CodigodeBarras = Column(String)
    Cliente = Column(String)
    Stock = Column(Integer)  # Cantidad vendida (siempre positivo)
    PrecioProducto = Column(Float)
    Id_productos = Column(Integer, ForeignKey('registro_productos.Id_productos'))
    producto = relationship("RegistroProductos")


class ValesDevolucion(Base):
    __tablename__ = 'vales_devolucion'
    Id_vale = Column(Integer, primary_key=True)
    CodigodeBarras = Column(String)
    Cliente = Column(String)
    Marca = Column(String)
    Color = Column(String)
    Talla = Column(String)
    PrecioProducto = Column(Float)
    Fechaingreso = Column(String)
    Fechavencimiento = Column(String)
    Id_productos = Column(Integer, ForeignKey('registro_productos.Id_productos'))
    producto = relationship("RegistroProductos")

class ValesDiferencia(Base):
    __tablename__ = 'vales_diferencia'
    Id_diferencia = Column(Integer, primary_key=True)
    CodigodeBarras = Column(String)
    Cliente = Column(String)
    Departamento = Column(String)
    Marca = Column(String)
    Color = Column(String)
    Talla = Column(String)
    vale_menos_diferencia = Column(Float)
    vale_mas_diferencia = Column(Float)
    Diferencia = Column(Float)
    Id_productos = Column(Integer, ForeignKey('registro_productos.Id_productos'))
    producto = relationship("RegistroProductos")

# Crear motor de base de datos
engine = create_engine('sqlite:///PuntoVenta.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class Ventas(tk.Frame):
    def __init__(self, padre):
        super().__init__(padre)
        self.Temp_dir = r"C:\punto-venta-almacenamiento"  # Ruta específica para archivos temporales
        self.pdf_path= r"C:\Program Files\Adobe\Acrobat DC\Acrobat.exe"
        try:
            self.sqliteConnection = sqlite3.connect('PuntoVenta.db')
            self.cursor = self.sqliteConnection.cursor()
            self.session = Session()  # Sesión de SQLAlchemy
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar a la base de datos:\n{str(e)}")
            return
        
        self.productos_agregados = {}  # Diccionario para llevar registro de productos agregados
        self.productos_transferencia = set()  # Conjunto para productos pagados por transferencia
        self.productos_devolucion = set()  # NUEVO: Conjunto para productos de devolución
        
        self.widgets()

        # Añade esta línea para configurar el estilo de la columna Precio
        self.tree.tag_configure('precio_verde', foreground='green')

    # AQUÍ AGREGA LA NUEVA FUNCIÓN (justo después del __init__)
    def formato_moneda(self, monto):
        """Formatea un número como moneda con separadores de miles y 2 decimales"""
        return "${:,.2f}".format(monto)

    def widgets(self):
        # Frame principal
        frame_principal = Frame(self, bg='orange')
        frame_principal.pack(pady=10, padx=20, fill='x')

        # --- NUEVO APARTADO DE BÚSQUEDA AVANZADA ---
        frame_busqueda_avanzada = Frame(self, bg='#f5f5f5', bd=1, relief=tk.SOLID, padx=5, pady=5)
        frame_busqueda_avanzada.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Título
        Label(frame_busqueda_avanzada, text="Búsqueda Avanzada", bg='#f5f5f5', 
              font=('Helvetica', 9, 'bold')).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 5))
        

         # Estilo para los campos de entrada
        estilo_campos = {
            'font': ('Helvetica', 9),
            'bd': 1,
            'relief': 'solid',
            'highlightbackground': '#e0e0e0',
            'highlightthickness': 1,
            'bg': 'white',
            'width': 13
        }

        # Estilo para las etiquetas
        estilo_etiquetas = {
            'bg': '#f8f9fa',
            'font': ('Helvetica', 9),
            'padx': 5
        }


        # Campos de búsqueda
        Label(frame_busqueda_avanzada, text="Cliente:", **estilo_etiquetas).grid(row=1, column=0, sticky='e', pady=3)
        self.entry_buscar_cliente = Entry(frame_busqueda_avanzada, **estilo_campos)
        self.entry_buscar_cliente.grid(row=1, column=1, sticky='w', pady=3)

        Label(frame_busqueda_avanzada, text="Apellido:", **estilo_etiquetas).grid(row=1, column=2, sticky='e', pady=3)
        self.entry_buscar_apellido = Entry(frame_busqueda_avanzada, **estilo_campos)
        self.entry_buscar_apellido.grid(row=1, column=3, sticky='w', pady=3)

        Label(frame_busqueda_avanzada, text="Marca:", **estilo_etiquetas).grid(row=2, column=0, sticky='e', pady=3)
        self.entry_buscar_marca = Entry(frame_busqueda_avanzada, **estilo_campos)
        self.entry_buscar_marca.grid(row=2, column=1, sticky='w', pady=3)

        Label(frame_busqueda_avanzada, text="Departamento:", **estilo_etiquetas).grid(row=2, column=2, sticky='e', pady=3)
        self.entry_buscar_departamento = Entry(frame_busqueda_avanzada, **estilo_campos)
        self.entry_buscar_departamento.grid(row=2, column=3, sticky='w', pady=3)


        # Botón de búsqueda
        btn_buscar_avanzada = Button(frame_busqueda_avanzada, text="Buscar", 
                                    command=self.buscar_avanzada,
                                    bg='#4CAF50', fg='white', font=('Helvetica', 8, 'bold'))
        btn_buscar_avanzada.grid(row=3, column=0, columnspan=4, pady=(5, 0))

        # --- FIN DEL NUEVO APARTADO ---

        # Código de barras
        lbl_CodigodeBarras = Label(frame_principal, font="sans 10 bold", text="Código de Barras:", bg='white', anchor='w')
        lbl_CodigodeBarras.grid(row=0, column=0, sticky='w', pady=5)
        self.entry_CodigodeBarras = Entry(frame_principal, relief="solid", font=('sans 13'), fg='blue')
        self.entry_CodigodeBarras.grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        self.entry_CodigodeBarras.focus()

        # Botón para buscar producto
        btn_buscar = Button(frame_principal, text="Buscar Producto", font=('Helvetica 10 bold'), 
                           command=self.buscar_producto, bg='#4CAF50', fg='white',
                           activebackground='#45a049', activeforeground='white',
                           bd=0, padx=15, pady=5, cursor="hand2")
        btn_buscar.grid(row=0, column=2, padx=10)

        # Frame para la lista de productos
        frame_lista = Frame(self, bg='white')
        frame_lista.pack(pady=10, padx=10, fill='both', expand=True)

        # Lista de productos con columna adicional para transferencia
        self.tree = ttk.Treeview(frame_lista, columns=("Código", "Cliente", "Departamento", "Marca", "Color", "Talla",
                                        "Precio", "Cantidad", "Stock", "Total", "Transferencia"), show='headings')
        self.tree.pack(pady=10, padx=0, fill='both', expand=True)

        # Vincular evento de doble clic
        self.tree.bind('<Double-1>', self.abrir_ventana_diferencia)

        # Definir encabezados
        self.tree.heading("Código", text="Código")
        self.tree.heading("Cliente", text="Cliente")
        self.tree.heading("Departamento", text="Departamento")
        self.tree.heading("Marca", text="Marca")
        self.tree.heading("Color", text="Color")
        self.tree.heading("Talla", text="Talla")
        self.tree.heading("Precio", text="Importe")
        self.tree.heading("Cantidad", text="Cantidad")
        self.tree.heading("Stock", text="Stock Restante")
        self.tree.heading("Total", text="Precio Venta")
        self.tree.heading("Transferencia", text="Transferencia")

        # Configurar ancho de columnas
        self.tree.column("Código", width=100, anchor='center')
        self.tree.column("Cliente", width=120, anchor='center')
        self.tree.column("Departamento", width=100, anchor='center')
        self.tree.column("Marca", width=100, anchor='center')
        self.tree.column("Color", width=110, anchor='center')
        self.tree.column("Talla", width=80, anchor='center')  # Nueva columna para Talla
        self.tree.column("Precio", width=100, anchor='center')
        self.tree.column("Cantidad", width=80, anchor='center')
        self.tree.column("Stock", width=80, anchor='center')
        self.tree.column("Total", width=100, anchor='center')
        self.tree.column("Transferencia", width=100, anchor='center')

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Frame para botones de transferencia
        frame_transferencia = Frame(frame_lista, bg='white')
        frame_transferencia.pack(fill='x', pady=(0, 10))

        # Botón para marcar transferencia
        btn_marcar_transferencia = Button(frame_transferencia, text="Marcar como Transferencia", 
                                        command=self.marcar_transferencia,
                                        bg='#2196F3', fg='white', font=('Helvetica', 9, 'bold'))
        btn_marcar_transferencia.pack(side='left', padx=5)

        # Botón para marcar TODOS como transferencia
        btn_todos_transferencia = Button(frame_transferencia, text="Marcar TODOS como Transferencia", 
                                       command=self.marcar_todos_transferencia,
                                       bg='#3F51B5', fg='white', font=('Helvetica', 9, 'bold'))
        btn_todos_transferencia.pack(side='left', padx=5)

        # NUEVO BOTÓN: Consultar Vales de Diferencia
        btn_consultar_vales = Button(frame_transferencia, text="Consultar Vales de Diferencia", 
                                    command=self.abrir_ventana_vales_diferencia,
                                    bg='#FF9800', fg='white', font=('Helvetica', 9, 'bold'))
        btn_consultar_vales.pack(side='left', padx=5)

        # NUEVO BOTÓN: Marcar Vale de Devolución
        btn_marcar_devolucion = Button(frame_transferencia, text="Marcar Vale de Devolución", 
                            command=self.marcar_devolucion,
                            bg='#9C27B0', fg='white', font=('Helvetica', 9, 'bold'))
        btn_marcar_devolucion.pack(side='left', padx=5)

        # Frame para totales - Tarjeta moderna
        frame_totales = Frame(self, bg="#cccccc", bd=0, highlightbackground='#1c1c1c', 
                             highlightthickness=1, padx=15, pady=10)
        frame_totales.pack(fill='x', padx=20, pady=10)
        
        lbl_total = Label(frame_totales, text="TOTAL DE VENTA:", font=('Helvetica 14 bold'),
                         bg="#cccccc", fg='#333333')
        lbl_total.grid(row=0, column=0, padx=10, sticky='w')
        
        self.lbl_monto_total = Label(frame_totales, text="$0.00", font=('Helvetica 16 bold'),
                                    bg="#cccccc", fg='#E91E63')
        self.lbl_monto_total.grid(row=0, column=1, sticky='e', padx=20)

        # Asegurar que la columna del monto se expanda
        frame_totales.columnconfigure(1, weight=1)

        # Frame para botones
        frame_botones = Frame(self, bg='#f5f5f5', pady=2)
        frame_botones.pack(fill='x', padx=20)

        # Estilo común para los botones
        estilo_botones = {
            'font': ('Open Sans', 13, 'bold'),
            'fg': 'white',
            'bd': 4,
            'padx': 20,
            'pady': -100,
            'activebackground': '#2e59d9',
            'activeforeground': 'white'
        }

        # Botón finalizar venta - Estilo destacado
        btn_finalizar = Button(frame_botones, text="FINALIZAR VENTA", 
                    command=self.finalizar_venta,
                    bg='#4CAF50',**estilo_botones)
        btn_finalizar.grid(row=0, column=0, padx=25)

        # Botón cancelar - Estilo de peligro
        btn_cancelar = Button(frame_botones, text="CANCELAR VENTA",
                    command=self.cancelar_venta,
                    bg='#f44336', 
                    **estilo_botones)
        btn_cancelar.grid(row=0, column=1, padx=25)

        # Botón Vale de Devolución - Estilo naranja
        btn_devolucion = Button(frame_botones, text="VALE DE DEVOLUCIÓN",
                    command=self.abrir_ventana_devolucion,
                    bg='#FF9800',
                    **estilo_botones)
        btn_devolucion.grid(row=0, column=2, padx=25)
        
        # Configurar el grid
        frame_principal.columnconfigure(1, weight=1)

        # Vincular eventos
        self.entry_CodigodeBarras.bind('<Return>', lambda event: self.buscar_producto())
        self.entry_CodigodeBarras.bind('<KeyRelease>', self.buscar_automatico)

     # NUEVA FUNCIÓN: Abrir ventana de consulta de vales de diferencia
    def abrir_ventana_vales_diferencia(self):
        """Abre una ventana para consultar vales de diferencia mediante código de barras"""
        ventana_vales = Toplevel(self)
        ventana_vales.title("Consultar Vales de Diferencia")
        ventana_vales.geometry("600x500")
        
        # Frame principal
        frame_principal = Frame(ventana_vales, padx=20, pady=20)
        frame_principal.pack(fill=BOTH, expand=True)
        
        # Título
        Label(frame_principal, text="Verificar Vale de Diferencia", 
              font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Frame para entrada de código de barras
        frame_codigo = Frame(frame_principal)
        frame_codigo.pack(fill=X, pady=10)
        
        Label(frame_codigo, text="Código de Barras:", font=('Helvetica', 10)).pack(side=LEFT)
        self.entry_codigo_vale = Entry(frame_codigo, font=('Helvetica', 12))
        self.entry_codigo_vale.pack(side=LEFT, padx=10, fill=X, expand=True)
        self.entry_codigo_vale.focus()
        
        # Botón para buscar
        btn_buscar = Button(frame_codigo, text="Buscar", 
                           command=self.buscar_vale_diferencia,
                           bg='#4CAF50', fg='white', font=('Helvetica', 10))
        btn_buscar.pack(side=LEFT, padx=5)
        
        # Frame para mostrar resultados
        frame_resultados = Frame(frame_principal)
        frame_resultados.pack(fill=BOTH, expand=True, pady=10)
        
        # Treeview para mostrar los resultados
        columns = ("Código", "Cliente", "Departamento", "Marca", "Color", "Talla", "Vale aplicado +$")
        self.tree_vales = ttk.Treeview(frame_resultados, columns=columns, show='headings', height=10)
        
        # Configurar columnas
        for col in columns:
            self.tree_vales.heading(col, text=col)
            self.tree_vales.column(col, width=100, anchor=CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_resultados, orient=VERTICAL, command=self.tree_vales.yview)
        self.tree_vales.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree_vales.pack(fill=BOTH, expand=True)
        
        # Vincular evento Enter al campo de código
        self.entry_codigo_vale.bind('<Return>', lambda e: self.buscar_vale_diferencia())

    # NUEVA FUNCIÓN: Buscar vales de diferencia
    def buscar_vale_diferencia(self):
        """Busca vales de diferencia por código de barras"""
        codigo = self.entry_codigo_vale.get().strip()
        if not codigo:
            messagebox.showwarning("Advertencia", "Por favor ingrese un código de barras")
            return
        
        try:
            # Limpiar resultados anteriores
            for item in self.tree_vales.get_children():
                self.tree_vales.delete(item)
            
            # Consultar la tabla vales_diferencia
            self.cursor.execute("""SELECT CodigodeBarras, Cliente, Departamento, Marca, 
                                Color, Talla, vale_mas_diferencia 
                                FROM vales_diferencia WHERE CodigodeBarras=?""", (codigo,))
            resultados = self.cursor.fetchall()
            
            if resultados:
                for resultado in resultados:
                    # Formatear el valor de vale_mas_diferencia como moneda
                    resultado_lista = list(resultado)
                    resultado_lista[6] = self.formato_moneda(resultado_lista[6])
                    self.tree_vales.insert("", END, values=resultado_lista)
            else:
                messagebox.showinfo("Información", "No se encontraron vales de diferencia para este código")
                
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo consultar los vales de diferencia:\n{str(e)}")


    def mostrar_vista_previa_ticket(self, pdf_path):
        """Muestra una ventana con la vista previa del ticket usando pdf2image"""
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "No se pudo generar el ticket para vista previa")
            return
    
        # Crear ventana de vista previa más pequeña
        preview_window = Toplevel(self)
        preview_window.title("Vista Previa del Ticket")
        preview_window.geometry("400x550")  # Tamaño más pequeño (400x550)
    
        # Frame principal con padding reducido
        main_frame = Frame(preview_window)
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
    
        # Frame para el canvas con tamaño fijo
        canvas_frame = Frame(main_frame, width=580, height=600)
        canvas_frame.pack_propagate(True)  # Evita que el frame se ajuste al contenido
        canvas_frame.pack()
    
        # Canvas con scrollbars
        canvas = Canvas(canvas_frame, width=580, height=450)
        scroll_y = Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scroll_x = Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
    
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill=BOTH, expand=True)
    
        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    
        # Frame interno para la imagen
        inner_frame = Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
    
        try:
            # Convertir PDF a imagen con menor resolución para ahorrar espacio
            images = convert_from_path(pdf_path, dpi=160)  # DPI reducido para imagen más pequeña
        
            if images:
                # Guardar la primera página como imagen temporal
                temp_img_path = os.path.join(tempfile.gettempdir(), "ticket_preview.png")
                images[0].save(temp_img_path, 'PNG')
            
                # Cargar la imagen y redimensionarla para que encaje en el canvas
                img = Image.open(temp_img_path)
            
                # Calcular nuevo tamaño manteniendo aspecto (ancho máximo 380)
                original_width, original_height = img.size
                aspect_ratio = original_height / original_width
                new_width = 580
                new_height = int(new_width * aspect_ratio)
            
                # Si la altura es muy grande, ajustamos
                if new_height > 1600:
                    new_height = 1600
                    new_width = int(new_height / aspect_ratio)
            
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
                img_tk = ImageTk.PhotoImage(img)
            
                # Mostrar la imagen en el canvas
                label = Label(inner_frame, image=img_tk)
                label.image = img_tk  # Mantener referencia
                label.pack()
            
                # Configurar el scroll del canvas
                inner_frame.update_idletasks()
                canvas.config(scrollregion=canvas.bbox("all"))
            
                # Eliminar la imagen temporal
                try:
                    os.remove(temp_img_path)
                except:
                    pass
            else:
                Label(inner_frame, 
                    text="No se pudo generar la vista previa del ticket",
                    font=('Helvetica', 12)).pack(pady=50)
            
        except Exception as e:
            Label(inner_frame, 
                text=f"Error al generar vista previa: {str(e)}",
                font=('Helvetica', 12)).pack(pady=50)
    
        # Frame para botones (debajo del canvas)
        btn_frame = Frame(main_frame)
        btn_frame.pack(pady=5)
    
        # Botón para imprimir directamente
        Button(btn_frame, text="Imprimir Ticket", 
            command=lambda: self.imprimir_ticket(pdf_path, preview_window),
            bg="#4CAF50", fg="white", font=('Helvetica', 10, 'bold')).pack(side=LEFT, padx=5)
    
        # Botón para cerrar
        Button(btn_frame, text="Cerrar", 
            command=preview_window.destroy,
            bg="#f44336", fg="white", font=('Helvetica', 10, 'bold')).pack(side=LEFT, padx=5)

    def mostrar_ticket_basico(self):
        """Muestra una ventana con el ticket en formato de texto básico"""
        ticket_window = Toplevel(self)
        ticket_window.title("Vista Previa del Ticket")
        ticket_window.geometry("500x600")
        
        # Frame principal
        frame = Frame(ticket_window)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Área de texto con scroll
        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        text_area = Text(frame, wrap=WORD, yscrollcommand=scrollbar.set,
                        font=('Courier New', 10))
        text_area.pack(fill=BOTH, expand=True)
        scrollbar.config(command=text_area.yview)
        
        # Generar contenido del ticket
        contenido = []
        contenido.append("MUILTIMARCAS TURQUESA".center(50))
        contenido.append("Carretera Antigua Camp-Merida #341".center(50))
        contenido.append("Col.Santa Lucia, Campeche, Campeche".center(50))
        contenido.append("\nTICKET DE VENTA".center(50))
        contenido.append(datetime.now().strftime("%d/%m/%Y %H:%M:%S").center(50))
        contenido.append("-"*50)
        
        # Detalles de productos
        contenido.append("\nPRODUCTOS:")
        contenido.append("-"*50)
        contenido.append(f"{'Descripción':<30}{'Cant':>5}{'P.U.':>10}{'Total':>10}")
        contenido.append("-"*50)
        
        total_venta = 0
        for codigo, datos in self.productos_agregados.items():
            descripcion = f"{datos['marca']} {datos['color']}"
            if len(descripcion) > 30:
                descripcion = descripcion[:27] + "..."
            
            linea = f"{descripcion:<30}{datos['cantidad']:>5}" \
                   f"{datos['precio']:>10.2f}" \
                   f"{(datos['precio'] * datos['cantidad']):>10.2f}"
            contenido.append(linea)
            total_venta += datos['precio'] * datos['cantidad']
        
        # Total
        contenido.append("-"*50)
        contenido.append(f"{'TOTAL:':>45}{total_venta:>10.2f}")
        contenido.append("-"*50)
        
        # Forma de pago
        if any(codigo in self.productos_transferencia for codigo in self.productos_agregados):
            contenido.append("\nFORMA DE PAGO: TRANSFERENCIA")
        
        if self.productos_agregados:
            primer_producto = next(iter(self.productos_agregados.values()))
            nombre_cliente = primer_producto['cliente'] if primer_producto['cliente'] else "Consumidor Final"

            contenido.append(f"\nCliente: {nombre_cliente}")
        else:
            contenido.append("\nCliente: Consumidor Final")
        
        # Pie del ticket
        contenido.append("\n\nGracias por su compra!")


        # Insertar contenido en el área de texto
        text_area.insert(END, "\n".join(contenido))
        text_area.config(state=DISABLED)  # Hacerlo de solo lectura
        
        # Botones
        btn_frame = Frame(ticket_window)
        btn_frame.pack(pady=10)
        
        Button(btn_frame, text="Imprimir PDF", 
               command=self.generar_ticket_pdf,
               bg="#4CAF50", fg="white").pack(side=LEFT, padx=5)
        
        Button(btn_frame, text="Cerrar", 
               command=ticket_window.destroy,
               bg="#f44336", fg="white").pack(side=LEFT, padx=5)

    
    def generar_ticket_pdf(self, mostrar_mensaje=True):
        """Genera un PDF optimizado para impresora térmica Epson TM-U220 con productos en lista vertical"""
        try:
            # Configuración para impresora térmica (80mm de ancho)
            width = 80 * mm
            height = 400 * mm  # Más alto para evitar cortes
            custom_size = (width, height)

            Temp_dir = tempfile.gettempdir()

            # Verificar permisos de escritura
            if not os.access(Temp_dir, os.W_OK):
                messagebox.showerror("Error", f"No hay permisos de escritura en: {Temp_dir}")
                return None

            pdf_path = os.path.join(self.Temp_dir, "ticket_venta.pdf")
            c = canvas.Canvas(pdf_path, pagesize=custom_size)

            # Configuración de márgenes y posición inicial
            margin_left = 5 * mm
            margin_right = 5 * mm
            y_position = height - 10 * mm

            # Fuentes mejoradas para mejor legibilidad
            c.setFont("Helvetica-Bold", 13)

            # Encabezado centrado
            c.drawCentredString(width/2, y_position, "MULTIMARCAS TURQUESA")
            y_position -= 6 * mm
            c.setFont("Helvetica", 11)
            c.drawCentredString(width/2, y_position, "Carretera Antigua Camp-Merida #341")
            y_position -= 5 * mm
            c.drawCentredString(width/2, y_position, "Col.Santa Lucia, Campeche, Campeche")
            y_position -= 8 * mm

            # Fecha y título
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(width/2, y_position, "TICKET DE VENTA")
            y_position -= 5 * mm
            c.setFont("Helvetica", 11)
            c.drawCentredString(width/2, y_position, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            y_position -= 10 * mm

            # Línea divisoria
            c.setLineWidth(0.5)
            # Podrías crear una línea de guiones manualmente:
            guiones = "-" * 55  # 40 guiones
            c.drawString(margin_left, y_position, guiones)
            y_position -= 8 * mm

            # Encabezado de productos
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin_left, y_position, "DETALLE DE PRODUCTOS:")
            y_position -= 8 * mm

            # Detalles de productos en formato de lista vertical
            c.setFont("Helvetica", 12)
            total_venta = 0

            for codigo, datos in self.productos_agregados.items():
                # Mostrar todos los datos del producto en líneas separadas
                c.drawString(margin_left, y_position,f"Código: {codigo}")
                y_position -= 5 * mm
        
                c.drawString(margin_left, y_position, f"Cliente: {datos['cliente']}")
                y_position -= 5 * mm
        
                c.drawString(margin_left, y_position, f"Departamento: {datos['departamento']}")
                y_position -= 5 * mm
        
                c.drawString(margin_left, y_position, f"Marca: {datos['marca']}")
                y_position -= 5 * mm
        
                c.drawString(margin_left, y_position, f"Color: {datos['color']}")
                y_position -= 5 * mm
            
                # NUEVO: Campo Talla agregado después de Color
                c.drawString(margin_left, y_position, f"Talla: {datos['talla']}")
                y_position -= 5 * mm
        
                c.drawString(margin_left, y_position, f"Precio: ${datos['precio']:.2f}")
                y_position -= 5 * mm
        
                y_position -= 8 * mm
        
                # Podrías crear una línea de guiones manualmente:
                guiones = "-" * 50  # 50 guiones
                c.drawString(margin_left, y_position, guiones)
                y_position -= 8 * mm
        
                total_venta += datos['precio'] * datos['cantidad']
        
                # Salto de página si es necesario
                if y_position < 20 * mm:
                    c.showPage()
                    y_position = height - 10 * mm
                    c.setFont("Helvetica", 9)

            # Línea divisoria antes del total
            y_position -= 4 * mm
            # Podrías crear una línea de guiones manualmente:
            guiones = "-" * 50  # 50 guiones
            c.drawString(margin_left, y_position, guiones)
            y_position -= 8 * mm

            # NUEVA SECCIÓN: Mostrar vales de diferencia y diferencias
            # Consultar la tabla vales_diferencia para esta venta
            try:
                # Obtener todos los códigos de productos en la venta
                codigos_venta = list(self.productos_agregados.keys())
                if codigos_venta:
                    # Crear marcador de posición para la consulta SQL
                    placeholders = ','.join(['?' for _ in codigos_venta])
                    
                    # Consultar vales de diferencia para los productos en esta venta
                    query = f"""SELECT CodigodeBarras, vale_menos_diferencia, Diferencia 
                                FROM vales_diferencia 
                                WHERE CodigodeBarras IN ({placeholders})"""
                    
                    self.cursor.execute(query, codigos_venta)
                    resultados_diferencias = self.cursor.fetchall()
                    
                    # Variables para acumular totales de diferencias
                    total_vale_menos = 0
                    total_diferencia = 0
                    
                    if resultados_diferencias:
                        c.setFont("Helvetica-Bold", 11)
                        c.drawString(margin_left, y_position, "DIFERENCIAS APLICADAS:")
                        y_position -= 8 * mm
                        
                        c.setFont("Helvetica", 11)
                        for resultado in resultados_diferencias:
                            codigo, vale_menos, diferencia = resultado
                            
                            # Mostrar vale de diferencia (-) si existe
                            if vale_menos and vale_menos > 0:
                                # Mostrar el código del producto en línea separada e indentado
                                c.drawString(margin_left + 10, y_position, f"Vale de diferencia:")
                                y_position -= 5 * mm
                                c.drawString(margin_left + 20, y_position, f"[Código: {codigo}]: -{self.formato_moneda(vale_menos)}")
                                y_position -= 7 * mm
                                total_vale_menos += vale_menos

                            # Mostrar diferencia ($) si existe
                            if diferencia and diferencia != 0:
                                signo = "+" if diferencia > 0 else ""
                                # Mostrar el código del producto en línea separada e indentado
                                c.drawString(margin_left + 10, y_position, f"Diferencia pagada:")
                                y_position -= 5 * mm
                                c.drawString(margin_left + 20, y_position, f"[Código: {codigo}]: {signo}{self.formato_moneda(diferencia)}")
                                y_position -= 7 * mm
                                total_diferencia += diferencia
                            
                            # Salto de página si es necesario
                            if y_position < 20 * mm:
                                c.showPage()
                                y_position = height - 10 * mm
                                c.setFont("Helvetica", 9)
                        
                        # Línea divisoria después de diferencias
                        guiones = "-" * 50
                        c.drawString(margin_left, y_position, guiones)
                        y_position -= 8 * mm
                        
                        # Ajustar el total de la venta con las diferencias
                        total_venta = total_venta
            except sqlite3.Error as e:
                # Si hay error en la consulta, continuar sin mostrar diferencias
                print(f"Error al consultar diferencias: {str(e)}")

            # Total con formato destacado
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin_left, y_position, "TOTAL:")
            c.drawRightString(width - margin_right, y_position, f"${total_venta:.2f}")
            y_position -= 11 * mm

            # Forma de pago si es transferencia
            if any(codigo in self.productos_transferencia for codigo in self.productos_agregados):
                c.setFont("Helvetica-Bold", 10)
                c.drawCentredString(width/2, y_position, "FORMA DE PAGO: TRANSFERENCIA")
                y_position -= 10 * mm

            # Pie del ticket
            c.setFont("Helvetica", 12)
            c.drawCentredString(width/2, y_position, "Gracias por su compra!")
            y_position -= 7 * mm

            if self.productos_agregados:
                primer_producto = next(iter(self.productos_agregados.values()))
                nombre_cliente = primer_producto['cliente'] if primer_producto['cliente'] else "Consumidor Final"

                c.drawCentredString(width/2, y_position, f"Cliente: {nombre_cliente}")
            else:
                c.drawCentredString(width/2, y_position, "Cliente: Consumidor Final")
            y_position -= 10 * mm

            # Línea de corte simbólica
            # Podrías crear una línea de guiones manualmente:
            guiones = "-" * 50  # 40 guiones
            c.drawString(margin_left, y_position, guiones)
            c.save()

            # Verificar y mostrar el PDF
            if not os.path.exists(pdf_path):
                raise Exception("No se pudo crear el archivo PDF")

            if mostrar_mensaje:
                messagebox.showinfo("Éxito", f"Ticket generado en:\n{pdf_path}")

            return pdf_path

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el ticket: {str(e)}")
        return None
    

    def imprimir_ticket(self, pdf_path, window):
        """Imprime el ticket directamente usando la impresora predeterminada"""
        try:
            if not os.path.exists(pdf_path):
                messagebox.showerror("Error", "El archivo del ticket no existe")
                return
        
            printer_name = win32print.GetDefaultPrinter()
        
            if not printer_name:
                messagebox.showerror("Error", "No se encontró impresora predeterminada")
                return
        
            win32api.ShellExecute(
                0,
                "print",
                pdf_path,
                f'/d:"{printer_name}"',
                ".",
                0
            )
        
            messagebox.showinfo("Éxito", f"Ticket enviado a impresión en {printer_name}")
            window.destroy()
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo imprimir el ticket: {str(e)}")

    def marcar_transferencia(self):
        """Marca los productos seleccionados como pagados por transferencia"""
        seleccionados = self.tree.selection()
        if not seleccionados:
            messagebox.showwarning("Advertencia", "Por favor seleccione al menos un producto")
            return
    
        # Mostrar diálogo para ingresar monto de transferencia
        dialogo = Toplevel(self)
        dialogo.title("Monto de Transferencia")
        dialogo.geometry("300x150")
    
        Label(dialogo, text="Ingrese el monto de la transferencia:", font=('Helvetica', 10)).pack(pady=10)
    
        self.entry_monto_transferencia = Entry(dialogo, font=('Helvetica', 12))
        self.entry_monto_transferencia.pack(pady=5, padx=20, fill='x')
    
        def guardar_transferencia():
            try:
                monto = float(self.entry_monto_transferencia.get())
                if monto <= 0:
                    raise ValueError("El monto debe ser positivo")
            
                # Actualizar productos seleccionados
                for item in seleccionados:
                    valores = self.tree.item(item, 'values')
                    codigo = valores[0]
                    # Guardar como tupla (código, monto) en lugar de solo el código
                    self.productos_transferencia.add((codigo, monto))
                    self.tree.set(item, "Transferencia", "Sí")
            
                dialogo.destroy()
            
            except ValueError as e:
                messagebox.showerror("Error", f"Monto inválido: {str(e)}")
    
        btn_guardar = Button(dialogo, text="Guardar", command=guardar_transferencia,
                        bg='#4CAF50', fg='white', font=('Helvetica', 10, 'bold'))
        btn_guardar.pack(pady=10)

    def marcar_devolucion(self):
        """Marca los productos seleccionados como vale de devolución (no se registrarán en inventario)"""
        seleccionados = self.tree.selection()
        if not seleccionados:
            messagebox.showwarning("Advertencia", "Por favor seleccione al menos un producto")
            return
    
        for item in seleccionados:
            valores = self.tree.item(item, 'values')
            codigo = valores[0]
            # Alternar entre marcado y desmarcado
            if codigo in self.productos_devolucion:
                self.productos_devolucion.remove(codigo)
                self.tree.set(item, "Transferencia", "No")
            else:
                self.productos_devolucion.add(codigo)
                self.tree.set(item, "Transferencia", "Devolución")
    
        messagebox.showinfo("Información", "Productos marcados como vale de devolución. No se registrarán en inventario.")

    def marcar_todos_transferencia(self):
        """Marca todos los productos como pagados por transferencia"""
        if not self.productos_agregados:
            messagebox.showwarning("Advertencia", "No hay productos en la venta")
            return
    
        # Mostrar diálogo para ingresar monto total de transferencia
        dialogo = Toplevel(self)
        dialogo.title("Monto Total de Transferencia")
        dialogo.geometry("300x150")
    
        Label(dialogo, text="Ingrese el monto total de la transferencia:", font=('Helvetica', 10)).pack(pady=10)
    
        self.entry_monto_total_transferencia = Entry(dialogo, font=('Helvetica', 12))
        self.entry_monto_total_transferencia.pack(pady=5, padx=20, fill='x')
    
        def guardar_transferencia_total():
            try:
                monto_total = float(self.entry_monto_total_transferencia.get())
                if monto_total <= 0:
                    raise ValueError("El monto debe ser positivo")
            
                # Calcular monto proporcional por producto
                total_venta = sum(datos['precio'] * datos['cantidad'] for datos in self.productos_agregados.values())
            
                # Marcar todos los productos como transferencia con monto proporcional
                for item in self.tree.get_children():
                    valores = self.tree.item(item, 'values')
                    codigo = valores[0]
                    precio_producto = float(valores[6].replace('$', '').replace(',', ''))
                    cantidad = int(valores[7])
                
                    # Calcular monto proporcional para este producto
                    monto_proporcional = (precio_producto * cantidad / total_venta) * monto_total
                
                    # Guardar como tupla (código, monto)
                    self.productos_transferencia.add((codigo, monto_proporcional))
                    self.tree.set(item, "Transferencia", "Sí)")
            
                dialogo.destroy()
            
            except ValueError as e:
                messagebox.showerror("Error", f"Monto inválido: {str(e)}")
    
        btn_guardar = Button(dialogo, text="Guardar", command=guardar_transferencia_total,
                        bg='#4CAF50', fg='white', font=('Helvetica', 10, 'bold'))
        btn_guardar.pack(pady=10)


    def buscar_avanzada(self):
        """Método para realizar búsqueda avanzada"""
        # Obtener parámetros de búsqueda
        cliente = self.entry_buscar_cliente.get().strip()
        apellido = self.entry_buscar_apellido.get().strip()
        marca = self.entry_buscar_marca.get().strip()
        departamento = self.entry_buscar_departamento.get().strip()

        if not cliente and not apellido and not marca and not departamento:
            messagebox.showwarning("Búsqueda avanzada", "Debe ingresar al menos un criterio de búsqueda")
            return

        # Construir consulta SQL dinámica
        query = "SELECT CodigodeBarras, Cliente, Departamento, Marca, Color, Talla, PrecioProducto, Stock, Fechaingreso, Fechavencimiento FROM registro_productos WHERE 1=1"
        params = []
        
        if cliente:
            query += " AND Cliente LIKE ?"
            params.append(f"%{cliente}%")
        if apellido:
            query += " AND Cliente LIKE ?"
            params.append(f"%{apellido}%")
        if marca:
            query += " AND Marca LIKE ?"
            params.append(f"%{marca}%")
        if departamento:
            query += " AND Departamento LIKE ?"
            params.append(f"%{departamento}%")

        try:
            self.cursor.execute(query, params)
            resultados = self.cursor.fetchall()

            if not resultados:
                messagebox.showinfo("Resultados", "No se encontraron productos con esos criterios")
                return

            # Mostrar resultados en ventana emergente
            self.mostrar_resultados_busqueda(resultados)

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error en la búsqueda:\n{str(e)}")

    def formato_moneda_input(self, valor):
        """Formatea un número con separadores de miles y 2 decimales"""
        try:
            # Remover comas existentes y convertir a float
            valor_limpio = valor.replace(',', '')
            numero = float(valor_limpio)
            # Formatear con comas y 2 decimales
            return "{:,.2f}".format(numero)
        except ValueError:
            return valor
        

    def validar_entrada_moneda(self, event, entry_widget, prefijo):
        """Valida y formatea la entrada monetaria"""
        texto_actual = entry_widget.get()
    
        # Si el texto no comienza con el prefijo, restaurarlo
        if not texto_actual.startswith(prefijo):
            entry_widget.delete(0, END)
            entry_widget.insert(0, prefijo)
            return
    
        # Obtener solo la parte numérica
        parte_numerica = texto_actual.replace(prefijo, '').replace(',', '')
    
        # Permitir solo números y un punto decimal
        if parte_numerica and not parte_numerica.replace('.', '').isdigit():
            # Eliminar caracteres no válidos
            nuevo_texto = ''.join(c for c in parte_numerica if c.isdigit() or c == '.')
            entry_widget.delete(0, END)
            entry_widget.insert(0, prefijo + nuevo_texto)
            return
    
        # Formatear con comas si hay un valor numérico
        if parte_numerica.replace('.', '').isdigit() and parte_numerica:
            try:
                numero = float(parte_numerica)
                formateado = "{:,.2f}".format(numero)
                entry_widget.delete(0, END)
                entry_widget.insert(0, prefijo + formateado)
            except ValueError:
                pass


    def abrir_ventana_diferencia(self, event):
        """Abre ventana para gestionar diferencias al hacer doble clic en un producto"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
    
        item = self.tree.item(seleccion[0])
        valores = item['values']
        codigo_barras = valores[0]
    
        # Buscar el producto en la base de datos para obtener todos los datos
        try:
            self.cursor.execute("""SELECT * FROM registro_productos WHERE CodigodeBarras=?""", (codigo_barras,))
            producto = self.cursor.fetchone()
        
            if producto:
                # Crear ventana de diferencia
                ventana_diferencia = Toplevel(self)
                ventana_diferencia.title("Gestión de Diferencias")
                ventana_diferencia.geometry("500x400")
            
                # Frame principal
                frame_principal = Frame(ventana_diferencia, padx=20, pady=20)
                frame_principal.pack(fill=BOTH, expand=True)
            
                # Título
                Label(frame_principal, text="GESTIÓN DE DIFERENCIAS", 
                font=('Helvetica', 14, 'bold')).pack(pady=10)
            
                # Información del producto
                Label(frame_principal, text=f"Producto: {producto[3]} {producto[4]}", 
                font=('Helvetica', 10)).pack(pady=5)
                Label(frame_principal, text=f"Código: {producto[1]}", 
                font=('Helvetica', 10)).pack(pady=2)
            
                # Campos de entrada
                frame_campos = Frame(frame_principal)
                frame_campos.pack(pady=20, fill=X)
            
                # Vale de diferencia (-)
                Label(frame_campos, text="Vale de diferencia:", 
                font=('Helvetica', 10)).grid(row=0, column=0, sticky=W, pady=5)
                self.entry_vale_menos = Entry(frame_campos, font=('Helvetica', 12))
                self.entry_vale_menos.grid(row=0, column=1, sticky=EW, pady=5, padx=10)
                self.entry_vale_menos.insert(0, "-$")
                # Vincular evento para validar entrada
                self.entry_vale_menos.bind('<KeyRelease>', 
                    lambda e: self.validar_entrada_moneda(e, self.entry_vale_menos, "-$"))
            
                # Vale de diferencia aplicado (+)
                Label(frame_campos, text="Vale de diferencia aplicado:", 
                font=('Helvetica', 10)).grid(row=1, column=0, sticky=W, pady=5)
                self.entry_vale_mas = Entry(frame_campos, font=('Helvetica', 12))
                self.entry_vale_mas.grid(row=1, column=1, sticky=EW, pady=5, padx=10)
                self.entry_vale_mas.insert(0, "+$")
                # Vincular evento para validar entrada
                self.entry_vale_mas.bind('<KeyRelease>', 
                    lambda e: self.validar_entrada_moneda(e, self.entry_vale_mas, "+$"))
            
                # Diferencia ($) - EDITABLE MANUALMENTE
                Label(frame_campos, text="Diferencia:", 
                font=('Helvetica', 10, 'bold')).grid(row=2, column=0, sticky=W, pady=5)
                self.entry_diferencia = Entry(frame_campos, font=('Helvetica', 12))
                self.entry_diferencia.grid(row=2, column=1, sticky=EW, pady=5, padx=10)
                self.entry_diferencia.insert(0, "$")
                # Vincular evento para validar entrada
                self.entry_diferencia.bind('<KeyRelease>', 
                    lambda e: self.validar_entrada_moneda(e, self.entry_diferencia, "$"))
            
                # Configurar peso de columnas
                frame_campos.columnconfigure(1, weight=1)
            
                # Botones
                frame_botones = Frame(frame_principal)
                frame_botones.pack(pady=20)
            
                btn_guardar = Button(frame_botones, text="Guardar Diferencia", 
                            command=lambda: self.guardar_diferencia(producto, ventana_diferencia),
                            bg='#4CAF50', fg='white', font=('Helvetica', 10, 'bold'))
                btn_guardar.pack(side=LEFT, padx=10)
            
                btn_cancelar = Button(frame_botones, text="Cancelar", 
                                command=ventana_diferencia.destroy,
                                bg='#f44336', fg='white', font=('Helvetica', 10))
                btn_cancelar.pack(side=LEFT, padx=10)
            
                # Guardar referencia a los datos del producto
                self.producto_actual = producto
            
        except sqlite3.Error as e:
                messagebox.showerror("Error", f"No se pudo obtener información del producto:\n{str(e)}")

    def actualizar_diferencia(self):
        """Calcula y actualiza la diferencia automáticamente"""
        try:
            # Obtener valores y limpiarlos
            menos_str = self.entry_vale_menos.get().replace('-', '').replace('+', '').strip()
            mas_str = self.entry_vale_mas.get().replace('+', '').replace('-', '').strip()
        
            # Convertir a float, si están vacíos usar 0
            menos = float(menos_str) if menos_str else 0.0
            mas = float(mas_str) if mas_str else 0.0
        
            # Calcular diferencia
            diferencia = mas - menos
        
            # Formatear diferencia con signo de dólar y separadores de miles
            diferencia_formateada = "${:,.2f}".format(diferencia)
        
            # Actualizar campo de diferencia
            self.entry_diferencia.config(state='normal')
            self.entry_diferencia.delete(0, END)
            self.entry_diferencia.insert(0, diferencia_formateada)
            self.entry_diferencia.config(state='readonly')
        
        except ValueError:
            # Si hay error en la conversión, limpiar el campo de diferencia
            self.entry_diferencia.config(state='normal')
            self.entry_diferencia.delete(0, END)
            self.entry_diferencia.config(state='readonly')

    def guardar_diferencia(self, producto, ventana):
        """Guarda la diferencia en la base de datos y actualiza el inventario"""
        try:
            # Obtener y limpiar valores (remover signos y comas)
            menos_str = self.entry_vale_menos.get().replace('-$', '').replace(',', '').strip()
            mas_str = self.entry_vale_mas.get().replace('+$', '').replace(',', '').strip()
            diferencia_str = self.entry_diferencia.get().replace('$', '').replace(',', '').strip()
    
            # Validar que al menos un campo tenga valor
            if not menos_str and not mas_str and not diferencia_str:
                messagebox.showwarning("Advertencia", "Debe ingresar al menos un valor en los campos de diferencia")
                return
    
            # Convertir a float, si están vacíos usar 0
            menos = float(menos_str) if menos_str else 0.0
            mas = float(mas_str) if mas_str else 0.0
            diferencia = float(diferencia_str) if diferencia_str else 0.0
    
            # Crear nuevo registro de diferencia
            nueva_diferencia = ValesDiferencia(
            CodigodeBarras=producto[1],
            Cliente=producto[2],
            Departamento=producto[3],
            Marca=producto[4],
            Color=producto[5],
            Talla=producto[6],
            vale_menos_diferencia=menos,
            vale_mas_diferencia=mas,
            Diferencia=diferencia,
            Id_productos=producto[0]
            )
    
            # Guardar en la base de datos
            self.session.add(nueva_diferencia)
            self.session.commit()
    
            # SI HAY DIFERENCIA POSITIVA, ACTUALIZAR EL INVENTARIO
            if diferencia > 0:
                self.actualizar_inventario_con_diferencia(producto, diferencia)
    
            messagebox.showinfo("Éxito", "Diferencia guardada correctamente")
            ventana.destroy()
    
        except ValueError:
            messagebox.showerror("Error", "Los valores ingresados deben ser números válidos")
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error", f"No se pudo guardar la diferencia:\n{str(e)}")

    def actualizar_inventario_con_diferencia(self, producto, diferencia):
        """Actualiza el inventario con la diferencia positiva"""
        try:
            # Buscar si ya existe un registro de inventario para este producto
            inventario_existente = self.session.query(InventarioModel).filter_by(
                Id_productos=producto[0]
            ).first()
    
            if inventario_existente:
                # Si existe, actualizar el precio del producto sumando la diferencia
                inventario_existente.PrecioProducto += diferencia
            else:
                # Si no existe, crear un nuevo registro de inventario
                nuevo_inventario = InventarioModel(
                CodigodeBarras=producto[1],
                Cliente=producto[2],
                Stock=0,  # No afectamos el stock, solo el precio
                PrecioProducto=producto[6] + diferencia,  # Precio original + diferencia
                Id_productos=producto[0]
                )
                self.session.add(nuevo_inventario)
    
            self.session.commit()
            print(f"Inventario actualizado: Se sumó ${diferencia} al producto {producto[1]}")
    
        except Exception as e:
            self.session.rollback()
            print(f"Error al actualizar inventario: {str(e)}")


    def mostrar_resultados_busqueda(self, resultados):
        """Muestra los resultados de búsqueda en una ventana emergente"""
        ventana_resultados = Toplevel(self)
        ventana_resultados.title("Resultados de Búsqueda")
        ventana_resultados.geometry("900x500")

        # Frame principal
        frame_principal = Frame(ventana_resultados)
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview para resultados
        tree = ttk.Treeview(frame_principal, columns=("Código", "Cliente", "Departamento", "Marca", "Color", "Talla", "Precio", "Stock", "Fecha de ingreso", "Fecha de vencimiento"), show='headings')
        
        # Configurar columnas
        columnas = [
            ("Código", 100),
            ("Cliente", 150),
            ("Departamento", 120),
            ("Marca", 100),
            ("Color", 220),
            ("Talla", 220),
            ("Precio", 100),
            ("Stock", 80),
            ("Fecha de ingreso", 91),
            ("Fecha de vencimiento", 105)
        ]

        for col, width in columnas:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor=tk.CENTER)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_principal, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Insertar datos
        for producto in resultados:
            tree.insert("", tk.END, values=producto)

        # Botón para agregar selección
        btn_agregar = Button(ventana_resultados, text="Agregar Producto Seleccionado",
                            command=lambda: self.agregar_desde_busqueda(tree),
                            bg='#4CAF50', fg='white', font=('Helvetica', 9, 'bold'))
        btn_agregar.pack(pady=10)

    def agregar_desde_busqueda(self, tree):
        """Agrega el producto seleccionado a la venta actual"""
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione un producto")
            return

        item = tree.item(seleccion[0])
        codigo = item['values'][0]
        
        # Simular entrada del código de barras
        self.entry_CodigodeBarras.delete(0, tk.END)
        self.entry_CodigodeBarras.insert(0, codigo)
        self.buscar_producto()

        # Cerrar la ventana de resultados de búsqueda
        for widget in self.winfo_children():
            if isinstance(widget, Toplevel) and widget.title() == "Resultados de Búsqueda":
                widget.destroy()
                break

    def buscar_automatico(self, event):
        if len(self.entry_CodigodeBarras.get()) >= 7:  # Asumiendo códigos de barras de 7+ dígitos
            self.buscar_producto()

    def buscar_producto(self):
        CodigodeBarras = self.entry_CodigodeBarras.get().strip()
        if not CodigodeBarras:
            messagebox.showerror("Error", "Por favor ingrese un código de barras")
            return
        
        try:
            # Buscar producto incluyendo el stock
            self.cursor.execute("""SELECT CodigodeBarras, Cliente, Departamento, Marca, Color, Talla, PrecioProducto, Stock FROM registro_productos WHERE CodigodeBarras=?""", (CodigodeBarras,))
            producto = self.cursor.fetchone()
            
            if producto:
                codigo_barras, cliente, departamento, marca, color, talla, precio, stock = producto

                # Verificar si ya se agregó este producto (usando el código de barras como referencia)
                if codigo_barras in self.productos_agregados:
                    # Si el producto ya está en la venta, aumentar cantidad
                    cantidad_actual = self.productos_agregados[codigo_barras]['cantidad']
                    if cantidad_actual + 1 > stock:
                        messagebox.showwarning("Stock insuficiente", 
                                         f"No hay suficiente stock. Disponible: {stock}")
                        return
                    else:
                        # Incrementar cantidad y actualizar stock restante
                        self.productos_agregados[codigo_barras]['cantidad'] += 1
                        self.productos_agregados[codigo_barras]['stock'] = stock - self.productos_agregados[codigo_barras]['cantidad']
                else:
                    # Agregar nuevo producto si hay stock
                    if stock <= 0:
                        messagebox.showwarning("Stock agotado", "Este producto no tiene stock disponible.")
                        return
                    self.productos_agregados[codigo_barras] = {
                        'cliente': cliente,
                        'departamento': departamento,
                        'marca': marca,
                        'color': color,
                        'talla': talla,
                        'precio': precio,
                        'cantidad': 1,
                        'stock': stock - 1
                    }
                
                # Actualizar la lista de productos
                self.actualizar_lista_productos()
                self.entry_CodigodeBarras.delete(0, END)
                self.entry_CodigodeBarras.focus()
            else:
                messagebox.showinfo("Resultado", "Producto no encontrado")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo buscar el producto:\n{str(e)}")

    def actualizar_lista_productos(self):
        # Limpiar la lista actual
        for item in self.tree.get_children():
            self.tree.delete(item)
    
        # Agregar todos los productos del diccionario
        total_venta = 0
        for codigo, datos in self.productos_agregados.items():
            total = datos['precio'] * datos['cantidad']
        
             # Verificar si el producto está marcado como transferencia
            transferencia = "Sí" if any(item[0] == codigo for item in self.productos_transferencia) else "No"

            self.tree.insert("", "end", values=(
            codigo,
            datos['cliente'],
            datos['departamento'],
            datos['marca'],
            datos['color'],
            datos['talla'],           # Columna "Talla" (nueva)
            self.formato_moneda(datos['precio']),  # Formatear precio unitario
            datos['cantidad'],
            datos['stock'],
            self.formato_moneda(total),  # Formatear total por producto
            transferencia
            ))
        
            total_venta += total
    
        # Actualizar el total de la venta con formato
        self.lbl_monto_total.config(text=self.formato_moneda(total_venta))

    def finalizar_venta(self):
        if not self.productos_agregados:
            messagebox.showwarning("Venta vacía", "No hay productos en la venta")
            return

        try:
            # Primero verificar que todo el stock esté disponible
            for codigo, datos in self.productos_agregados.items():
                self.cursor.execute("SELECT Stock FROM registro_productos WHERE CodigodeBarras=?", (codigo,))
                stock_actual = self.cursor.fetchone()[0]

                if datos['cantidad'] > stock_actual:
                    messagebox.showwarning("Stock insuficiente", 
                    f"No hay suficiente stock del producto {codigo}")
                    return

            # Procesar la venta
            for codigo, datos in self.productos_agregados.items():
                # Actualizar stock en la base de datos
                self.cursor.execute("""UPDATE registro_productos SET Stock = Stock - ? 
                            WHERE CodigodeBarras=?""", 
                        (datos['cantidad'], codigo))
        
                # Obtener el ID del producto
                self.cursor.execute("SELECT Id_productos FROM registro_productos WHERE CodigodeBarras=?", (codigo,))
                Id_productos = self.cursor.fetchone()[0]
        
                # Obtener los datos completos del producto
                self.cursor.execute("""SELECT CodigodeBarras, Cliente, PrecioProducto 
                            FROM registro_productos WHERE CodigodeBarras=?""", (codigo,))
                producto_data = self.cursor.fetchone()
        
                # CONSULTAR SI HAY DIFERENCIAS PARA ESTE PRODUCTO
                self.cursor.execute("""SELECT Diferencia FROM vales_diferencia 
                                WHERE CodigodeBarras=? AND Diferencia > 0""", (codigo,))
                diferencia_data = self.cursor.fetchone()
                diferencia = diferencia_data[0] if diferencia_data else 0.0
        
                # Calcular el precio final (precio original + diferencia)
                precio_final = datos['precio'] + diferencia
        
                # Registrar en Inventario SOLO si NO es un producto de devolución
                if codigo not in self.productos_devolucion:
                    inventario = InventarioModel(
                    CodigodeBarras=codigo,
                    Cliente=datos['cliente'],
                    Stock=datos['cantidad'],
                    PrecioProducto=precio_final,  # Usar el precio final con diferencia
                    Id_productos=Id_productos
                    )
                    self.session.add(inventario)

                    # Obtener el ID del producto y las fechas
                    self.cursor.execute("""SELECT Id_productos, Fechaingreso, Fechavencimiento 
                        FROM registro_productos WHERE CodigodeBarras=?""", (codigo,))
                    producto_data = self.cursor.fetchone()
                    Id_productos = producto_data[0]
                    fecha_ingreso = producto_data[1]
                    fecha_vencimiento = producto_data[2]
        
                    vale_devolucion = ValesDevolucion(
                    CodigodeBarras=codigo,
                    Cliente=datos['cliente'],
                    Marca=datos['marca'],
                    Color=datos['color'],
                    PrecioProducto=precio_final,  # Usar el precio final con diferencia
                    Fechaingreso=fecha_ingreso,
                    Fechavencimiento=fecha_vencimiento,
                    Id_productos=Id_productos
                    )
                    self.session.add(vale_devolucion)

                # Inicializar monto_transferencia fuera del condicional
                monto_transferencia = None
            
                # Si el producto fue pagado por transferencia, guardar en la tabla transferencias_diferencias
                if codigo in [item[0] for item in self.productos_transferencia] and codigo not in self.productos_devolucion:
                    # Buscar el monto específico para este producto
                    monto_transferencia = None
                    for item in self.productos_transferencia:
                        if item[0] == codigo:
                            monto_transferencia = item[1]
                            break

                    # Si no encontramos un monto específico, usar el precio total como fallback
                    if monto_transferencia is None:
                        monto_transferencia = precio_final * datos['cantidad']  # Usar precio final

                    transferencia = TransferenciasDiferencias(
                        Monto=monto_transferencia,  # Usar el monto ingresado por el usuario
                        CodigodeBarras=codigo,
                        Cliente=datos['cliente'],
                        Marca=datos['marca'],
                        PrecioProducto=precio_final,  # Usar el precio final con diferencia
                        Id_productos=Id_productos
                    )
                    self.session.add(transferencia)

            # Confirmar todas las transacciones
            self.sqliteConnection.commit()
            self.session.commit()
    
            # Generar el PDF (sin mostrar mensaje)
            pdf_path = self.generar_ticket_pdf(mostrar_mensaje=False)
    
            # Mostrar vista previa
            self.mostrar_vista_previa_ticket(pdf_path)
    
            # Limpiar la venta
            self.productos_agregados = {}
            self.productos_transferencia = set()
            self.actualizar_lista_productos()
            self.lbl_monto_total.config(text="$0.00")
    
        except Exception as e:
            self.sqliteConnection.rollback()
            self.session.rollback()
            messagebox.showerror("Error", f"Error al procesar la venta:\n{str(e)}")
    
    def cancelar_venta(self):
        seleccionados = self.tree.selection()
        if not seleccionados:
            if messagebox.askyesno("Cancelar", "¿Desea cancelar la venta actual?"):
                self.productos_agregados = {}
                self.productos_transferencia = set()
                self.actualizar_lista_productos()
                self.entry_CodigodeBarras.focus()
        else:
            messagebox.showinfo("Cancelar", "¿Desea cancelar la venta actual?")
            # Eliminar solo los productos seleccionados
            for item in seleccionados:
                valores = self.tree.item(item, 'values')
                codigo = valores[0]
                if codigo in self.productos_agregados:
                    del self.productos_agregados[codigo]
                if codigo in self.productos_transferencia:
                    self.productos_transferencia.remove(codigo)
            # Actualizar la lista y el total
            self.actualizar_lista_productos()
            self.entry_CodigodeBarras.focus()


    # Nuevos métodos para manejar la funcionalidad de devolución
    def abrir_ventana_devolucion(self):
        """Abre la ventana para gestionar vales de devolución"""
        ventana_devolucion = Toplevel(self)
        ventana_devolucion.title("Vale de Devolución")
        ventana_devolucion.geometry("600x400")
        
        # Frame principal
        frame_principal = Frame(ventana_devolucion, padx=10, pady=10)
        frame_principal.pack(fill=BOTH, expand=True)
        
        # Código de barras
        Label(frame_principal, text="Código de Barras:", font=('Helvetica', 10)).pack(pady=5)
        self.entry_codigo_devolucion = Entry(frame_principal, font=('Helvetica', 12))
        self.entry_codigo_devolucion.pack(fill=X, pady=5)
        self.entry_codigo_devolucion.focus()
        self.entry_codigo_devolucion.bind('<Return>', lambda e: self.buscar_producto_devolucion())
        
        # Botón de búsqueda
        btn_buscar = Button(frame_principal, text="Buscar Producto", 
                          command=self.buscar_producto_devolucion,
                          bg='#4CAF50', fg='white')
        btn_buscar.pack(pady=10)
        
        # Frame para botones inferiores
        frame_botones = Frame(frame_principal)
        frame_botones.pack(side=BOTTOM, pady=10)
        
        # Botón Generar Vale
        btn_generar = Button(frame_botones, text="Generar Vale de Devolución",
                           command=self.generar_vale_devolucion,
                           bg='#2196F3', fg='white', state=DISABLED)
        btn_generar.pack(side=LEFT, padx=5)
        self.btn_generar_vale = btn_generar  # Guardar referencia
        
        # Botón Consultar Vale
        btn_consultar = Button(frame_botones, text="Consultar Vale de Devolución",
                              command=self.consultar_vale_devolucion,
                              bg='#9C27B0', fg='white')
        btn_consultar.pack(side=LEFT, padx=5)
        
        # Frame para mostrar datos del producto
        self.frame_datos_producto = Frame(frame_principal, bd=1, relief=SOLID, padx=10, pady=10)
        self.frame_datos_producto.pack(fill=BOTH, expand=True, pady=10)
        
        # Variables para almacenar datos del producto
        self.datos_producto_devolucion = None
    
    def buscar_producto_devolucion(self):
        """Busca un producto para devolución"""
        codigo = self.entry_codigo_devolucion.get().strip()
        if not codigo:
            messagebox.showwarning("Advertencia", "Ingrese un código de barras")
            return
        
        try:
            # Buscar producto en la base de datos
            session = Session()
            producto = session.query(RegistroProductos).filter_by(CodigodeBarras=codigo).first()
            
            if producto:
                # Limpiar frame de datos
                for widget in self.frame_datos_producto.winfo_children():
                    widget.destroy()
                
                # Mostrar datos del producto
                Label(self.frame_datos_producto, text="Datos del Producto:", 
                     font=('Helvetica', 10, 'bold')).pack(anchor=W)
                
                datos = [
                    f"Código: {producto.CodigodeBarras}",
                    f"Cliente: {producto.Cliente}",
                    f"Marca: {producto.Marca}",
                    f"Color: {producto.Color}",
                    f"Precio: ${producto.PrecioProducto:.2f}",
                    f"Fecha ingreso: {producto.Fechaingreso}",
                    f"Fecha vencimiento: {producto.Fechavencimiento}"
                ]
                
                for dato in datos:
                    Label(self.frame_datos_producto, text=dato, anchor=W).pack(fill=X)
                
                # Guardar datos para posible devolución
                self.datos_producto_devolucion = {
                    'CodigodeBarras': producto.CodigodeBarras,
                    'Cliente': producto.Cliente,
                    'Marca': producto.Marca,
                    'Color': producto.Color,
                    'PrecioProducto': producto.PrecioProducto,
                    'Id_productos': producto.Id_productos,
                    'Fechaingreso': producto.Fechaingreso,  # Añadir esto
                    'Fechavencimiento': producto.Fechavencimiento  # Añadir esto
                }
                
                # Habilitar botón de generar vale
                self.btn_generar_vale.config(state=NORMAL)
            else:
                messagebox.showinfo("Información", "Producto no encontrado")
                self.datos_producto_devolucion = None
                self.btn_generar_vale.config(state=DISABLED)
            
            session.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar el producto: {str(e)}")
    
    def generar_vale_devolucion(self):
        """Genera un vale de devolución para el producto seleccionado"""
        if not self.datos_producto_devolucion:
            messagebox.showwarning("Advertencia", "No hay datos de producto para generar el vale")
            return
    
        try:
            session = Session()
        
            # Verificar si ya existe un vale para este producto específico
            vale_existente = session.query(ValesDevolucion).filter(
            ValesDevolucion.CodigodeBarras == self.datos_producto_devolucion['CodigodeBarras'],
            ValesDevolucion.Id_productos == self.datos_producto_devolucion['Id_productos']
            ).first()
        
            # Obtener el último ID de vale para implementar el contador
            ultimo_vale = session.query(ValesDevolucion).order_by(ValesDevolucion.Id_vale.desc()).first()
            nuevo_id = 1 if not ultimo_vale else (ultimo_vale.Id_vale % 100) + 1
        
            # Calcular fechas
            fecha_emision = datetime.now().strftime("%d/%m/%Y")
            fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
        
            # Crear nuevo vale de devolución
            nuevo_vale = ValesDevolucion(
            Id_vale=nuevo_id,
            CodigodeBarras=self.datos_producto_devolucion['CodigodeBarras'],
            Cliente=self.datos_producto_devolucion['Cliente'],
            Marca=self.datos_producto_devolucion['Marca'],
            Color=self.datos_producto_devolucion['Color'],
            PrecioProducto=self.datos_producto_devolucion['PrecioProducto'],
            Fechaingreso=self.datos_producto_devolucion['Fechaingreso'],
            Fechavencimiento=self.datos_producto_devolucion['Fechavencimiento'],
            Id_productos=self.datos_producto_devolucion['Id_productos']
            )
        
            session.add(nuevo_vale)
            session.commit()
        
            # Generar el PDF del vale
            self.generar_pdf_vale_devolucion(nuevo_vale)
        
            messagebox.showinfo("Éxito", "Vale de devolución generado correctamente")

            # Cerrar la ventana de devolución después de generar el vale
            for widget in self.winfo_children():
                if isinstance(widget, Toplevel) and widget.title() == "Vale de Devolución":
                    widget.destroy()
                    break
        
        except Exception as e:
            session.rollback()
            messagebox.showerror("Error", f"No se pudo generar el vale: {str(e)}")
        finally:
            session.close()
    
    def generar_pdf_vale_devolucion(self, vale):
        """Genera el PDF del vale de devolución"""
        try:
            # Configuración para impresora térmica (80mm de ancho)
            width = 80 * mm
            height = 400 * mm
            custom_size = (width, height)
        
            pdf_path = os.path.join(self.Temp_dir, f"vale_devolucion_{vale.Id_vale}.pdf")
            c = canvas.Canvas(pdf_path, pagesize=custom_size)
        
            # Configuración de márgenes
            margin_left = 5 * mm
            margin_right = 5 * mm
            y_position = height - 10 * mm
        
            # Encabezado
            c.setFont("Helvetica-Bold", 13)
            c.drawCentredString(width/2, y_position, "MULTIMARCAS TURQUESA")
            y_position -= 6 * mm
            c.setFont("Helvetica", 12)
            c.drawCentredString(width/2, y_position, "VALE DE DEVOLUCIÓN")
            y_position -= 8 * mm
        
            # Línea divisoria
            c.line(margin_left, y_position, width - margin_right, y_position)
            y_position -= 10 * mm
        
            # Datos del vale
            c.setFont("Helvetica-Bold", 11)
            c.drawString(margin_left, y_position, f"N° Vale: {vale.Id_vale}")
            y_position -= 7 * mm
        
            # Datos del producto
            c.setFont("Helvetica", 12)
            datos = [
            f"Código: {vale.CodigodeBarras}",
            f"Cliente: {vale.Cliente}",
            f"Marca: {vale.Marca}",
            f"Color: {vale.Color}",
            f"Precio: ${vale.PrecioProducto:.2f}"
            ]
        
            for dato in datos:
                c.drawString(margin_left, y_position, dato)
                y_position -= 6 * mm
        
            # Fechas (solo en el ticket de devolución)
            fecha_emision = datetime.now().strftime("%d/%m/%Y")
            fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
        
            y_position -= 10 * mm
            c.drawString(margin_left, y_position, f"Fecha emisión: {fecha_emision}")
            y_position -= 6 * mm
            c.drawString(margin_left, y_position, f"Fecha vencimiento: {fecha_vencimiento}")
            y_position -= 10 * mm
        
            # Línea divisoria final
            c.line(margin_left, y_position, width - margin_right, y_position)
            y_position -= 10 * mm
        
            # Mensaje final
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(width/2, y_position, "VÁLIDO POR 30 DÍAS")
            y_position -= 7 * mm
            c.drawCentredString(width/2, y_position, "Gracias por su preferencia")
        
            c.save()
        
            # Mostrar vista previa
            self.mostrar_vista_previa_ticket(pdf_path)
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF: {str(e)}")
    
    def consultar_vale_devolucion(self):
        """Consulta vales de devolución existentes con búsqueda avanzada"""
        ventana_consulta = Toplevel(self)
        ventana_consulta.title("Consultar Vales de Devolución")
        ventana_consulta.geometry("800x600")

        # Cerrar la ventana de Vale de Devolución si está abierta
        for widget in self.winfo_children():
            if isinstance(widget, Toplevel) and widget.title() == "Vale de Devolución":
                widget.destroy()
                break
    
        # Frame de búsqueda
        frame_busqueda = Frame(ventana_consulta, padx=10, pady=10, bg='#f0f0f0')
        frame_busqueda.pack(fill=X)
    
        # Campos de búsqueda
        Label(frame_busqueda, text="Nombre del Cliente:", bg='#f0f0f0').grid(row=0, column=0, padx=5, pady=5, sticky=E)
        self.entry_buscar_cliente_vale = Entry(frame_busqueda, width=25)
        self.entry_buscar_cliente_vale.grid(row=0, column=1, padx=5, pady=5, sticky=W)
    
        Label(frame_busqueda, text="Marca:", bg='#f0f0f0').grid(row=1, column=0, padx=5, pady=5, sticky=E)
        self.entry_buscar_marca_vale = Entry(frame_busqueda, width=25)
        self.entry_buscar_marca_vale.grid(row=1, column=1, padx=5, pady=5, sticky=W)
    
        Label(frame_busqueda, text="Departamento:", bg='#f0f0f0').grid(row=2, column=0, padx=5, pady=5, sticky=E)
        self.entry_buscar_depto_vale = Entry(frame_busqueda, width=25)
        self.entry_buscar_depto_vale.grid(row=2, column=1, padx=5, pady=5, sticky=W)
    
        # Botón de búsqueda
        btn_buscar = Button(frame_busqueda, text="Buscar Vales", 
                    command=self.buscar_vales_devolucion,
                    bg='#4CAF50', fg='white')
        btn_buscar.grid(row=3, column=0, columnspan=2, pady=10)
    
        # Frame principal para resultados
        frame_principal = Frame(ventana_consulta, padx=10, pady=10)
        frame_principal.pack(fill=BOTH, expand=True)
    
        # Treeview para mostrar vales
        columns = ("ID", "Código", "Cliente", "Marca", "Departamento", "Fecha Emisión", "Fecha Vencimiento")
        self.tree_vales = ttk.Treeview(frame_principal, columns=columns, show='headings')
    
        # Configurar columnas
        for col in columns:
            self.tree_vales.heading(col, text=col)
            self.tree_vales.column(col, width=100, anchor=CENTER)
    
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_principal, orient=VERTICAL, command=self.tree_vales.yview)
        self.tree_vales.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree_vales.pack(fill=BOTH, expand=True)
    
        # Frame para botones
        frame_botones = Frame(frame_principal)
        frame_botones.pack(fill=X, pady=10)
    
        # Botón para ver ticket original
        btn_ver_ticket = Button(frame_botones, text="Ver Ticket Original", 
        command=self.ver_ticket_original,
        bg='#2196F3', fg='white')
        btn_ver_ticket.pack(side=LEFT, padx=5)
    

    def buscar_vales_devolucion(self):
        """Busca vales según los criterios ingresados"""
        cliente = self.entry_buscar_cliente_vale.get().strip()
        marca = self.entry_buscar_marca_vale.get().strip()
        departamento = self.entry_buscar_depto_vale.get().strip()
    
        # Limpiar treeview
        for item in self.tree_vales.get_children():
            self.tree_vales.delete(item)
    
        try:
            session = Session()
            query = session.query(ValesDevolucion)
        
            # Aplicar filtros según lo ingresado
            if cliente:
                query = query.filter(ValesDevolucion.Cliente.like(f"%{cliente}%"))
            if marca:
                query = query.filter(ValesDevolucion.Marca.like(f"%{marca}%"))
        
            # Para departamento necesitamos unir con la tabla de productos
            if departamento:
                query = query.join(RegistroProductos).filter(
                RegistroProductos.Departamento.like(f"%{departamento}%"))
        
            vales = query.all()
        
            for vale in vales:
                # Obtener el departamento del producto asociado
                producto = session.query(RegistroProductos).filter_by(Id_productos=vale.Id_productos).first()
                depto = producto.Departamento if producto else "N/A"
            
                self.tree_vales.insert("", END, values=(
                vale.Id_vale,
                vale.CodigodeBarras,
                vale.Cliente,
                vale.Marca,
                depto,
                vale.Fechaingreso,
                vale.Fechavencimiento
                ))
        
            if not vales:
                messagebox.showinfo("Información", "No se encontraron vales con esos criterios")
        
            session.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los vales: {str(e)}")

    def ver_ticket_original(self):
        seleccion = self.tree_vales.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un vale")
            return

        item = self.tree_vales.item(seleccion[0])
        Id_vale = item['values'][0]  # Obtener el ID del vale
        codigo_barras = item['values'][1]  # Código de barras completo

        try:
            # Buscar todos los archivos que coincidan con el patrón del código
            pattern = f"vale_devolucion_{Id_vale}.pdf"
            matching_files = [f for f in os.listdir(self.Temp_dir) if fnmatch.fnmatch(f, pattern)]
        
            if matching_files:
                # Tomar el más reciente si hay múltiples
                pdf_path = os.path.join(self.Temp_dir, sorted(matching_files)[-1])
                self.mostrar_vista_previa_ticket(pdf_path)
            else:
                messagebox.showinfo("Información", "No se encontró el ticket original guardado")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener el ticket: {str(e)}")


    def limpiar_lista(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def __del__(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'sqliteConnection') and self.sqliteConnection:
            self.sqliteConnection.close()
        if hasattr(self, 'session') and self.session:
            self.session.close()