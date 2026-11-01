from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
import os
import tempfile
from pdf2image import convert_from_path
from PIL import Image, ImageTk
import win32api
import win32print
from agregar_productos import Agregar_Productos



# Configuración de SQLAlchemy
Base = declarative_base()

class RegistroProducto(Base):
    __tablename__ = 'registro_productos'
    Id_productos = Column(Integer, primary_key=True)
    CodigodeBarras = Column(String)
    Cliente = Column(String)
    Stock = Column(Integer)
    PrecioProducto = Column(Float)
    inventario = relationship("InventarioModel", back_populates="producto")

class InventarioModel(Base):
    __tablename__ = 'Inventario'
    Id_inventario = Column(Integer, primary_key=True)
    CodigodeBarras = Column(String)
    Cliente = Column(String)
    Stock = Column(Integer)
    PrecioProducto = Column(Float)
    Id_productos = Column(Integer, ForeignKey('registro_productos.Id_productos'))
    producto = relationship("RegistroProducto", back_populates="inventario")

class TransferenciaDiferencia(Base):
    __tablename__ = 'transferencias_diferencias'
    Id_transferencias = Column(Integer, primary_key=True)
    CodigodeBarras = Column(String)
    Cliente = Column(String)
    Monto = Column(Float)

# Crear motor de base de datos y tablas
engine = create_engine('sqlite:///PuntoVenta.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class Inventario(tk.Frame):
    def __init__(self, padre, usuario_actual=None):
        super().__init__(padre)
        self.usuario_actual = usuario_actual  # Guardar el nombre de usuario
        self.session = Session()
        self._construir_interfaz()

    def _construir_interfaz(self):
        """Construye la interfaz gráfica para el corte de caja"""
        # Configuración inicial del frame
        self.config(bg='#f0f2f5', bd=0, highlightthickness=0)
        
        # --- Contenedor principal ---
        main_container = Frame(self, bg='#ffffff', bd=0, highlightthickness=0,
                             relief='ridge', padx=0, pady=0)
        main_container.pack(padx=20, pady=20, fill='both', expand=True)
        
        # --- Separador decorativo ---
        separator = Frame(main_container, height=3, bg='#0984e3')
        separator.pack(fill='x', padx=80, pady=5)

        # --- Tarjeta de información ---
        frame_info = Frame(main_container, bg='#f8f9fa', bd=0, highlightthickness=1,
                         highlightbackground='#dfe6e9', relief='groove', padx=25, pady=20)
        frame_info.pack(fill='x', padx=40, pady=15, ipady=10)

        # --- Estilos para etiquetas ---
        label_style = {'font': ('Poppins', 14), 'bg': '#f8f9fa', 'fg': '#000000'}
        value_style = {'font': ('Poppins', 12, 'bold'), 'bg': '#f8f9fa'}

        # Fecha y hora
        lbl_fecha = Label(frame_info, text="📅 Fecha del corte:", **label_style)
        lbl_fecha.grid(row=0, column=0, sticky='w', pady=20)
        self.lbl_fecha_valor = Label(frame_info, text="--/--/----", **value_style, fg='#000000')
        self.lbl_fecha_valor.grid(row=0, column=1, sticky='w', padx=20)
        # Emoji con estilo especial
        lbl_emoji = Label(frame_info, 
                text="📅",
                font=('Segoe UI Emoji', 14),  # Fuente específica para emojis
                bg='#f8f9fa',
                fg='#000000')
        lbl_emoji.grid(row=0, column=0, sticky='w', padx=(0, 5))

        # Total de productos
        lbl_total_productos = Label(frame_info, text="📦 Productos vendidos:", **label_style)
        lbl_total_productos.grid(row=1, column=0, sticky='w', pady=10)
        self.lbl_total_productos_valor = Label(frame_info, text="0", **value_style, fg='#0f8341')
        self.lbl_total_productos_valor.grid(row=1, column=1, sticky='w', padx=20)
        # Emoji con estilo especial
        lbl_emoji = Label(frame_info, 
                text="📦",
                font=('Segoe UI Emoji', 15),  # Fuente específica para emojis
                bg='#f8f9fa',
                fg='#000000')
        lbl_emoji.grid(row=1, column=0, sticky='w', padx=(0, 5))


        # Monto total
        lbl_monto_total = Label(frame_info, text="💰 Ventas totales:", **label_style)
        lbl_monto_total.grid(row=2, column=0, sticky='w', pady=10)
        self.lbl_monto_total_valor = Label(frame_info, text="$0.00", **value_style, fg='#e61919')
        self.lbl_monto_total_valor.grid(row=2, column=1, sticky='w', padx=20)
        # Emoji con estilo especial
        lbl_emoji = Label(frame_info, 
                text="💰",
                font=('Segoe UI Emoji', 15),  # Fuente específica para emojis
                bg='#f8f9fa',
                fg='#000000')
        lbl_emoji.grid(row=2, column=0, sticky='w', padx=(0, 5))

        # --- Botón principal ---
        btn_style = {
            'bg': '#0984e3', 'fg': 'white', 'font': ('Poppins', 13, 'bold'),
            'padx': 30, 'pady': 12, 'bd': 0, 'cursor': 'hand2',
            'activebackground': '#0767b3', 'activeforeground': 'white',
            'relief': 'flat', 'highlightthickness': 0
        }
        btn_generar = Button(main_container, text="🔄 GENERAR CORTE", 
                           command=self._generar_corte, **btn_style)
        btn_generar.pack(pady=(10, 25), ipadx=20)
        
        # Efectos hover
        btn_generar.bind("<Enter>", lambda e: btn_generar.config(bg='#0767b3'))
        btn_generar.bind("<Leave>", lambda e: btn_generar.config(bg='#0984e3'))

        # --- Sección de transferencias ---
        frame_transferencias = LabelFrame(main_container, 
                                        text="  💳 PAGOS POR TRANSFERENCIA  ",
                                        font=('Poppins', 12, 'bold'),
                                        bg='#ffffff', fg='#2d3436', bd=1,
                                        relief='groove', padx=15, pady=10)
        frame_transferencias.pack(fill='both', expand=True, padx=40, pady=(0, 25))

        # --- Configuración EXCLUSIVA del Treeview ---
        self._configure_unique_style()  # Método nuevo para estilos únicos
        
        # Contenedor para Treeview y Scrollbar
        tree_container = Frame(frame_transferencias)
        tree_container.pack(fill='both', expand=True)
        
        self.tree_transferencias = ttk.Treeview(tree_container, 
                                              columns=("codigo", "cliente", "monto"), 
                                              show="headings",
                                              height=7,
                                              selectmode='browse',
                                              style='Inventario.Treeview')
        
        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree_transferencias.yview)
        self.tree_transferencias.configure(yscrollcommand=scrollbar.set)
        
        # Configuración de columnas
        column_style = {'anchor': 'center', 'stretch': False}
        self.tree_transferencias.heading("codigo", text="CÓDIGO")
        self.tree_transferencias.column("codigo", width=350, **column_style)
        
        self.tree_transferencias.heading("cliente", text="CLIENTE")
        self.tree_transferencias.column("cliente", width=350, **column_style)
        
        self.tree_transferencias.heading("monto", text="MONTO ($)")
        self.tree_transferencias.column("monto", width=350, **column_style)
        
        # Layout
        self.tree_transferencias.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Estilo para total
        self.tree_transferencias.tag_configure('total', 
                                             background='#f1f8fe', 
                                             font=('Poppins', 10, 'bold'),
                                             foreground='#2d3436')
        
    def _generar_y_mostrar_ticket(self):
        """Genera y muestra el ticket de corte de caja automáticamente"""
        try:
            # Obtener la fecha y hora actual
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            hora_actual = datetime.now().strftime("%H:%M:%S")
            
            # Obtener TODOS los productos vendidos (sin filtrar por fecha)
            productos_vendidos = self.session.query(InventarioModel).all()
            
            # Obtener TODAS las transferencias (sin filtrar por fecha)
            transferencias = self.session.query(TransferenciaDiferencia).all()
            
            # Calcular totales
            total_ventas_efectivo = sum(p.Stock * p.PrecioProducto for p in productos_vendidos 
                                    if p.CodigodeBarras not in [t.CodigodeBarras for t in transferencias])
            
            total_transferencias = sum(t.Monto for t in transferencias)
            total_general = total_ventas_efectivo + total_transferencias
            
            # Generar el PDF del ticket
            pdf_path = self._generar_pdf_ticket(fecha_actual, hora_actual, productos_vendidos, transferencias, 
                                total_ventas_efectivo, total_transferencias, total_general)
            
            # Mostrar vista previa del ticket
            self.mostrar_vista_previa_ticket(pdf_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el ticket:\n{str(e)}")

    def _generar_pdf_ticket(self, fecha, hora, productos, transferencias, total_efectivo, total_transferencias, total_general):
        """Genera el PDF del ticket de corte de caja"""
        try:
            # Configuración para impresora térmica (80mm de ancho)
            width = 80 * mm
            height = 400 * mm
            custom_size = (width, height)

            # Crear directorio temporal si no existe
            temp_dir = tempfile.gettempdir()
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
    
            pdf_path = os.path.join(temp_dir, f"corte_caja_{fecha.replace('-', '')}_{hora.replace(':', '')}.pdf")
            c = canvas.Canvas(pdf_path, pagesize=custom_size)

            # Configuración de márgenes
            margin_left = 5 * mm
            margin_right = 5 * mm
            y_position = height - 10 * mm

            # Encabezado
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width/2, y_position, "MULTIMARCAS TURQUESA")
            y_position -= 6 * mm

            # Dirección
            c.setFont("Helvetica", 11)
            c.drawCentredString(width/2, y_position, "Carretera Antigua Camp-Merida #341")
            y_position -= 5 * mm
            c.drawCentredString(width/2, y_position, "Col.Santa Lucia, Campeche, Campeche")
            y_position -= 8 * mm

            c.setFont("Helvetica", 11)
            c.drawCentredString(width/2, y_position, "CORTE DE CAJA")
            y_position -= 8 * mm

            c.drawCentredString(width/2, y_position, f"Fecha: {fecha}")
            y_position -= 6 * mm
            c.drawCentredString(width/2, y_position, f"Hora: {hora}")
            y_position -= 10 * mm

            # Línea divisoria de guiones
            c.setFont("Helvetica", 12)
            linea_guiones = "-" * 53  # Línea de 30 guiones
            c.drawCentredString(width/2, y_position, linea_guiones)
            y_position -= 12 * mm


            # Obtener los totales de la interfaz
            total_productos_vendidos = self.lbl_total_productos_valor.cget("text")
            # Obtener el total de ventas en efectivo (convertir de texto a número)
            total_ventas_efectivo_texto = self.lbl_monto_total_valor.cget("text")
            # Remover el símbolo de dólar y convertir a float
            total_ventas_efectivo = float(total_ventas_efectivo_texto.replace('$', '').replace(',', ''))

            # Función para formatear números con separadores de miles
            def formato_moneda(monto):
                return f"${monto:,.2f}"

            # Mostrar total de productos vendidos
            c.setFont("Helvetica", 12)
            c.drawString(margin_left, y_position, "Productos Vendidos:")
            c.drawString(margin_left + 40 * mm, y_position, f"{total_productos_vendidos}")
            y_position -= 10 * mm

            # Mostrar total de ventas en efectivo
            c.setFont("Helvetica", 12)
            c.drawString(margin_left, y_position, "Ventas Pagadas En Efectivo:")
            c.drawString(margin_left + 55 * mm, y_position, formato_moneda(total_ventas_efectivo))
            y_position -= 12 * mm

            # Transferencias (solo si existen)
            if transferencias:
                c.setFont("Helvetica", 12)
                c.drawString(margin_left, y_position, "PAGOS POR TRANSFERENCIA:")
                y_position -= 8 * mm
    
                c.setFont("Helvetica-Bold", 10)
                c.drawString(margin_left, y_position, "Código")
                c.drawString(margin_left + 25 * mm, y_position, "Cliente")
                c.drawString(margin_left + 55 * mm, y_position, "Monto")
                y_position -= 6 * mm
    
                c.setFont("Helvetica", 10)
                for transferencia in transferencias:
                    # Acortar nombre si es muy largo
                    nombre_cliente = transferencia.Cliente
                    if len(nombre_cliente) > 15:
                        nombre_cliente = nombre_cliente[:12] + "..."
            
                    c.drawString(margin_left, y_position, transferencia.CodigodeBarras[:8])
                    c.drawString(margin_left + 25 * mm, y_position, nombre_cliente)
                    c.drawString(margin_left + 55 * mm, y_position, formato_moneda(transferencia.Monto))
                    y_position -= 5 * mm
        
                    # Salto de página si es necesario
                    if y_position < 50 * mm:
                        c.showPage()
                        y_position = height - 10 * mm
    
                    y_position -= 8 * mm
    
                # Total transferencias
                c.setFont("Helvetica-Bold", 11)
                c.drawString(margin_left, y_position, "TOTAL TRANSFERENCIAS:")
                c.drawString(margin_left + 55 * mm, y_position, formato_moneda(total_transferencias))
                y_position -= 10 * mm

            # Línea divisoria final de guiones
            c.setFont("Helvetica", 12)
            linea_guiones_final = "-" * 53  # Línea de 30 guiones
            c.drawCentredString(width/2, y_position, linea_guiones_final)
            y_position -= 10 * mm

            # Total general (suma de ventas en efectivo + transferencias)
            total_general = total_ventas_efectivo + total_transferencias
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin_left, y_position, "TOTAL GENERAL:")
            c.drawString(margin_left + 55 * mm, y_position, formato_moneda(total_general))
            y_position -= 12 * mm

            # Agregar información del usuario que atendió
            c.setFont("Helvetica", 11)
            c.drawString(margin_left, y_position, f"Turno en caja por: {self.usuario_actual}")
            y_position -= 12* mm
    
            # Firma y hora
            c.drawString(margin_left, y_position, "Firma: ___________________")
            y_position -= 6 * mm
            c.drawString(margin_left, y_position, f"Hora corte: {hora}")

            c.save()

            return pdf_path

        except Exception as e:
            raise Exception(f"Error al generar PDF: {str(e)}")

    def mostrar_vista_previa_ticket(self, pdf_path):
        """Muestra una ventana con la vista previa del ticket usando pdf2image"""
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "No se pudo generar el ticket para vista previa")
            return

        # Crear ventana de vista previa más pequeña
        preview_window = Toplevel(self)
        preview_window.title("Vista Previa del Ticket de Corte")
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
                temp_img_path = os.path.join(tempfile.gettempdir(), "ticket_corte_preview.png")
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

            # Limpiar las tablas después de imprimir
            self._limpiar_tablas()

            # Redireccionar al login
            self._redireccionar_a_login()
    
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo imprimir el ticket: {str(e)}")

    def _limpiar_tablas(self):
        """Limpia las tablas Inventario y transferencias_diferencias"""
        try:
            # Limpiar tabla Inventario
            self.session.query(InventarioModel).delete()
        
            # Limpiar tabla transferencias_diferencias
            self.session.query(TransferenciaDiferencia).delete()
        
            self.session.commit()
            print("Tablas limpiadas exitosamente")
        
        except Exception as e:
            self.session.rollback()
            print(f"Error al limpiar tablas: {e}")

    def _redireccionar_a_login(self):
        """Redirecciona al apartado de login"""
        try:
            # Buscar el controlador principal
            controlador = self.winfo_toplevel()
            
            # Verificar si el controlador tiene el método show_frame
            if hasattr(controlador, 'show_frame'):
                # Cerrar la sesión actual primero
                self.session.close()
            
                # Destruir este frame completamente
                self.destroy()
            
                # Importar y crear una nueva instancia de Login
                import login
                nuevo_login = login.Login(controlador, controlador)
            
                # Mostrar el frame de login
                nuevo_login.tkraise()
            else:
                # Si no encontramos el controlador, mostramos un mensaje
                messagebox.showinfo("Corte completado", "Corte de caja finalizado. Por favor inicie sesión nuevamente.")
            
        except Exception as e:
            print(f"Error al redireccionar al login: {e}")
            messagebox.showinfo("Corte completado", "Corte de caja finalizado. Por favor inicie sesión nuevamente.")



    def _configure_unique_style(self):
        """Configura estilos únicos para este módulo que no afecten al resto"""
        style = ttk.Style()
        
        # Crear un estilo único para este Treeview
        style.configure('Inventario.Treeview', 
                      font=('Poppins', 10), 
                      rowheight=30,
                      background='#ffffff',
                      fieldbackground='#ffffff',
                      bordercolor='#dfe6e9',
                      borderwidth=0)
        
        style.configure('Inventario.Treeview.Heading', 
                      font=('Poppins', 11, 'bold'), 
                      background='#0984e3', 
                      foreground='white',
                      borderwidth=0,
                      padding=8)
        
        style.map('Inventario.Treeview.Heading', 
                background=[('active', '#0767b3')])
        
        style.map('Inventario.Treeview', 
                background=[('selected', '#e3f2fd')])
        

    def _transferir_ventas_a_inventario(self):
        """Transfiere solo los productos vendidos (con stock negativo) a Inventario"""
        try:
            productos_vendidos = self.session.query(RegistroProducto).filter(
                RegistroProducto.Stock < 0
            ).all()
        
            for producto in productos_vendidos:
                cantidad_vendida = abs(producto.Stock)
            
                inventario_existente = self.session.query(InventarioModel).filter(
                    InventarioModel.CodigodeBarras == producto.CodigodeBarras,
                    InventarioModel.PrecioProducto == producto.PrecioProducto
                ).first()
            
                if inventario_existente:
                    inventario_existente.Stock += cantidad_vendida
                else:
                    nuevo_inventario = InventarioModel(
                        CodigodeBarras=producto.CodigodeBarras,
                        Cliente=producto.Cliente,
                        Stock=cantidad_vendida,
                        PrecioProducto=producto.PrecioProducto,
                        Id_productos=producto.Id_productos
                    )
                    self.session.add(nuevo_inventario)
            
                producto.Stock = 0
        
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error", f"No se pudieron transferir las ventas:\n{e}")
            return False

    def _mostrar_transferencias(self):
        """Muestra los registros de transferencias_diferencias en el treeview"""
        try:
            for item in self.tree_transferencias.get_children():
                self.tree_transferencias.delete(item)
            
            transferencias = self.session.query(TransferenciaDiferencia).all()
            
            total_transferencias = 0.0
            for transferencia in transferencias:
                self.tree_transferencias.insert("", "end", 
                                               values=(transferencia.CodigodeBarras,
                                                      transferencia.Cliente,
                                                      f"${transferencia.Monto:.2f}"))
                total_transferencias += transferencia.Monto
            
            # Agregar fila de total
            self.tree_transferencias.insert("", "end", 
                                          values=("", "TOTAL:", f"${total_transferencias:.2f}"),
                                          tags=('total',))
            
            # Configurar estilo para la fila de total
            self.tree_transferencias.tag_configure('total', background='#e0e0e0', font=('Helvetica', 10, 'bold'))
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las transferencias:\n{e}")

    def _generar_corte(self):
        """Genera el corte de caja basado en la tabla Inventario"""
        try:
            if not self._transferir_ventas_a_inventario():
                return
                
            ventas = self.session.query(InventarioModel).all()
            
            total_productos = sum(venta.Stock for venta in ventas)
            total_monto = sum(venta.Stock * venta.PrecioProducto for venta in ventas)
            
            self.lbl_fecha_valor.config(text=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            self.lbl_total_productos_valor.config(text=str(total_productos))
            self.lbl_monto_total_valor.config(text=f"${total_monto:.2f}")
            
            self._mostrar_transferencias()

            # Generar y mostrar el ticket automáticamente después del corte
            self._generar_y_mostrar_ticket()
            
            messagebox.showinfo("Éxito", "Corte de caja generado correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el corte de caja:\n{e}")