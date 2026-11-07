import customtkinter as ctk

class InventoryView(ctk.CTkFrame):
    def __init__(self, parent, db, app_reference=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.app_ref = app_reference
        self.editing_id = None
        self.filtro_critico = False
        self.vista_actual = "catalogo"  # "catalogo" o "kardex"
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # --- FORMULARIO IZQUIERDO ---
        form_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12)
        form_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

        self.lbl_titulo = ctk.CTkLabel(form_frame, text="➕ Nuevo Producto", font=("Segoe UI", 16, "bold"), text_color="#F8FAFC")
        self.lbl_titulo.pack(pady=(15, 10))

        # Botón Carga Rápida de Stock (Kardex de Entrada)
        btn_carga_rapida = ctk.CTkButton(
            form_frame, text="📥 Carga Rápida de Stock (+)", 
            command=self.abrir_modal_carga_rapida, fg_color="#2563EB", hover_color="#1D4ED8", font=("Segoe UI", 12, "bold"),
            height=36
        )
        btn_carga_rapida.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(form_frame, text="Código de Barras:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=20, pady=(2,0))
        self.entry_codigo = ctk.CTkEntry(form_frame, placeholder_text="Escanea o escribe código", fg_color="#0F172A")
        self.entry_codigo.pack(fill="x", padx=20, pady=4)
        self.entry_codigo.bind("<KeyRelease>", self.al_cambiar_codigo)

        # Frame de alerta si el código ya existe
        self.frame_alerta_existente = ctk.CTkFrame(form_frame, fg_color="#331A15", corner_radius=8, border_color="#EF4444", border_width=1)
        self.lbl_alerta_existente = ctk.CTkLabel(
            self.frame_alerta_existente, 
            text="⚠️ Este código ya existe.", 
            font=("Segoe UI", 11, "bold"), 
            text_color="#F87171",
            wraplength=210,
            justify="left"
        )
        self.lbl_alerta_existente.pack(padx=10, pady=(6, 2), anchor="w")

        self.btn_accion_carga_rapida = ctk.CTkButton(
            self.frame_alerta_existente, 
            text="📥 Abrir Carga Rápida (+)", 
            font=("Segoe UI", 11, "bold"),
            fg_color="#D97706", 
            hover_color="#B45309", 
            height=28,
            command=self.ir_a_carga_rapida_desde_alerta
        )
        self.btn_accion_carga_rapida.pack(padx=10, pady=(2, 8), fill="x")

        # Frame de sugerencia si el producto existe en Open Food Facts
        self.frame_sug_maestro = ctk.CTkFrame(form_frame, fg_color="#0F2D37", corner_radius=8, border_color="#0EA5E9", border_width=1)
        self.lbl_sug_maestro = ctk.CTkLabel(
            self.frame_sug_maestro, 
            text="", 
            font=("Segoe UI", 11, "bold"), 
            text_color="#38BDF8",
            wraplength=210,
            justify="left"
        )
        self.lbl_sug_maestro.pack(padx=10, pady=(6, 2), anchor="w")

        self.btn_usar_sug = ctk.CTkButton(
            self.frame_sug_maestro, 
            text="✔️ Usar Nombre Sugerido", 
            font=("Segoe UI", 11, "bold"),
            fg_color="#0284C7", 
            hover_color="#0369A1", 
            height=28,
            command=self.aplicar_sugerencia_maestro
        )
        self.btn_usar_sug.pack(padx=10, pady=(2, 8), fill="x")

        ctk.CTkLabel(form_frame, text="Nombre del Producto:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=20, pady=(2,0))
        self.entry_nombre = ctk.CTkEntry(form_frame, placeholder_text="Ej: Arroz 1kg", fg_color="#0F172A")
        self.entry_nombre.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(form_frame, text="Precio Costo ($):", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=20, pady=(2,0))
        self.entry_costo = ctk.CTkEntry(form_frame, placeholder_text="Ej: 700", fg_color="#0F172A")
        self.entry_costo.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(form_frame, text="Precio Venta ($):", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=20, pady=(2,0))
        self.entry_precio = ctk.CTkEntry(form_frame, placeholder_text="Ej: 1200", fg_color="#0F172A")
        self.entry_precio.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(form_frame, text="Stock Inicial:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=20, pady=(2,0))
        self.entry_stock = ctk.CTkEntry(form_frame, placeholder_text="Ej: 50", fg_color="#0F172A")
        self.entry_stock.pack(fill="x", padx=20, pady=4)

        self.lbl_estado = ctk.CTkLabel(form_frame, text="", font=("Segoe UI", 12))
        self.lbl_estado.pack(pady=4)

        self.btn_guardar = ctk.CTkButton(form_frame, text="Guardar Producto", command=self.guardar, fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 13, "bold"), height=36)
        self.btn_guardar.pack(fill="x", padx=20, pady=4)

        self.btn_cancelar = ctk.CTkButton(form_frame, text="Cancelar Edición", command=self.limpiar_form, fg_color="#475569", hover_color="#334155")
        
        # --- PANEL DERECHO CON PESTAÑAS (CATÁLOGO vs KARDEX) ---
        right_container = ctk.CTkFrame(self, fg_color="transparent")
        right_container.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        right_container.grid_columnconfigure(0, weight=1)
        right_container.grid_rowconfigure(1, weight=1)

        # Barra Superior de Navegación de Inventario
        self.top_nav = ctk.CTkFrame(right_container, fg_color="#1E293B", corner_radius=10)
        self.top_nav.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # Selector de Vista: Catálogo / Kardex
        nav_buttons = ctk.CTkFrame(self.top_nav, fg_color="transparent")
        nav_buttons.pack(side="left", padx=10, pady=6)

        self.btn_tab_catalogo = ctk.CTkButton(
            nav_buttons, text="📦 Catálogo de Productos", width=160, height=32,
            fg_color="#2563EB", hover_color="#1D4ED8", font=("Segoe UI", 11, "bold"),
            command=lambda: self.cambiar_vista("catalogo")
        )
        self.btn_tab_catalogo.pack(side="left", padx=4)

        self.btn_tab_kardex = ctk.CTkButton(
            nav_buttons, text="📋 Historial de Carga (Kardex)", width=190, height=32,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 11, "bold"),
            command=lambda: self.cambiar_vista("kardex")
        )
        self.btn_tab_kardex.pack(side="left", padx=4)

        # Filtros para el Catálogo (se muestran sólo en vista catálogo)
        self.frame_filtros_catalogo = ctk.CTkFrame(self.top_nav, fg_color="transparent")
        self.frame_filtros_catalogo.pack(side="right", padx=10, pady=6)

        self.btn_f_todos = ctk.CTkButton(self.frame_filtros_catalogo, text="Todos", width=70, height=30, fg_color="#2563EB", command=lambda: self.set_filtro(False))
        self.btn_f_todos.pack(side="right", padx=3)

        self.btn_f_critico = ctk.CTkButton(self.frame_filtros_catalogo, text="⚠️ Stock Crítico (≤ 5)", width=130, height=30, fg_color="#334155", command=lambda: self.set_filtro(True))
        self.btn_f_critico.pack(side="right", padx=3)

        # Contenedor con Scroll para las Tablas
        self.table_frame = ctk.CTkScrollableFrame(right_container, fg_color="#1E293B")
        self.table_frame.grid(row=1, column=0, sticky="nsew")

        self.cargar_productos()

    def al_cambiar_codigo(self, event=None):
        cod = self.entry_codigo.get().strip()
        if not cod:
            self.frame_alerta_existente.pack_forget()
            self.frame_sug_maestro.pack_forget()
            if self.editing_id is None:
                self.btn_guardar.configure(state="normal", fg_color="#10B981", text="Guardar Producto")
            return

        prod = self.db.get_producto_por_codigo(cod)

        if self.editing_id is None:
            # Modo creación de nuevo producto
            if prod:
                # El código ya existe en catálogo
                self.frame_sug_maestro.pack_forget()
                self.lbl_alerta_existente.configure(text=f"⚠️ Código ya existe:\n'{prod[2]}'\n(Stock actual: {prod[5]})")
                self.frame_alerta_existente.pack(after=self.entry_codigo, fill="x", padx=20, pady=4)
                self.btn_guardar.configure(state="disabled", fg_color="#475569", text="⚠️ Código ya Registrado")
                self.lbl_estado.configure(text="❌ Usa Carga Rápida para sumar stock.", text_color="#F59E0B")
            else:
                self.frame_alerta_existente.pack_forget()
                self.btn_guardar.configure(state="normal", fg_color="#10B981", text="Guardar Producto")
                self.lbl_estado.configure(text="")

                # Consultar en catálogo maestro Open Food Facts
                sug = self.db.buscar_en_catalogo_maestro(cod)
                if sug:
                    self.sugerencia_activa = sug["nombre"]
                    self.lbl_sug_maestro.configure(text=f"💡 Open Food Facts:\n'{sug['nombre']}'")
                    self.frame_sug_maestro.pack(after=self.entry_codigo, fill="x", padx=20, pady=4)
                else:
                    self.frame_sug_maestro.pack_forget()
        else:
            # Modo edición: si el código pertenece a OTRO producto
            self.frame_sug_maestro.pack_forget()
            if prod and prod[0] != self.editing_id:
                self.lbl_alerta_existente.configure(text=f"⚠️ Código en uso por:\n'{prod[2]}'")
                self.frame_alerta_existente.pack(after=self.entry_codigo, fill="x", padx=20, pady=4)
                self.btn_guardar.configure(state="disabled", fg_color="#475569", text="⚠️ Código en uso")
            else:
                self.frame_alerta_existente.pack_forget()
                self.btn_guardar.configure(state="normal", fg_color="#F59E0B", text="💾 Actualizar Cambios")

    def aplicar_sugerencia_maestro(self):
        if hasattr(self, "sugerencia_activa") and self.sugerencia_activa:
            self.entry_nombre.delete(0, "end")
            self.entry_nombre.insert(0, self.sugerencia_activa)
            self.frame_sug_maestro.pack_forget()
            self.entry_costo.focus_set()

    def ir_a_carga_rapida_desde_alerta(self):
        cod = self.entry_codigo.get().strip()
        self.abrir_modal_carga_rapida(codigo_inicial=cod)

    def cambiar_vista(self, nueva_vista):
        self.vista_actual = nueva_vista
        if nueva_vista == "catalogo":
            self.btn_tab_catalogo.configure(fg_color="#2563EB")
            self.btn_tab_kardex.configure(fg_color="#334155")
            self.frame_filtros_catalogo.pack(side="right", padx=10, pady=6)
            self.cargar_productos()
        else:
            self.btn_tab_catalogo.configure(fg_color="#334155")
            self.btn_tab_kardex.configure(fg_color="#2563EB")
            self.frame_filtros_catalogo.pack_forget()
            self.cargar_historial_kardex()

    def set_filtro(self, es_critico):
        self.filtro_critico = es_critico
        self.btn_f_todos.configure(fg_color="#334155" if es_critico else "#2563EB")
        self.btn_f_critico.configure(fg_color="#EF4444" if es_critico else "#334155")
        self.cargar_productos()

    # --- REQUERIMIENTO 4: CARGA RÁPIDA DE STOCK (KARDEX) ---
    def abrir_modal_carga_rapida(self, codigo_inicial=None):
        modal = ctk.CTkToplevel(self)
        modal.title("📥 Carga Rápida de Stock (Kardex de Entradas)")
        modal.geometry("440x480")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="📥 Cargar Unidades Entrantes", font=("Segoe UI", 16, "bold"), text_color="#38BDF8").pack(pady=(18, 5))
        
        usuario_actual = getattr(self.app_ref, "usuario_actual", "Administrador") if self.app_ref else "Administrador"
        ctk.CTkLabel(modal, text=f"Registrado por: 👤 {usuario_actual}", font=("Segoe UI", 11, "bold"), text_color="#F59E0B").pack(pady=(0, 10))

        ctk.CTkLabel(modal, text="Escanea o escribe el código de barras:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=35, pady=(2,0))
        entry_code = ctk.CTkEntry(modal, placeholder_text="Código de barras...", fg_color="#0F172A", width=370)
        entry_code.pack(padx=35, pady=4)

        lbl_info_prod = ctk.CTkLabel(modal, text="Escribe un código para verificar producto y stock actual", font=("Segoe UI", 11), text_color="#F59E0B")
        lbl_info_prod.pack(pady=4)

        ctk.CTkLabel(modal, text="Cantidad de unidades recibidas (+):", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=35, pady=(2,0))
        entry_cant = ctk.CTkEntry(modal, placeholder_text="Ej: 24", fg_color="#0F172A", width=370, font=("Segoe UI", 14, "bold"))
        entry_cant.pack(padx=35, pady=4)

        ctk.CTkLabel(modal, text="Precio Costo Unitario ($):", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=35, pady=(2,0))
        entry_costo_unit = ctk.CTkEntry(modal, placeholder_text="Costo por unidad de esta carga", fg_color="#0F172A", width=370)
        entry_costo_unit.pack(padx=35, pady=4)

        ctk.CTkLabel(modal, text="Motivo del Reabastecimiento:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=35, pady=(2,0))
        combo_motivo = ctk.CTkComboBox(
            modal, 
            values=["Reabastecimiento", "Compra a Proveedor", "Ajuste de Inventario", "Devolución Proveedor"], 
            width=370, 
            fg_color="#0F172A"
        )
        combo_motivo.pack(padx=35, pady=4)
        combo_motivo.set("Reabastecimiento")

        prod_encontrado = [None]

        def buscar_prod(event=None):
            c = entry_code.get().strip()
            if not c:
                return
            p = self.db.get_producto_por_codigo(c)
            if p:
                prod_encontrado[0] = p
                lbl_info_prod.configure(text=f"✔️ {p[2]} (Stock actual: {p[5]} | Costo reg: ${int(p[3]):,})", text_color="#10B981")
                if not entry_costo_unit.get().strip():
                    entry_costo_unit.insert(0, str(int(p[3])))
            else:
                prod_encontrado[0] = None
                lbl_info_prod.configure(text="❌ Producto no existe en catálogo.", text_color="#EF4444")

        entry_code.bind("<KeyRelease>", buscar_prod)

        # Si se pasó un código inicial, pre-cargarlo
        if codigo_inicial:
            entry_code.insert(0, codigo_inicial)
            buscar_prod()
            entry_cant.focus_set()
        else:
            entry_code.focus_set()

        def sumar():
            if not prod_encontrado[0]:
                lbl_info_prod.configure(text="❌ Debes seleccionar un producto válido.", text_color="#EF4444")
                return
            try:
                cant = int(entry_cant.get().strip())
                if cant <= 0: raise ValueError
            except ValueError:
                lbl_info_prod.configure(text="❌ Ingresa una cantidad válida mayor a 0.", text_color="#EF4444")
                return

            costo_unitario = 0.0
            try:
                c_str = entry_costo_unit.get().strip()
                if c_str:
                    costo_unitario = float(c_str)
                    if costo_unitario < 0: raise ValueError
                else:
                    costo_unitario = float(prod_encontrado[0][3])
            except ValueError:
                lbl_info_prod.configure(text="❌ Costo unitario inválido.", text_color="#EF4444")
                return

            motivo = combo_motivo.get().strip() or "Reabastecimiento"

            self.db.registrar_carga_stock(
                producto_id=prod_encontrado[0][0],
                cantidad=cant,
                precio_costo_unitario=costo_unitario,
                usuario_nombre=usuario_actual,
                motivo=motivo
            )

            modal.destroy()
            self.limpiar_form()
            if self.vista_actual == "catalogo":
                self.cargar_productos()
            else:
                self.cargar_historial_kardex()

        ctk.CTkButton(
            modal, text="➕ Confirmar Carga y Registrar en Kardex", command=sumar, 
            fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 13, "bold"), height=42, width=370
        ).pack(pady=15)

    # --- REQUERIMIENTO 4: VISUALIZACIÓN DE KARDEX DE ENTRADAS ---
    def cargar_historial_kardex(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        registros = self.db.get_historial_stock(limite=100)

        headers_frame = ctk.CTkFrame(self.table_frame, fg_color="#0F172A")
        headers_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(headers_frame, text="Fecha y Hora", width=140, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(headers_frame, text="Código", width=95, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(headers_frame, text="Producto", width=150, font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Cant. (+)", width=75, font=("Segoe UI", 11, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(headers_frame, text="Costo Unit.", width=85, font=("Segoe UI", 11, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(headers_frame, text="Motivo", width=110, font=("Segoe UI", 11, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(headers_frame, text="Usuario / Cargado Por", width=130, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)

        if not registros:
            ctk.CTkLabel(
                self.table_frame, 
                text="No hay registros de carga de stock en el kardex aún.", 
                font=("Segoe UI", 12), 
                text_color="#64748B"
            ).pack(pady=30)
            return

        for reg in registros:
            r_id, f_hora, cod, nombre, cant, costo, usuario, motivo = reg
            row = ctk.CTkFrame(self.table_frame, fg_color="#0F172A", corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=f_hora, width=140, font=("Segoe UI", 10)).pack(side="left")
            ctk.CTkLabel(row, text=cod, width=95, font=("Segoe UI", 11), text_color="#94A3B8").pack(side="left")
            ctk.CTkLabel(row, text=nombre, width=150, anchor="w", font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"+{cant}", width=75, font=("Segoe UI", 12, "bold"), text_color="#10B981").pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"${int(costo):,}", width=85, font=("Segoe UI", 11)).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=motivo or "Reabastecimiento", width=110, font=("Segoe UI", 10), text_color="#F59E0B").pack(side="left", padx=2)
            ctk.CTkLabel(row, text=usuario, width=130, font=("Segoe UI", 11, "bold"), text_color="#38BDF8").pack(side="left", padx=5)

    # --- CATÁLOGO DE PRODUCTOS ---
    def guardar(self):
        cod = self.entry_codigo.get().strip()
        nombre = self.entry_nombre.get().strip()
        costo_str = self.entry_costo.get().strip()
        precio_str = self.entry_precio.get().strip()
        stock_str = self.entry_stock.get().strip()

        if not (cod and nombre and costo_str and precio_str and stock_str):
            self.lbl_estado.configure(text="❌ Completa todos los campos.", text_color="#EF4444")
            return

        try:
            p_costo = float(costo_str)
            p_venta = float(precio_str)
            stock = int(stock_str)
        except ValueError:
            self.lbl_estado.configure(text="❌ Números inválidos.", text_color="#EF4444")
            return

        exito, msg = self.db.guardar_producto(cod, nombre, p_costo, p_venta, stock, prod_id=self.editing_id)
        if not exito:
            self.lbl_estado.configure(text=f"❌ {msg}", text_color="#EF4444")
            return

        self.lbl_estado.configure(text=f"✅ {msg}", text_color="#10B981")
        self.limpiar_form()
        if self.vista_actual == "catalogo":
            self.cargar_productos()
        else:
            self.cargar_historial_kardex()

    def iniciar_edicion(self, prod):
        prod_id, cod, nombre, p_costo, p_venta, stock = prod
        self.editing_id = prod_id
        self.frame_alerta_existente.pack_forget()
        self.frame_sug_maestro.pack_forget()

        self.entry_codigo.delete(0, "end")
        self.entry_codigo.insert(0, cod)

        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, nombre)

        self.entry_costo.delete(0, "end")
        self.entry_costo.insert(0, str(int(p_costo)))

        self.entry_precio.delete(0, "end")
        self.entry_precio.insert(0, str(int(p_venta)))

        self.entry_stock.delete(0, "end")
        self.entry_stock.insert(0, str(stock))

        self.lbl_titulo.configure(text="✏️ Modificar Producto", text_color="#F59E0B")
        self.btn_guardar.configure(state="normal", text="💾 Actualizar Cambios", fg_color="#F59E0B", hover_color="#D97706")
        self.btn_cancelar.pack(fill="x", padx=20, pady=4)

    def eliminar(self, prod_id, nombre):
        self.db.eliminar_producto(prod_id)
        self.lbl_estado.configure(text=f"🗑️ Eliminado '{nombre}'", text_color="#F59E0B")
        if self.editing_id == prod_id:
            self.limpiar_form()
        self.cargar_productos()

    def limpiar_form(self):
        self.editing_id = None
        self.frame_alerta_existente.pack_forget()
        self.frame_sug_maestro.pack_forget()
        self.entry_codigo.delete(0, "end")
        self.entry_nombre.delete(0, "end")
        self.entry_costo.delete(0, "end")
        self.entry_precio.delete(0, "end")
        self.entry_stock.delete(0, "end")
        
        self.lbl_titulo.configure(text="➕ Nuevo Producto", text_color="#F8FAFC")
        self.btn_guardar.configure(state="normal", text="Guardar Producto", fg_color="#10B981", hover_color="#059669")
        self.btn_cancelar.pack_forget()

    def cargar_productos(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        productos = self.db.get_todos_productos(filtro_critico=self.filtro_critico)

        headers_frame = ctk.CTkFrame(self.table_frame, fg_color="#0F172A")
        headers_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(headers_frame, text="Código", width=100, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(headers_frame, text="Producto", width=140, font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="P. Costo", width=70, font=("Segoe UI", 11, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(headers_frame, text="P. Venta", width=70, font=("Segoe UI", 11, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(headers_frame, text="Stock", width=60, font=("Segoe UI", 11, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(headers_frame, text="Acciones", width=90, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)

        for prod in productos:
            prod_id, cod, nombre, p_costo, p_venta, stock = prod
            row = ctk.CTkFrame(self.table_frame, fg_color="#0F172A", corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=cod, width=100, anchor="w", font=("Segoe UI", 11)).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=nombre, width=140, anchor="w", font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"${int(p_costo):,}", width=70).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"${int(p_venta):,}", width=70, font=("Segoe UI", 11, "bold"), text_color="#10B981").pack(side="left", padx=2)
            
            color_stock = "#EF4444" if stock <= 3 else ("#F59E0B" if stock <= 5 else "#10B981")
            ctk.CTkLabel(row, text=str(stock), width=60, text_color=color_stock, font=("Segoe UI", 12, "bold")).pack(side="left", padx=2)

            acc_frame = ctk.CTkFrame(row, fg_color="transparent")
            acc_frame.pack(side="left", padx=5)

            btn_edit = ctk.CTkButton(acc_frame, text="✏️", width=30, height=24, fg_color="#F59E0B", hover_color="#D97706",
                                     command=lambda p=prod: self.iniciar_edicion(p))
            btn_edit.pack(side="left", padx=2)

            btn_del = ctk.CTkButton(acc_frame, text="🗑️", width=30, height=24, fg_color="#EF4444", hover_color="#DC2626",
                                     command=lambda pid=prod_id, n=nombre: self.eliminar(pid, n))
            btn_del.pack(side="left", padx=2)
