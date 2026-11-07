import customtkinter as ctk
import uuid
from datetime import datetime

class POSView(ctk.CTkFrame):
    def __init__(self, parent, db, app_reference):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.app_ref = app_reference
        self.carrito = []
        self.ventas_en_espera = []
        self.contador_espera = 1

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        # --- SECCIÓN SUPERIOR ---
        top_container = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12)
        top_container.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")

        lbl_escaneo = ctk.CTkLabel(
            top_container, 
            text="🔎 Buscar por nombre o código:", 
            font=("Segoe UI", 13, "bold"), 
            text_color="#F8FAFC"
        )
        lbl_escaneo.pack(side="left", padx=(15, 10), pady=12)

        self.entry_codigo = ctk.CTkEntry(
            top_container, 
            placeholder_text="Escribe o escanea un código...", 
            font=("Segoe UI", 13), 
            width=330,
            height=38,
            fg_color="#0F172A",
            border_color="#334155"
        )
        self.entry_codigo.pack(side="left", padx=5, pady=12)
        
        self.entry_codigo.bind("<KeyRelease>", self.on_search_key_release)
        self.entry_codigo.bind("<Return>", self.agregar_por_barcode_enter)

        btn_limpiar_search = ctk.CTkButton(
            top_container, text="Limpiar", width=65, height=36,
            fg_color="#334155", hover_color="#475569", command=self.limpiar_busqueda
        )
        btn_limpiar_search.pack(side="left", padx=5, pady=12)

        # Indicador de Caja
        self.btn_estado_caja = ctk.CTkButton(
            top_container, text="💰 Caja...", width=130, height=36,
            fg_color="#334155", font=("Segoe UI", 11, "bold"),
            command=self.ir_a_caja
        )
        self.btn_estado_caja.pack(side="right", padx=10, pady=12)

        # Botón de Acceso Rápido a Ventas en Espera en barra superior
        self.btn_top_espera = ctk.CTkButton(
            top_container, text="⏸️ Ventas en Espera (0)", width=170, height=36,
            fg_color="#D97706", hover_color="#B45309", font=("Segoe UI", 12, "bold"),
            command=self.abrir_modal_ventas_espera
        )
        self.btn_top_espera.pack(side="right", padx=5, pady=12)

        # --- PANEL IZQUIERDO ---
        left_container = ctk.CTkFrame(self, fg_color="transparent")
        left_container.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="nsew")
        left_container.grid_columnconfigure(0, weight=1)
        left_container.grid_rowconfigure(0, weight=1)
        left_container.grid_rowconfigure(1, weight=2)

        self.frame_resultados = ctk.CTkScrollableFrame(
            left_container, 
            label_text="🔍 Coincidencias encontradas", 
            label_font=("Segoe UI", 12, "bold"),
            fg_color="#1E293B",
            height=160
        )
        self.frame_resultados.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        self.frame_carrito = ctk.CTkScrollableFrame(
            left_container, 
            label_text="🛒 Carrito de Compras", 
            label_font=("Segoe UI", 13, "bold"),
            fg_color="#1E293B"
        )
        self.frame_carrito.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

        # --- PANEL DERECHO ---
        right_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12)
        right_frame.grid(row=1, column=1, padx=(5, 10), pady=10, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)

        lbl_resumen = ctk.CTkLabel(right_frame, text="Resumen de Venta", font=("Segoe UI", 18, "bold"), text_color="#F8FAFC")
        lbl_resumen.pack(pady=(20, 10))

        self.lbl_total = ctk.CTkLabel(right_frame, text="TOTAL: $0", font=("Segoe UI", 28, "bold"), text_color="#10B981")
        self.lbl_total.pack(pady=15)

        self.lbl_items = ctk.CTkLabel(right_frame, text="Artículos: 0", font=("Segoe UI", 13), text_color="#94A3B8")
        self.lbl_items.pack(pady=2)

        self.lbl_mensaje = ctk.CTkLabel(right_frame, text="", font=("Segoe UI", 12))
        self.lbl_mensaje.pack(pady=10)

        # Botón Cobrar
        btn_cobrar = ctk.CTkButton(
            right_frame, text="💳 PROCESAR PAGO", command=self.abrir_modal_pago, 
            fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 16, "bold"), height=50, corner_radius=10
        )
        btn_cobrar.pack(fill="x", padx=15, pady=10)

        # Botón Pausar Venta (En Espera)
        self.btn_pausar = ctk.CTkButton(
            right_frame, text="⏸️ Pausar Venta (Venta en Espera)", command=self.pausar_venta_actual,
            fg_color="#F59E0B", hover_color="#D97706", text_color="#0F172A", font=("Segoe UI", 13, "bold"), height=38, corner_radius=8
        )
        self.btn_pausar.pack(fill="x", padx=15, pady=5)

        # Botón Ver Ventas en Espera
        self.btn_ver_espera = ctk.CTkButton(
            right_frame, text="📋 Ver Ventas en Espera (0)", command=self.abrir_modal_ventas_espera,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 13, "bold"), height=36, corner_radius=8
        )
        self.btn_ver_espera.pack(fill="x", padx=15, pady=5)

        # Botón Vaciar Carrito
        btn_limpiar = ctk.CTkButton(
            right_frame, text="🗑️ Vaciar Carrito", command=self.vaciar_carrito, 
            fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 12), height=34, corner_radius=8
        )
        btn_limpiar.pack(fill="x", padx=15, pady=(15, 15))

        self.focus_codigo()
        self.actualizar_lista_resultados([])

    def focus_codigo(self):
        self.entry_codigo.focus_set()
        self.actualizar_estado_caja()

    def ir_a_caja(self):
        if self.app_ref:
            self.app_ref.show_view("cash")

    def actualizar_estado_caja(self):
        caja = self.db.get_caja_abierta()
        if caja:
            self.btn_estado_caja.configure(text="🟢 Caja Abierta", fg_color="#065F46", hover_color="#047857")
        else:
            self.btn_estado_caja.configure(text="🔴 Caja Cerrada", fg_color="#7F1D1D", hover_color="#991B1B")

    def limpiar_busqueda(self):
        self.entry_codigo.delete(0, "end")
        self.actualizar_lista_resultados([])
        self.focus_codigo()

    def on_search_key_release(self, event):
        if event.keysym in ["Return", "Escape"]:
            if event.keysym == "Escape":
                self.limpiar_busqueda()
            return

        query = self.entry_codigo.get().strip()
        coincidencias = self.db.buscar_productos_live(query)
        self.actualizar_lista_resultados(coincidencias)

    def actualizar_lista_resultados(self, productos):
        for widget in self.frame_resultados.winfo_children():
            widget.destroy()

        btn_otros = ctk.CTkButton(
            self.frame_resultados,
            text="➕ OTROS / PAN / VERDURAS (Ingresar Monto Manual)",
            anchor="w",
            fg_color="#D97706",
            hover_color="#B45309",
            text_color="#F8FAFC",
            font=("Segoe UI", 12, "bold"),
            height=36,
            corner_radius=6,
            command=self.abrir_modal_otros
        )
        btn_otros.pack(fill="x", padx=5, pady=3)

        for prod in productos:
            btn_item = ctk.CTkButton(
                self.frame_resultados,
                text=f"➕  {prod[2]}   |   Precio: ${int(prod[4]):,}   |   Stock: {prod[5]}   |   Código: {prod[1]}",
                anchor="w",
                fg_color="#0F172A",
                hover_color="#334155",
                text_color="#F8FAFC",
                font=("Segoe UI", 12),
                height=36,
                corner_radius=6,
                command=lambda p=prod: self.seleccionar_producto_live(p)
            )
            btn_item.pack(fill="x", padx=5, pady=3)

    def abrir_modal_otros(self):
        modal = ctk.CTkToplevel(self)
        modal.title("➕ Agregar Producto Genérico / Sin Código")
        modal.geometry("380x360")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="🥐 Producto Variable (Pan, Verdura, etc.)", font=("Segoe UI", 15, "bold"), text_color="#F59E0B").pack(pady=(20, 10))

        ctk.CTkLabel(modal, text="Descripción (opcional):", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=30, pady=(5,0))
        entry_desc = ctk.CTkEntry(modal, placeholder_text="Ej: Pan, Tomates, Galleta", fg_color="#0F172A", width=320)
        entry_desc.pack(padx=30, pady=4)
        entry_desc.focus_set()

        ctk.CTkLabel(modal, text="Monto Total a Cobrar ($):", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=30, pady=(5,0))
        
        def solo_num_otros(P):
            return P == "" or P.isdigit()
        vcmd_otros = (modal.register(solo_num_otros), '%P')

        entry_monto = ctk.CTkEntry(modal, placeholder_text="Ej: 1250", fg_color="#0F172A", width=320, font=("Segoe UI", 14, "bold"), validate="key", validatecommand=vcmd_otros)
        entry_monto.pack(padx=30, pady=4)

        lbl_error = ctk.CTkLabel(modal, text="", font=("Segoe UI", 11), text_color="#EF4444")
        lbl_error.pack(pady=5)

        def agregar():
            desc = entry_desc.get().strip()
            if not desc:
                desc = "Otros"

            try:
                monto = float(entry_monto.get().strip())
                if monto <= 0:
                    raise ValueError
            except ValueError:
                lbl_error.configure(text="❌ Ingresa un monto válido.")
                return

            fake_id = f"otros_{uuid.uuid4().hex[:6]}"
            nombre_final = f"Otros: {desc}"
            self.carrito.append((fake_id, "OTROS", nombre_final, 0, monto, 1, monto))

            self.actualizar_tabla_carrito()
            modal.destroy()
            self.limpiar_busqueda()

        btn_confirmar = ctk.CTkButton(modal, text="Agregar al Carrito", command=agregar, fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 13, "bold"), height=38, width=320)
        btn_confirmar.pack(pady=15)

    def seleccionar_producto_live(self, prod):
        prod_id, cod, nombre, p_costo, p_venta, stock = prod
        self.agregar_al_carrito_data(prod_id, cod, nombre, p_costo, p_venta, stock)
        self.limpiar_busqueda()

    def agregar_por_barcode_enter(self, event=None):
        codigo = self.entry_codigo.get().strip()
        if not codigo:
            return

        producto = self.db.get_producto_por_codigo(codigo)
        if not producto:
            coincidencias = self.db.buscar_productos_live(codigo)
            if coincidencias:
                producto = coincidencias[0]
            else:
                self.limpiar_busqueda()
                # Consultar en catálogo maestro Open Food Facts
                sug_maestro = self.db.buscar_en_catalogo_maestro(codigo)
                if sug_maestro:
                    self.abrir_modal_sugerencia_maestro(codigo, sug_maestro)
                else:
                    self.abrir_modal_registro(codigo)
                return

        prod_id, cod, nombre, p_costo, p_venta, stock = producto
        self.agregar_al_carrito_data(prod_id, cod, nombre, p_costo, p_venta, stock)
        self.limpiar_busqueda()

    def abrir_modal_sugerencia_maestro(self, codigo, prod_maestro):
        modal = ctk.CTkToplevel(self)
        modal.title("⚡ Sugerencia Open Food Facts (Chile)")
        modal.geometry("440x480")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="⚡ PRODUCTO RECONOCIDO", font=("Segoe UI", 17, "bold"), text_color="#38BDF8").pack(pady=(20, 2))
        ctk.CTkLabel(modal, text="Base de Datos: Open Food Facts (Chile)", font=("Segoe UI", 10), text_color="#94A3B8").pack(pady=(0, 10))

        # Tarjeta del producto encontrado
        card = ctk.CTkFrame(modal, fg_color="#0F172A", corner_radius=10)
        card.pack(fill="x", padx=25, pady=10)

        # Badge Marca / Categoría
        marca = prod_maestro.get("marca") or "Comercial"
        cat = prod_maestro.get("categoria") or "Abarrotes"
        top_c = ctk.CTkFrame(card, fg_color="transparent")
        top_c.pack(fill="x", padx=15, pady=(12, 4))
        ctk.CTkLabel(top_c, text=f"🏷️ Marca: {marca}", font=("Segoe UI", 11, "bold"), text_color="#F59E0B").pack(side="left")
        ctk.CTkLabel(top_c, text=f"Categoría: {cat}", font=("Segoe UI", 10), text_color="#94A3B8").pack(side="right")

        # Nombre oficial sugerido
        lbl_nom = ctk.CTkLabel(
            card, text=prod_maestro["nombre"], 
            font=("Segoe UI", 15, "bold"), text_color="#F8FAFC", wraplength=350, justify="left"
        )
        lbl_nom.pack(anchor="w", padx=15, pady=(4, 6))

        ctk.CTkLabel(card, text=f"Código de Barras: {codigo}", font=("Segoe UI", 11), text_color="#64748B").pack(anchor="w", padx=15, pady=(0, 12))

        ctk.CTkLabel(
            modal, 
            text="¿Es este el producto que deseas ingresar al almacén?",
            font=("Segoe UI", 12, "bold"), text_color="#E2E8F0"
        ).pack(pady=(10, 15))

        def confirmar_sugerencia():
            modal.destroy()
            self.abrir_modal_registro(codigo, nombre_precargado=prod_maestro["nombre"])

        def rechazar_sugerencia():
            modal.destroy()
            self.abrir_modal_registro(codigo, nombre_precargado="")

        # Botón 1: Confirmar sugerencia
        btn_si = ctk.CTkButton(
            modal, 
            text="✔️ SÍ, ES ESTE PRODUCTO (Confirmar)", 
            command=confirmar_sugerencia, 
            fg_color="#10B981", 
            hover_color="#059669", 
            font=("Segoe UI", 13, "bold"), 
            height=44, 
            width=360
        )
        btn_si.pack(pady=6)

        # Botón 2: Rechazar e ingresar a mano
        btn_no = ctk.CTkButton(
            modal, 
            text="❌ NO ES ESTE PRODUCTO (Ingresar a Mano)", 
            command=rechazar_sugerencia, 
            fg_color="#334155", 
            hover_color="#475569", 
            font=("Segoe UI", 12), 
            height=38, 
            width=360
        )
        btn_no.pack(pady=6)

    def abrir_modal_registro(self, codigo_desconocido, nombre_precargado=""):
        modal = ctk.CTkToplevel(self)
        modal.title("⚡ Registrar Producto en Inventario")
        modal.geometry("400x520")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="📦 Registrar Nuevo Producto", font=("Segoe UI", 16, "bold"), text_color="#38BDF8").pack(pady=(20, 5))
        ctk.CTkLabel(modal, text=f"Código: {codigo_desconocido}", font=("Segoe UI", 11), text_color="#94A3B8").pack(pady=(0, 15))

        entry_nombre = ctk.CTkEntry(modal, placeholder_text="Nombre del producto", fg_color="#0F172A", width=340)
        entry_nombre.pack(padx=30, pady=6)
        if nombre_precargado:
            entry_nombre.insert(0, nombre_precargado)

        entry_costo = ctk.CTkEntry(modal, placeholder_text="Precio Costo ($)", fg_color="#0F172A", width=340)
        entry_costo.pack(padx=30, pady=6)

        entry_precio = ctk.CTkEntry(modal, placeholder_text="Precio Venta ($)", fg_color="#0F172A", width=340)
        entry_precio.pack(padx=30, pady=6)

        entry_stock = ctk.CTkEntry(modal, placeholder_text="Stock Inicial", fg_color="#0F172A", width=340)
        entry_stock.pack(padx=30, pady=6)
        entry_stock.insert(0, "10")

        if nombre_precargado:
            entry_costo.focus_set()
        else:
            entry_nombre.focus_set()

        lbl_err = ctk.CTkLabel(modal, text="", font=("Segoe UI", 11), text_color="#EF4444")
        lbl_err.pack(pady=5)

        def guardar():
            nombre = entry_nombre.get().strip()
            try:
                p_costo = float(entry_costo.get().strip())
                p_venta = float(entry_precio.get().strip())
                stock = int(entry_stock.get().strip())
                if not nombre: raise ValueError
            except ValueError:
                lbl_err.configure(text="❌ Completa todos los campos correctamente.")
                return

            exito, msg = self.db.guardar_producto(codigo_desconocido, nombre, p_costo, p_venta, stock)
            if not exito:
                lbl_err.configure(text=f"❌ {msg}")
                return

            prod_g = self.db.get_producto_por_codigo(codigo_desconocido)
            if prod_g:
                self.agregar_al_carrito_data(prod_g[0], codigo_desconocido, nombre, p_costo, p_venta, stock)
            modal.destroy()
            self.focus_codigo()

        ctk.CTkButton(modal, text="Guardar y Agregar a la Venta", command=guardar, fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 13, "bold"), height=40, width=340).pack(pady=15)

    def agregar_al_carrito_data(self, prod_id, cod, nombre, p_costo, p_venta, stock):
        if stock <= 0:
            self.lbl_mensaje.configure(text=f"⚠️ '{nombre}' sin stock.", text_color="#F59E0B")

        encontrado = False
        for i, item in enumerate(self.carrito):
            if item[0] == prod_id:
                nueva_cant = item[5] + 1
                nuevo_subtotal = nueva_cant * p_venta
                self.carrito[i] = (prod_id, cod, nombre, p_costo, p_venta, nueva_cant, nuevo_subtotal)
                encontrado = True
                break

        if not encontrado:
            self.carrito.append((prod_id, cod, nombre, p_costo, p_venta, 1, p_venta))

        self.lbl_mensaje.configure(text=f"✔️ Agregado: {nombre}", text_color="#10B981")
        self.actualizar_tabla_carrito()

    def cambiar_cantidad(self, prod_id, delta):
        for i, item in enumerate(self.carrito):
            if item[0] == prod_id:
                nueva_cant = item[5] + delta
                if nueva_cant <= 0:
                    self.eliminar_item(prod_id)
                    return
                nuevo_subtotal = nueva_cant * item[4]
                self.carrito[i] = (item[0], item[1], item[2], item[3], item[4], nueva_cant, nuevo_subtotal)
                break
        self.actualizar_tabla_carrito()

    def eliminar_item(self, prod_id):
        self.carrito = [item for item in self.carrito if item[0] != prod_id]
        self.actualizar_tabla_carrito()

    def actualizar_tabla_carrito(self):
        for widget in self.frame_carrito.winfo_children():
            widget.destroy()

        headers_frame = ctk.CTkFrame(self.frame_carrito, fg_color="#0F172A")
        headers_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(headers_frame, text="Producto", width=140, font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", padx=8)
        ctk.CTkLabel(headers_frame, text="Precio", width=80, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Cant.", width=90, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Total", width=80, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="", width=40).pack(side="left", padx=5)

        total_bruto = 0
        cant_total = 0

        for item in self.carrito:
            prod_id, _, nombre, _, p_venta, cant, subtotal = item
            total_bruto += subtotal
            cant_total += cant

            row = ctk.CTkFrame(self.frame_carrito, fg_color="#0F172A", corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=nombre, width=140, anchor="w", font=("Segoe UI", 12)).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=f"${int(p_venta):,}", width=80, font=("Segoe UI", 12)).pack(side="left", padx=5)

            cant_frame = ctk.CTkFrame(row, fg_color="transparent")
            cant_frame.pack(side="left", padx=5)

            btn_minus = ctk.CTkButton(
                cant_frame, text="-", width=24, height=24, fg_color="#EF4444", hover_color="#DC2626", 
                command=lambda pid=prod_id: self.cambiar_cantidad(pid, -1)
            )
            btn_minus.pack(side="left")

            ctk.CTkLabel(cant_frame, text=str(cant), width=30, font=("Segoe UI", 12, "bold")).pack(side="left")

            btn_plus = ctk.CTkButton(
                cant_frame, text="+", width=24, height=24, fg_color="#10B981", hover_color="#059669", 
                command=lambda pid=prod_id: self.cambiar_cantidad(pid, 1)
            )
            btn_plus.pack(side="left")

            ctk.CTkLabel(row, text=f"${int(subtotal):,}", width=80, font=("Segoe UI", 12, "bold"), text_color="#10B981").pack(side="left", padx=5)

            btn_del = ctk.CTkButton(
                row, text="🗑️", width=28, height=24, fg_color="transparent", text_color="#EF4444",
                hover_color="#331111", command=lambda pid=prod_id: self.eliminar_item(pid)
            )
            btn_del.pack(side="left", padx=5)

        self.lbl_total.configure(text=f"TOTAL: ${int(total_bruto):,}")
        self.lbl_items.configure(text=f"Artículos: {cant_total}")

    # --- VENTA EN ESPERA ---
    def actualizar_indicador_espera(self):
        cant = len(self.ventas_en_espera)
        texto = f"⏸️ Ventas en Espera ({cant})"
        self.btn_ver_espera.configure(text=texto)
        self.btn_top_espera.configure(text=texto)
        if cant > 0:
            self.btn_ver_espera.configure(fg_color="#D97706", hover_color="#B45309")
            self.btn_top_espera.configure(fg_color="#D97706", hover_color="#B45309")
        else:
            self.btn_ver_espera.configure(fg_color="#334155", hover_color="#475569")
            self.btn_top_espera.configure(fg_color="#334155", hover_color="#475569")

    def pausar_venta_actual(self):
        if not self.carrito:
            self.lbl_mensaje.configure(text="⚠️ El carrito está vacío, nada que pausar.", text_color="#F59E0B")
            return

        total_venta = sum(item[6] for item in self.carrito)
        total_arts = sum(item[5] for item in self.carrito)
        hora_str = datetime.now().strftime("%H:%M:%S")

        ticket_id = self.contador_espera
        self.contador_espera += 1

        venta_guardada = {
            "id": ticket_id,
            "etiqueta": f"Ticket #{ticket_id}",
            "hora": hora_str,
            "items": list(self.carrito),
            "total": total_venta,
            "cant_arts": total_arts
        }

        self.ventas_en_espera.append(venta_guardada)
        self.carrito = []
        self.actualizar_tabla_carrito()
        self.actualizar_indicador_espera()
        self.lbl_mensaje.configure(text=f"⏸️ Venta #{ticket_id} guardada en espera.", text_color="#F59E0B")
        self.focus_codigo()

    def abrir_modal_ventas_espera(self):
        modal = ctk.CTkToplevel(self)
        modal.title("⏸️ Ventas en Espera")
        modal.geometry("520x450")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        header_frame = ctk.CTkFrame(modal, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(header_frame, text="⏸️ Ventas Pausadas en Espera", font=("Segoe UI", 16, "bold"), text_color="#F59E0B").pack(side="left")
        ctk.CTkLabel(header_frame, text=f"Total: {len(self.ventas_en_espera)}", font=("Segoe UI", 12), text_color="#94A3B8").pack(side="right")

        scroll_espera = ctk.CTkScrollableFrame(modal, fg_color="#0F172A", height=310)
        scroll_espera.pack(fill="both", expand=True, padx=20, pady=5)

        def refrescar_contenido():
            for widget in scroll_espera.winfo_children():
                widget.destroy()

            if not self.ventas_en_espera:
                ctk.CTkLabel(
                    scroll_espera, 
                    text="No hay compras pausadas en espera actualmente.", 
                    font=("Segoe UI", 12), 
                    text_color="#64748B"
                ).pack(pady=40)
                return

            for ticket in self.ventas_en_espera:
                t_id = ticket["id"]
                t_hora = ticket["hora"]
                t_arts = ticket["cant_arts"]
                t_tot = ticket["total"]
                t_items = ticket["items"]

                card = ctk.CTkFrame(scroll_espera, fg_color="#1E293B", corner_radius=8)
                card.pack(fill="x", padx=5, pady=5)

                top_c = ctk.CTkFrame(card, fg_color="transparent")
                top_c.pack(fill="x", padx=10, pady=(8, 2))

                ctk.CTkLabel(top_c, text=f"Ticket #{t_id} • {t_hora}", font=("Segoe UI", 13, "bold"), text_color="#38BDF8").pack(side="left")
                ctk.CTkLabel(top_c, text=f"${int(t_tot):,}", font=("Segoe UI", 15, "bold"), text_color="#10B981").pack(side="right")

                resumen_txt = ", ".join([f"{item[2]} (x{item[5]})" for item in t_items[:3]])
                if len(t_items) > 3:
                    resumen_txt += f" ... y {len(t_items)-3} más"

                ctk.CTkLabel(card, text=f"{t_arts} artículo(s) | {resumen_txt}", font=("Segoe UI", 11), text_color="#94A3B8", anchor="w").pack(fill="x", padx=10, pady=(0, 8))

                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(fill="x", padx=10, pady=(0, 8))

                btn_reanudar = ctk.CTkButton(
                    btn_frame, text="▶️ Cargar al Carrito", width=140, height=30,
                    fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 11, "bold"),
                    command=lambda t=ticket: self.reanudar_venta(t, modal)
                )
                btn_reanudar.pack(side="left", padx=(0, 8))

                btn_borrar = ctk.CTkButton(
                    btn_frame, text="🗑️ Descartar", width=90, height=30,
                    fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 11),
                    command=lambda t=ticket: self.descartar_venta_espera(t, refrescar_contenido)
                )
                btn_borrar.pack(side="left")

        refrescar_contenido()

        btn_cerrar = ctk.CTkButton(modal, text="Cerrar", command=modal.destroy, fg_color="#334155", hover_color="#475569", width=100)
        btn_cerrar.pack(pady=10)

    def reanudar_venta(self, ticket, modal):
        if self.carrito:
            for item in ticket["items"]:
                self.carrito.append(item)
        else:
            self.carrito = list(ticket["items"])

        self.ventas_en_espera = [v for v in self.ventas_en_espera if v["id"] != ticket["id"]]
        self.actualizar_indicador_espera()
        self.actualizar_tabla_carrito()
        modal.destroy()
        self.lbl_mensaje.configure(text=f"✔️ Ticket #{ticket['id']} cargado exitosamente.", text_color="#10B981")
        self.focus_codigo()

    def descartar_venta_espera(self, ticket, callback_refrescar):
        self.ventas_en_espera = [v for v in self.ventas_en_espera if v["id"] != ticket["id"]]
        self.actualizar_indicador_espera()
        callback_refrescar()

    # --- MODAL DE PAGO ---
    def abrir_modal_pago(self):
        # Validar si la caja está abierta antes de cobrar (sólo el Admin puede saltarlo)
        rol = getattr(self.app_ref, "rol_actual", "cajero") if self.app_ref else "cajero"
        caja = self.db.get_caja_abierta()
        if not caja and rol != "admin":
            self.lbl_mensaje.configure(text="❌ Caja cerrada. Es obligatorio abrir caja para cobrar.", text_color="#EF4444")
            if self.app_ref:
                self.app_ref.show_view("cash")
            return

        if not self.carrito:
            self.lbl_mensaje.configure(text="❌ El carrito está vacío.", text_color="#EF4444")
            return

        total_venta = sum(item[6] for item in self.carrito)

        modal = ctk.CTkToplevel(self)
        modal.title("💳 Procesar Pago y Vuelto")
        modal.geometry("420x500")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="Finalizar Venta", font=("Segoe UI", 18, "bold"), text_color="#F8FAFC").pack(pady=(15, 5))
        ctk.CTkLabel(modal, text=f"Total a Pagar: ${int(total_venta):,}", font=("Segoe UI", 22, "bold"), text_color="#10B981").pack(pady=(0, 15))

        ctk.CTkLabel(modal, text="Selecciona Medio de Pago:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=35, pady=(2, 0))
        combo_pago = ctk.CTkOptionMenu(
            modal, 
            values=["Efectivo", "Tarjeta (Débito/Crédito)", "Transferencia"], 
            width=350, height=36, font=("Segoe UI", 13, "bold")
        )
        combo_pago.pack(padx=35, pady=5)

        frame_efectivo = ctk.CTkFrame(modal, fg_color="#0F172A", corner_radius=10)
        frame_efectivo.pack(fill="x", padx=35, pady=10)

        ctk.CTkLabel(frame_efectivo, text="Paga con ($):", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=15, pady=(10, 0))

        def solo_numeros(P):
            return P == "" or P.isdigit()

        vcmd = (modal.register(solo_numeros), '%P')

        entry_pagado = ctk.CTkEntry(
            frame_efectivo, 
            placeholder_text=str(int(total_venta)), 
            font=("Segoe UI", 16, "bold"), 
            width=320,
            validate="key",
            validatecommand=vcmd
        )
        entry_pagado.pack(padx=15, pady=5)
        entry_pagado.insert(0, str(int(total_venta)))
        entry_pagado.focus_set()

        lbl_vuelto = ctk.CTkLabel(frame_efectivo, text="VUELTO: $0", font=("Segoe UI", 20, "bold"), text_color="#10B981")
        lbl_vuelto.pack(pady=10)

        def calcular_vuelto(event=None):
            if combo_pago.get() != "Efectivo":
                lbl_vuelto.configure(text="VUELTO: $0", text_color="#10B981")
                return
            try:
                txt = entry_pagado.get().strip()
                pagado = float(txt) if txt else total_venta
                vuelto = pagado - total_venta
                if vuelto >= 0:
                    lbl_vuelto.configure(text=f"VUELTO: ${int(vuelto):,}", text_color="#10B981")
                else:
                    lbl_vuelto.configure(text=f"Falta: ${int(abs(vuelto)):,}", text_color="#EF4444")
            except ValueError:
                lbl_vuelto.configure(text="VUELTO: $0", text_color="#F59E0B")

        entry_pagado.bind("<KeyRelease>", calcular_vuelto)

        def on_pago_change(choice):
            if choice == "Efectivo":
                frame_efectivo.pack(fill="x", padx=35, pady=10)
            else:
                frame_efectivo.pack_forget()

        combo_pago.configure(command=on_pago_change)

        def confirmar_finalizacion():
            medio = combo_pago.get()
            monto_pagado = total_venta
            vuelto_entregado = 0.0

            if medio == "Efectivo":
                try:
                    txt = entry_pagado.get().strip()
                    monto_pagado = float(txt) if txt else total_venta
                    if monto_pagado < total_venta:
                        return
                    vuelto_entregado = monto_pagado - total_venta
                except ValueError:
                    return

            cajero_actual = getattr(self.app_ref, "usuario_actual", "Cajero")
            
            items_db = []
            for item in self.carrito:
                pid, cod, nom, pcosto, pventa, cant, sub = item
                real_pid = None if str(pid).startswith("otros_") else pid
                items_db.append((real_pid, cod, nom, pcosto, pventa, cant, sub))

            exito, msg = self.db.registrar_venta(
                items_db, 
                total_venta, 
                medio_pago=medio, 
                cajero_nombre=cajero_actual,
                monto_pagado=monto_pagado,
                vuelto=vuelto_entregado
            )
            
            if exito:
                self.lbl_mensaje.configure(text="✅ Venta Completada con Éxito", text_color="#10B981")
                self.carrito = []
                self.actualizar_tabla_carrito()
                modal.destroy()
                self.focus_codigo()

        btn_confirmar = ctk.CTkButton(
            modal, text="✔️ CONFIRMAR VENTA", command=confirmar_finalizacion, 
            fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 15, "bold"), height=45, width=350
        )
        btn_confirmar.pack(pady=15)

    def vaciar_carrito(self):
        self.carrito = []
        self.actualizar_tabla_carrito()
        self.lbl_mensaje.configure(text="Carrito vaciado.", text_color="#F59E0B")
        self.focus_codigo()
