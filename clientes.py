from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from tempfile import gettempdir
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import mm
import win32api
import win32print
from pdf2image import convert_from_path
from PIL import Image, ImageTk

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

class ApartadoProductos(Base):
    __tablename__ = 'apartado_productos'
    Id_apartado = Column(Integer, primary_key=True)
    CodigodeBarras = Column(String)
    Cliente = Column(String)
    Departamento = Column(String)
    Marca = Column(String)
    Color = Column(String)
    Talla = Column(String)
    PrecioProducto = Column(Float)
    Abono = Column(Float, default=0.0)
    Restante = Column(Float)
    Estatus = Column(String, default="Pendiente")
    Id_productos = Column(Integer, ForeignKey('registro_productos.Id_productos'))
    producto = relationship("RegistroProductos")

# Crear motor de base de datos
engine = create_engine('sqlite:///PuntoVenta.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class Clientes(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.temp_dir = r"C:\punto-venta-almacenamiento"  # Ruta específica para archivos temporales
        self.pdf_path= r"C:\Program Files\Adobe\Acrobat DC\Acrobat.exe"
        self.configure(bg='white')
        self.place(x=0, y=0, width=1100, height=650)
        
        # Variables de control
        self.busqueda_var = tk.StringVar()
        self.abono_var = tk.DoubleVar()
        self.producto_seleccionado = None
        self.producto_encontrado = None
        self.productos_apartados = []  # Lista para guardar productos seleccionados
    
        self.crear_widgets()
        # Eliminamos la llamada a actualizar_tabla() aquí para que no cargue todos los productos al inicio

    def generar_ticket_abono(self, apartado):
        """Genera un PDF con los detalles del abono realizado"""
        try:
            # Configuración para impresora térmica (80mm de ancho)
            width = 80 * mm  # 80mm en puntos (1mm = 2.83465 puntos)
            height = 400 * mm  # Altura suficiente
            custom_size = (width, height)
            
            # Crear archivo temporal
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, f"abono_apartado_{apartado.Id_apartado}.pdf")
            c = canvas.Canvas(pdf_path, pagesize=custom_size)
            
            # Configuración de márgenes
            margin_left = 10
            margin_right = 10
            y_position = height - 20
            
            # Encabezado
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(width/2, y_position, "MULTIMARCAS TURQUESA")
            y_position -= 15
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, y_position, "RECIBO DE ABONO - APARTADO")
            y_position -= 15
            c.drawCentredString(width/2, y_position, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            y_position -= 20
            
            # Línea divisoria
            c.line(margin_left, y_position, width - margin_right, y_position)
            y_position -= 20
            
            # Datos del producto
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin_left, y_position, "DETALLES DEL PRODUCTO:")
            y_position -= 15
            
            c.setFont("Helvetica", 9)
            detalles = [
                f"Código: {apartado.CodigodeBarras}",
                f"Cliente: {apartado.Cliente}",
                f"Departamento: {apartado.Departamento}",
                f"Marca: {apartado.Marca}",
                f"Precio Total: ${apartado.PrecioProducto:.2f}",
                f"Abono Realizado: ${apartado.Abono:.2f}",
                f"Saldo Pendiente: ${apartado.Restante:.2f}"
            ]
            
            for detalle in detalles:
                c.drawString(margin_left, y_position, detalle)
                y_position -= 12
            
            # Línea divisoria
            y_position -= 10
            c.line(margin_left, y_position, width - margin_right, y_position)
            y_position -= 15
            
            # Mensaje final
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(width/2, y_position, "¡GRACIAS POR SU PREFERENCIA!")
            y_position -= 12
            c.setFont("Helvetica", 8)
            c.drawCentredString(width/2, y_position, "Conserve este comprobante")
            
            c.save()
            
            # Mostrar vista previa
            self.mostrar_vista_previa_ticket(pdf_path)
            
            return pdf_path
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el ticket: {str(e)}")
            return None
        
    
    def generar_ticket_pagado(self, apartado):
        """Genera un PDF cuando un apartado se paga completamente"""
        try:
            # Configuración para impresora térmica (80mm de ancho)
            width = 80 * mm  # 80mm en puntos
            height = 400 * mm  # Altura suficiente
            custom_size = (width, height)
            
            # Crear archivo temporal
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, f"apartado_pagado_{apartado.Id_apartado}.pdf")
            c = canvas.Canvas(pdf_path, pagesize=custom_size)
            
            # Configuración de márgenes
            margin_left = 10
            margin_right = 10
            y_position = height - 20
            
            # Encabezado
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(width/2, y_position, "MULTIMARCAS TURQUESA")
            y_position -= 15
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, y_position, "APARTADO LIQUIDADO")
            y_position -= 15
            c.drawCentredString(width/2, y_position, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            y_position -= 20
            
            # Línea divisoria
            c.line(margin_left, y_position, width - margin_right, y_position)
            y_position -= 20
            
            # Datos del producto
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin_left, y_position, "DETALLES DEL PRODUCTO:")
            y_position -= 15
            
            c.setFont("Helvetica", 9)
            detalles = [
                f"Código: {apartado.CodigodeBarras}",
                f"Cliente: {apartado.Cliente}",
                f"Departamento: {apartado.Departamento}",
                f"Marca: {apartado.Marca}",
                f"Precio Total: ${apartado.PrecioProducto:.2f}",
                f"Total Abonado: ${apartado.Abono:.2f}",
                f"Estatus: {apartado.Estatus}"
            ]
            
            for detalle in detalles:
                c.drawString(margin_left, y_position, detalle)
                y_position -= 12
            
            # Línea divisoria
            y_position -= 10
            c.line(margin_left, y_position, width - margin_right, y_position)
            y_position -= 15
            
            # Mensaje final
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(width/2, y_position, "¡PAGO COMPLETADO!")
            y_position -= 12
            c.setFont("Helvetica", 8)
            c.drawCentredString(width/2, y_position, "Gracias por su compra")
            
            c.save()
            
            # Mostrar vista previa
            self.mostrar_vista_previa_ticket(pdf_path)
            
            return pdf_path
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el ticket: {str(e)}")
            return None
        

    def mostrar_vista_previa_ticket(self, pdf_path):
        """Muestra una ventana con la vista previa del ticket usando pdf2image"""
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "No se pudo generar el ticket para vista previa")
            return

        # Crear ventana de vista previa
        preview_window = Toplevel(self)
        preview_window.title("Vista Previa del Ticket")
        preview_window.geometry("400x600")

        # Frame principal
        main_frame = Frame(preview_window)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Canvas para mostrar la imagen
        canvas = Canvas(main_frame)
        canvas.pack(fill=BOTH, expand=True)

        try:
            # Convertir PDF a imagen (primera página)
            images = convert_from_path(pdf_path, dpi=200)
            if images:
                # Guardar la imagen temporalmente
                temp_img_path = os.path.join(tempfile.gettempdir(), "ticket_preview.png")
                images[0].save(temp_img_path, 'PNG')
            
                # Cargar la imagen y mostrarla en el canvas
                img = Image.open(temp_img_path)
                img = img.resize((380, int(380 * img.height / img.width)), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
            
                # Mostrar la imagen en el canvas
                canvas.create_image(0, 0, anchor=NW, image=img_tk)
                canvas.image = img_tk  # Mantener referencia
            
                # Configurar el scroll del canvas
                canvas.config(scrollregion=canvas.bbox("all"))
            
                # Eliminar la imagen temporal
                try:
                    os.remove(temp_img_path)
                except:
                    pass
            else:
                Label(main_frame, 
                    text="No se pudo generar la vista previa del ticket",
                    font=('Helvetica', 12)).pack(pady=50)
        
        except Exception as e:
            Label(main_frame, 
                text=f"Error al generar vista previa: {str(e)}",
                font=('Helvetica', 12)).pack(pady=50)

        # Frame para botones
        btn_frame = Frame(main_frame)
        btn_frame.pack(pady=10)

        # Botón para imprimir directamente
        Button(btn_frame, text="Imprimir Ticket", 
            command=lambda: self.imprimir_ticket(pdf_path, preview_window),
            bg="#4CAF50", fg="white", font=('Helvetica', 10, 'bold')).pack(side=LEFT, padx=5)

        # Botón para cerrar
        Button(btn_frame, text="Cerrar", 
            command=preview_window.destroy,
            bg="#f44336", fg="white", font=('Helvetica', 10, 'bold')).pack(side=LEFT, padx=5)
    
    def imprimir_ticket(self, pdf_path, window=None):
        """Imprime el ticket directamente"""
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
            if window:
                window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo imprimir el ticket: {str(e)}")


    def crear_widgets(self):
        # Frame de búsqueda mejorado con estilo moderno
        frame_busqueda = tk.Frame(self, bg='#2c3e50', padx=15, pady=10)
        frame_busqueda.pack(fill=tk.X)
    
        # Título de búsqueda
        tk.Label(frame_busqueda, text="BUSCAR PRODUCTOS", bg='#2c3e50', fg='white', 
            font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT, padx=(0, 20))
    
        # Frame para opciones de búsqueda
        frame_opciones = tk.Frame(frame_busqueda, bg='#2c3e50')
        frame_opciones.pack(side=tk.LEFT, padx=5)
    
        # Opciones de búsqueda con estilo moderno
        self.opcion_busqueda = tk.StringVar(value="codigo")
    
        estilo_radio = {'bg': '#2c3e50', 'fg': 'white', 'selectcolor': '#2c3e50', 
                'activebackground': '#2c3e50', 'font': ('Helvetica', 10)}
    
        tk.Radiobutton(frame_opciones, text="Código Barras", variable=self.opcion_busqueda, 
                  value="codigo", **estilo_radio).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(frame_opciones, text="Cliente", variable=self.opcion_busqueda, 
                  value="cliente", **estilo_radio).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(frame_opciones, text="Marca", variable=self.opcion_busqueda, 
                  value="marca", **estilo_radio).pack(side=tk.LEFT, padx=5)
    
        # Frame para campo de búsqueda
        frame_campo_busqueda = tk.Frame(frame_busqueda, bg='#2c3e50')
        frame_campo_busqueda.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
    
        # Campo de búsqueda con estilo moderno (sin botón)
        self.entry_busqueda = tk.Entry(frame_campo_busqueda, textvariable=self.busqueda_var, 
                                font=('Helvetica', 11), bd=2, relief=tk.FLAT)
        self.entry_busqueda.pack(fill=tk.X, expand=True, ipady=3)
    
        # Configurar solo el evento Enter para búsqueda
        self.entry_busqueda.bind('<Return>', self.buscar_producto)
        
        # Frame de tabla
        frame_tabla = tk.Frame(self)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Tabla de productos
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
        
        self.tabla = ttk.Treeview(frame_tabla, columns=('ID', 'Código', 'Cliente', 'Departamento', 'Marca', 'Precio', 'Abono', 'Restante', 'Estatus'), show='headings')
        
        # Configurar columnas
        columnas = [
            ('ID', 50),
            ('Código', 100),
            ('Cliente', 150),
            ('Departamento', 120),
            ('Marca', 120),
            ('Precio', 80),
            ('Abono', 80),
            ('Restante', 80),
            ('Estatus', 100)
        ]
        
        for col, width in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=width, anchor=tk.CENTER)
        
        # Configurar tags para colorear filas
        self.tabla.tag_configure('pagado', background='#d4edda')  # Verde claro para productos pagados
        self.tabla.tag_configure('pendiente', background='#fff3cd')  # Amarillo claro para productos pendientes
        
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=self.tabla.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        # Frame de botones
        frame_botones = tk.Frame(self, bg='#f0f0f0', padx=10, pady=10)
        frame_botones.pack(fill=tk.X)
        
        # Botón para apartar producto
        btn_apartar = tk.Button(frame_botones, text="Apartar Producto", command=self.mostrar_ventana_apartar,
                              bg='#4CAF50', fg='white', font=('Helvetica', 10, 'bold'))
        btn_apartar.pack(side=tk.LEFT, padx=5)
        
        # Botón para quitar producto
        btn_quitar = tk.Button(frame_botones, text="Quitar Producto", command=self.quitar_producto,
                              bg='#f44336', fg='white', font=('Helvetica', 10, 'bold'))
        btn_quitar.pack(side=tk.LEFT, padx=5)
        
        # Frame de detalles del producto
        frame_detalles = tk.Frame(self, bg='#e9f5ff', padx=10, pady=10, bd=1, relief=tk.SOLID)
        frame_detalles.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Detalles del producto
        self.label_detalles = tk.Label(frame_detalles, text="Seleccione un producto para ver detalles", 
                                     justify=tk.LEFT, bg='#e9f5ff', font=('Helvetica', 10))
        self.label_detalles.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        
        
        # Frame de abono mejorado
        frame_abono = tk.Frame(self, bg='#f8f9fa', padx=10, pady=10, bd=1, relief=tk.SOLID)
        frame_abono.pack(fill=tk.X, padx=10)
    
        tk.Label(frame_abono, text="ABONO", bg='#f8f9fa', font=('Helvetica', 11, 'bold')).pack(anchor=tk.W)
    
        frame_abono_datos = tk.Frame(frame_abono, bg='#f8f9fa')
        frame_abono_datos.pack(fill=tk.X, pady=5)
    
        tk.Label(frame_abono_datos, text="Cantidad a abonar ($):", bg='#f8f9fa',  font=('Helvetica', 12)).pack(side=tk.LEFT)
    
        # Variable para el campo de abono
        self.abono_text = tk.StringVar(value="$")
        self.entry_abono = tk.Entry(frame_abono_datos, textvariable=self.abono_text, width=15, 
                            font=('Helvetica', 15), bd=3, relief=tk.SOLID)
        self.entry_abono.pack(side=tk.LEFT, padx=5)
    
        # Configuramos eventos para el campo de abono
        self.entry_abono.bind('<FocusIn>', self._on_focus_in_abono)
        self.entry_abono.bind('<Key>', self._validar_tecla_abono)
        self.entry_abono.bind('<KeyRelease>', self._formatear_abono_en_tiempo_real)
    
        self.btn_abonar = tk.Button(frame_abono_datos, text="Realizar Abono", command=self.realizar_abono,
                            bg='#007bff', fg='white', font=('Helvetica', 10, 'bold'))
        self.btn_abonar.pack(side=tk.LEFT)

        
        # Configurar selección de tabla
        self.tabla.bind('<<TreeviewSelect>>', self.seleccionar_producto)

    def mostrar_ventana_apartar(self):
        """Muestra ventana para buscar producto por código de barras"""
        top = tk.Toplevel(self)
        top.title("Apartar Producto")
        top.geometry("500x350")
        top.configure(bg='white')
        top.resizable(False, False)
        
        # Frame principal
        main_frame = tk.Frame(top, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para código de barras
        frame_codigo = tk.Frame(main_frame, bg='white')
        frame_codigo.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(frame_codigo, text="Código de Barras:", bg='white').pack(side=tk.LEFT)
        self.codigo_var = tk.StringVar()
        entry_codigo = tk.Entry(frame_codigo, textvariable=self.codigo_var, width=30, bd=2, relief=tk.SOLID)
        entry_codigo.pack(side=tk.LEFT, padx=5)
        entry_codigo.focus_set()
        entry_codigo.bind('<Return>', lambda e: self.buscar_por_codigo(top))
        
        btn_buscar = tk.Button(frame_codigo, text="Buscar", command=lambda: self.buscar_por_codigo(top),
                              bg='#007bff', fg='white')
        btn_buscar.pack(side=tk.LEFT, padx=5)
        
        # Frame para mostrar resultados
        frame_resultados = tk.Frame(main_frame, bg='white')
        frame_resultados.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Etiquetas para mostrar la información del producto
        self.labels_info = {
            'Código': tk.Label(frame_resultados, text="", anchor='w', bg='white'),
            'Cliente': tk.Label(frame_resultados, text="", anchor='w', bg='white'),
            'Departamento': tk.Label(frame_resultados, text="", anchor='w', bg='white'),
            'Marca': tk.Label(frame_resultados, text="", anchor='w', bg='white'),
            'Color': tk.Label(frame_resultados, text="", anchor='w', bg='white'),
            'Precio': tk.Label(frame_resultados, text="", anchor='w', bg='white')
        }
        
        for i, (key, label) in enumerate(self.labels_info.items()):
            tk.Label(frame_resultados, text=f"{key}:", bg='white').grid(row=i, column=0, sticky='e', padx=5, pady=2)
            label.grid(row=i, column=1, sticky='w', padx=5, pady=2)
        
        # Frame para nombre del cliente (editable si no tiene)
        self.frame_cliente = tk.Frame(main_frame, bg='white')
        self.frame_cliente.pack(fill=tk.X, pady=(5, 15))
        
        tk.Label(self.frame_cliente, text="Nombre del Cliente:", bg='white').pack(side=tk.LEFT)
        self.cliente_var = tk.StringVar()
        self.entry_cliente = tk.Entry(self.frame_cliente, textvariable=self.cliente_var, width=30, bd=2, relief=tk.SOLID)
        self.entry_cliente.pack(side=tk.LEFT, padx=5)
        
        # Botón para apartar
        btn_apartar = tk.Button(main_frame, text="APARTAR PRODUCTO", 
                               command=lambda: self.apartar_producto_seleccionado(top),
                               state=tk.DISABLED, bg='#28a745', fg='white', font=('Helvetica', 10, 'bold'))
        btn_apartar.pack(fill=tk.X, pady=(10, 0))
        self.btn_apartar_actual = btn_apartar

    def buscar_por_codigo(self, ventana):
        """Busca un producto por su código de barras"""
        codigo = self.codigo_var.get().strip()
        if not codigo:
            messagebox.showwarning("Advertencia", "Ingrese un código de barras")
            return
        
        session = Session()
        producto = session.query(RegistroProductos).filter_by(CodigodeBarras=codigo).first()
        
        if producto:
            self.producto_encontrado = producto
            # Mostrar información del producto
            self.labels_info['Código'].config(text=producto.CodigodeBarras)
            
            # Mostrar cliente si existe, sino permitir edición
            if producto.Cliente:
                self.labels_info['Cliente'].config(text=producto.Cliente)
                self.cliente_var.set(producto.Cliente)
                self.entry_cliente.config(state='disabled')
            else:
                self.labels_info['Cliente'].config(text="(Sin asignar)")
                self.cliente_var.set("")
                self.entry_cliente.config(state='normal')
            
            self.labels_info['Departamento'].config(text=producto.Departamento)
            self.labels_info['Marca'].config(text=producto.Marca)
            self.labels_info['Color'].config(text=producto.Color)
            self.labels_info['Precio'].config(text=f"${producto.PrecioProducto:.2f}")
            
            self.btn_apartar_actual.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Error", "Producto no encontrado")
            self.limpiar_campos_info()
            self.btn_apartar_actual.config(state=tk.DISABLED)
        
        session.close()

    def limpiar_campos_info(self):
        """Limpia los campos de información del producto"""
        for label in self.labels_info.values():
            label.config(text="")
        self.cliente_var.set("")
        self.entry_cliente.config(state='normal')
        self.producto_encontrado = None

    def apartar_producto_seleccionado(self, ventana):
        """Agrega el producto encontrado a los apartados"""
        if not self.producto_encontrado:
            return
        
        # Obtener nombre del cliente (del campo editable si no tenía)
        cliente = self.producto_encontrado.Cliente if self.producto_encontrado.Cliente else self.cliente_var.get().strip()
        if not cliente:
            messagebox.showwarning("Advertencia", "Ingrese el nombre del cliente")
            return
        
        session = Session()
        try:
            # Verificar si el producto ya está apartado
            existente = session.query(ApartadoProductos).filter_by(
                CodigodeBarras=self.producto_encontrado.CodigodeBarras,
                Estatus="Pendiente"
            ).first()
            
            if existente:
                messagebox.showwarning("Advertencia", "Este producto ya está apartado")
                return
            
            nuevo_apartado = ApartadoProductos(
                CodigodeBarras=self.producto_encontrado.CodigodeBarras,
                Cliente=cliente,
                Departamento=self.producto_encontrado.Departamento,
                Marca=self.producto_encontrado.Marca,
                Color=self.producto_encontrado.Color,
                PrecioProducto=float(self.producto_encontrado.PrecioProducto),
                Restante=float(self.producto_encontrado.PrecioProducto),
                Id_productos=self.producto_encontrado.Id_productos,
                producto=self.producto_encontrado
            )
            
            session.add(nuevo_apartado)
            session.commit()
            messagebox.showinfo("Éxito", "Producto apartado correctamente")
            ventana.destroy()
            self.actualizar_tabla()
            
        except Exception as e:
            session.rollback()
            messagebox.showerror("Error", f"No se pudo apartar el producto: {str(e)}")
        finally:
            session.close()

    def quitar_producto(self):
        """Quita el producto seleccionado visualmente pero permite volver a agregarlo mediante búsqueda"""
        if not self.producto_seleccionado:
            messagebox.showwarning("Advertencia", "Por favor seleccione un producto primero")
            return

        respuesta = messagebox.askyesno("Confirmar", "¿Está seguro de quitar este producto de la vista?")
        if not respuesta:
            return

        try:
            # Solo eliminamos el producto de la tabla (interfaz)
            seleccion = self.tabla.selection()
            if seleccion:
                # Guardamos el ID del producto que estamos quitando
                id_quitado = self.tabla.item(seleccion[0])['values'][0]
            
                # Eliminamos de la tabla
                self.tabla.delete(seleccion[0])
            
                # Eliminamos de la lista de productos apartados
                self.productos_apartados = [p for p in self.productos_apartados if p.Id_apartado != id_quitado]
            
                self.producto_seleccionado = None
                self.label_detalles.config(text="Seleccione un producto para apartar o abonar")
                messagebox.showinfo("Éxito", "Producto quitado de la vista correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo quitar el producto: {str(e)}")

    def actualizar_tabla(self):
        """Actualiza la tabla con los productos apartados seleccionados"""
        # Limpiar tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)
    
        # Agregar solo los productos que han sido seleccionados mediante búsqueda
        for producto in self.productos_apartados:
            tags = ('pagado',) if producto.Estatus == "Pagado" else ('pendiente',)
            self.tabla.insert('', tk.END, values=(
            producto.Id_apartado,
            producto.CodigodeBarras,
            producto.Cliente,
            producto.Departamento,
            producto.Marca,
            f"${float(producto.PrecioProducto):.2f}",
            f"${float(producto.Abono):.2f}",
            f"${float(producto.Restante):.2f}",
            producto.Estatus
            ), tags=tags)

    def buscar_producto(self, event=None):
        """Busca productos en ApartadoProductos según el criterio seleccionado y muestra ventana de selección"""
        # Solo realizar la búsqueda si es un evento de botón o Enter
        if event is None or isinstance(event, str) or event.keysym == 'Return':
            termino = self.busqueda_var.get().strip()
            opcion = self.opcion_busqueda.get()
    
            # Si no hay término de búsqueda, no hacer nada
            if not termino:
                return

            session = Session()
            query = session.query(ApartadoProductos)

            if opcion == "codigo":
                query = query.filter(ApartadoProductos.CodigodeBarras == termino)
            elif opcion == "cliente":
                # Cambio aquí: usar contains para búsqueda parcial en lugar de igualdad exacta
                query = query.filter(ApartadoProductos.Cliente.contains(termino))
            elif opcion == "marca":
                query = query.filter(ApartadoProductos.Marca == termino)

            productos = query.all()
            session.close()

            if not productos:
                messagebox.showinfo("Información", "No se encontraron productos con ese criterio")
                return
        
            # Mostrar ventana de selección
            self.mostrar_ventana_seleccion(productos)


    def mostrar_ventana_seleccion(self, productos):
        """Muestra ventana con los productos encontrados para seleccionar uno"""
        top = tk.Toplevel(self)
        top.title("Seleccionar Producto")
        top.geometry("800x500")
        top.configure(bg='white')
        top.resizable(False, False)
    
        # Frame principal
        main_frame = tk.Frame(top, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
    
        # Título
        tk.Label(main_frame, text="PRODUCTOS ENCONTRADOS", bg='white', 
            font=('Helvetica', 12, 'bold')).pack(pady=(0, 15))
    
        # Frame para tabla de productos
        frame_tabla = tk.Frame(main_frame, bg='white')
        frame_tabla.pack(fill=tk.BOTH, expand=True)
    
        # Tabla de productos encontrados
        columns = ('ID', 'Código', 'Cliente', 'Departamento', 'Marca', 'Precio', 'Abono', 'Restante', 'Estatus')
        tree = ttk.Treeview(frame_tabla, columns=columns, show='headings', height=8)
    
        # Configurar columnas
        column_widths = [
        ('ID', 50),
        ('Código', 100),
        ('Cliente', 150),
        ('Departamento', 120),
        ('Marca', 120),
        ('Precio', 80),
        ('Abono', 80),
        ('Restante', 80),
        ('Estatus', 100)
        ]
    
        for col, width in column_widths:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor=tk.CENTER)
    
        # Agregar productos a la tabla
        for producto in productos:
            tree.insert('', tk.END, values=(
            producto.Id_apartado,
            producto.CodigodeBarras,
            producto.Cliente,
            producto.Departamento,
            producto.Marca,
            f"${float(producto.PrecioProducto):.2f}",
            f"${float(producto.Abono):.2f}",
            f"${float(producto.Restante):.2f}",
            producto.Estatus
            ))
    
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
    
        # Frame para botones
        frame_botones = tk.Frame(main_frame, bg='white', pady=15)
        frame_botones.pack(fill=tk.X)
    
        # Botón para seleccionar
        btn_seleccionar = tk.Button(frame_botones, text="SELECCIONAR", 
                            command=lambda: self.agregar_producto_apartado(tree, top),
                            bg='#4CAF50', fg='white', font=('Helvetica', 10, 'bold'))
        btn_seleccionar.pack(side=tk.LEFT, padx=5)
    
        # Botón para cancelar
        btn_cancelar = tk.Button(frame_botones, text="CANCELAR", 
                        command=top.destroy,
                        bg='#f44336', fg='white', font=('Helvetica', 10, 'bold'))
        btn_cancelar.pack(side=tk.RIGHT, padx=5)

    def agregar_producto_apartado(self, tree, ventana):
        """Agrega el producto seleccionado al apartado principal"""
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un producto primero")
            return

        item = tree.item(seleccion[0])
        id_apartado = item['values'][0]

        session = Session()
        try:
            # Buscar el producto en apartado_productos
            producto = session.query(ApartadoProductos).filter_by(Id_apartado=id_apartado).first()
    
            if not producto:
                messagebox.showerror("Error", "Producto no encontrado")
                return
    
            # Verificar si ya está en la tabla principal
            existente = any(p.Id_apartado == producto.Id_apartado for p in self.productos_apartados)
    
            if existente:
                messagebox.showwarning("Advertencia", "Este producto ya está en el apartado principal")
                return
    
            # Agregar a la lista de productos apartados
            self.productos_apartados.append(producto)
        
            # Actualizar la tabla
            self.actualizar_tabla()

            #Limpia la barra de busqueda
            self.busqueda_var.set("")
        
            messagebox.showinfo("Éxito", "Producto agregado al apartado principal")
            ventana.destroy()
    
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar el producto: {str(e)}")
        finally:
            session.close()

    def seleccionar_producto(self, event):
        """Muestra los detalles del producto seleccionado"""
        seleccion = self.tabla.selection()
        if seleccion:
            item = self.tabla.item(seleccion[0])
            id_apartado = item['values'][0]
            
            session = Session()
            self.producto_seleccionado = session.query(ApartadoProductos).filter_by(Id_apartado=id_apartado).first()
            session.close()
            
            if self.producto_seleccionado:
                detalles = (
                    f"Producto: {self.producto_seleccionado.Marca} - {self.producto_seleccionado.Color}\n"
                    f"Cliente: {self.producto_seleccionado.Cliente}\n"
                    f"Precio: ${float(self.producto_seleccionado.PrecioProducto):.2f} | "
                    f"Abonado: ${float(self.producto_seleccionado.Abono):.2f} | "
                    f"Restante: ${float(self.producto_seleccionado.Restante):.2f}"
                )
                self.label_detalles.config(text=detalles)
                
                # Habilitar/deshabilitar abono según estatus
                if self.producto_seleccionado.Estatus == "Pagado":
                    self.entry_abono.config(state='disabled')
                    self.btn_abonar.config(state='disabled')
                else:
                    self.entry_abono.config(state='normal')
                    self.btn_abonar.config(state='normal')

    def _on_focus_in_abono(self, event):
        """Cuando el campo de abono recibe foco, selecciona todo el texto"""
        self.entry_abono.select_range(0, tk.END)

    def _validar_tecla_abono(self, event):
        """Valida las teclas permitidas para el campo de abono"""
        # Permitir teclas de control (borrar, retroceso, etc.)
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End'):
            return
    
        # Permitir solo dígitos y un punto decimal
        if not event.char.isdigit() and event.char != '.':
            return "break"

    
    def _formatear_abono_en_tiempo_real(self, event):
        """Formatea el valor del abono en tiempo real con $ y separadores de miles"""
        # Obtener la posición actual del cursor
        cursor_pos = self.entry_abono.index(tk.INSERT)
    
        # Obtener el texto actual (sin formato)
        current = self.abono_text.get().replace("$", "").replace(",", "")
    
        # Si está vacío, establecer a 0
        if not current:
            current = "0"
    
        try:
            # Convertir a float y luego formatear
            value = float(current)
        
            # Formatear el valor con $ y separadores de miles
            if value == 0:
                formatted = "$0.00"
            else:
                # Manejar el caso cuando el usuario está escribiendo centavos
                if "." in current:
                    parts = current.split(".")
                    if len(parts) > 1 and len(parts[1]) > 2:
                        parts[1] = parts[1][:2]
                    current = ".".join(parts)
                    value = float(current)
            
                formatted = "${:,.2f}".format(value)
        
            self.abono_text.set(formatted)
        
            # Restaurar la posición del cursor (ajustada por los nuevos caracteres)
            if event.keysym not in ('BackSpace', 'Delete'):
                new_cursor_pos = cursor_pos + (len(formatted) - len(current))
                self.entry_abono.icursor(new_cursor_pos)
        except ValueError:
            # Si hay un error, dejar el valor anterior
            pass


    def _on_focus_out_abono(self, event):
        """Cuando el campo de abono pierde foco, aplica formato"""
        current = self.abono_text.get()
        if not current:
            self.abono_text.set("0.0")
        else:
            try:
                # Formatear el número con separadores de miles
                value = float(current)
                formatted = "${:,.2f}".format(value)
                self.abono_text.set(formatted)
            except ValueError:
                self.abono_text.set("0.0")

    def _validar_abono(self, event):
        """Valida que solo se ingresen números y un punto decimal"""
        current = self.abono_text.get()
        if not current:
            return
    
        # Permitir solo números y un punto decimal
        new_value = []
        has_decimal = False
        for char in current:
            if char.isdigit():
                new_value.append(char)
            elif char == '.' and not has_decimal:
                new_value.append(char)
                has_decimal = True
    
        self.abono_text.set(''.join(new_value))

        
    # Modificar el método realizar_abono para generar el ticket
    def realizar_abono(self):
        """Registra un abono para el producto seleccionado"""
        if not self.producto_seleccionado:
            messagebox.showwarning("Advertencia", "Por favor seleccione un producto primero")
            return
    
        try:
            # Obtener el valor formateado (remover $ y comas)
            abono_str = self.abono_text.get().replace("$", "").replace(",", "")
            abono = float(abono_str)
        
            if abono <= 0:
                messagebox.showwarning("Advertencia", "El abono debe ser mayor a cero")
                return
        except ValueError:
            messagebox.showerror("Error", "Ingrese una cantidad válida")
            return
    
        session = Session()
        try:
            producto = session.query(ApartadoProductos).filter_by(Id_apartado=self.producto_seleccionado.Id_apartado).first()
    
            if producto:
                # Calcular nuevo abono y restante
                nuevo_abono = float(producto.Abono) + abono
                nuevo_restante = float(producto.PrecioProducto) - nuevo_abono
        
                if nuevo_restante < 0:
                    messagebox.showwarning("Advertencia", "El abono excede el monto restante")
                    session.close()
                    return
        
                # Actualizar producto
                producto.Abono = nuevo_abono
                producto.Restante = nuevo_restante
        
                # Verificar si ya se pagó completo
                if nuevo_restante <= 0:
                    producto.Estatus = "Pagado"
                    # Generar ticket de pago completo
                    self.generar_ticket_pagado(producto)
                    messagebox.showinfo("Éxito", "¡Producto pagado en su totalidad!")
                else:
                    # Generar ticket de abono
                    self.generar_ticket_abono(producto)
        
                session.commit()

                # Actualizar el producto en la lista local
                for i, p in enumerate(self.productos_apartados):
                    if p.Id_apartado == producto.Id_apartado:
                        self.productos_apartados[i] = producto
                        break
        
                # Actualizar interfaz
                self.actualizar_tabla()
                self.abono_text.set("$0.00")
                self.seleccionar_producto(None)
        
                messagebox.showinfo("Éxito", "Abono registrado correctamente")
            else:
                messagebox.showerror("Error", "No se encontró el producto seleccionado")
        except Exception as e:
            session.rollback()
            messagebox.showerror("Error", f"Ocurrió un error al registrar el abono: {str(e)}")
        finally:
            session.close()