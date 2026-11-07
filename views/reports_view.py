import customtkinter as ctk

class ReportsView(ctk.CTkFrame):
    def __init__(self, parent, db, app_reference=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.app_ref = app_reference
        self.periodo_actual = "todos"
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_dashboard = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_dashboard.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.frame_dashboard.grid_columnconfigure(0, weight=1)
        self.frame_dashboard.grid_rowconfigure(2, weight=1)

    def cargar_reporte(self):
        self.cargar_dashboard()

    def cambiar_periodo(self, nuevo_periodo):
        self.periodo_actual = nuevo_periodo
        self.cargar_dashboard()

    # --- REQUERIMIENTO 1: MODAL DE DETALLE DE VENTA ---
    def abrir_modal_detalle(self, venta_id):
        venta = self.db.get_venta_por_id(venta_id)
        if not venta:
            return

        v_id, fecha, total, medio, cajero, pagado, vuelto, estado = venta
        items = self.db.get_detalle_venta(venta_id)

        modal = ctk.CTkToplevel(self)
        modal.title(f"🧾 Detalle de Venta #{v_id}")
        modal.geometry("540x580")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        # Encabezado
        top_frame = ctk.CTkFrame(modal, fg_color="transparent")
        top_frame.pack(fill="x", padx=25, pady=(20, 10))

        ctk.CTkLabel(
            top_frame, 
            text=f"Transacción #{v_id}", 
            font=("Segoe UI", 20, "bold"), 
            text_color="#38BDF8"
        ).pack(side="left")

        color_estado = "#10B981" if estado == "Completada" else "#EF4444"
        badge_estado = ctk.CTkLabel(
            top_frame,
            text=f"  {estado.upper()}  ",
            font=("Segoe UI", 11, "bold"),
            fg_color=color_estado,
            text_color="#FFFFFF",
            corner_radius=6
        )
        badge_estado.pack(side="right")

        # Ficha Informativa
        info_frame = ctk.CTkFrame(modal, fg_color="#0F172A", corner_radius=10)
        info_frame.pack(fill="x", padx=25, pady=5)
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(info_frame, text=f"📅 Fecha: {fecha}", font=("Segoe UI", 11), text_color="#94A3B8").grid(row=0, column=0, sticky="w", padx=15, pady=(10, 4))
        ctk.CTkLabel(info_frame, text=f"👤 Cajero: {cajero}", font=("Segoe UI", 11, "bold"), text_color="#F8FAFC").grid(row=0, column=1, sticky="w", padx=15, pady=(10, 4))

        ctk.CTkLabel(info_frame, text=f"💳 Medio de Pago: {medio}", font=("Segoe UI", 11), text_color="#F59E0B").grid(row=1, column=0, sticky="w", padx=15, pady=(2, 4))
        ctk.CTkLabel(info_frame, text=f"💵 Pagado: ${int(pagado):,}", font=("Segoe UI", 11), text_color="#94A3B8").grid(row=1, column=1, sticky="w", padx=15, pady=(2, 4))

        ctk.CTkLabel(info_frame, text=f"🪙 Vuelto entregado: ${int(vuelto):,}", font=("Segoe UI", 11), text_color="#10B981").grid(row=2, column=0, sticky="w", padx=15, pady=(2, 10))
        ctk.CTkLabel(info_frame, text=f"💰 Total Venta: ${int(total):,}", font=("Segoe UI", 13, "bold"), text_color="#10B981").grid(row=2, column=1, sticky="w", padx=15, pady=(2, 10))

        # Tabla de Productos
        ctk.CTkLabel(modal, text="📦 Productos Comprados:", font=("Segoe UI", 13, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=25, pady=(12, 4))

        items_table = ctk.CTkScrollableFrame(modal, fg_color="#0F172A", corner_radius=10, height=200)
        items_table.pack(fill="both", expand=True, padx=25, pady=5)

        # Headers tabla items
        h_row = ctk.CTkFrame(items_table, fg_color="#1E293B", corner_radius=6)
        h_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(h_row, text="Producto", width=190, font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", padx=8)
        ctk.CTkLabel(h_row, text="Cant.", width=50, font=("Segoe UI", 11, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(h_row, text="P. Unit.", width=90, font=("Segoe UI", 11, "bold")).pack(side="left", padx=4)
        ctk.CTkLabel(h_row, text="Subtotal", width=90, font=("Segoe UI", 11, "bold")).pack(side="left", padx=4)

        for it in items:
            _, _, nom_item, cant, _, p_unit, sub = it
            it_row = ctk.CTkFrame(items_table, fg_color="#1E293B", corner_radius=6)
            it_row.pack(fill="x", pady=2)

            ctk.CTkLabel(it_row, text=nom_item, width=190, anchor="w", font=("Segoe UI", 11)).pack(side="left", padx=8)
            ctk.CTkLabel(it_row, text=str(cant), width=50, font=("Segoe UI", 11, "bold")).pack(side="left", padx=4)
            ctk.CTkLabel(it_row, text=f"${int(p_unit):,}", width=90).pack(side="left", padx=4)
            ctk.CTkLabel(it_row, text=f"${int(sub):,}", width=90, font=("Segoe UI", 11, "bold"), text_color="#10B981").pack(side="left", padx=4)

        # Botones inferiores del modal
        bot_frame = ctk.CTkFrame(modal, fg_color="transparent")
        bot_frame.pack(fill="x", padx=25, pady=15)

        if estado != "Anulada":
            btn_anular_modal = ctk.CTkButton(
                bot_frame, text="🗑️ Anular Venta", width=140, height=36,
                fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 12, "bold"),
                command=lambda: [modal.destroy(), self.abrir_modal_anular(venta_id, total)]
            )
            btn_anular_modal.pack(side="left")

        btn_cerrar = ctk.CTkButton(
            bot_frame, text="Cerrar", width=100, height=36,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 12),
            command=modal.destroy
        )
        btn_cerrar.pack(side="right")

    # --- REQUERIMIENTO 2: ANULACIONES CON SEGURIDAD DE ADMINISTRADOR ---
    def abrir_modal_anular(self, venta_id, total_venta):
        modal = ctk.CTkToplevel(self)
        modal.title(f"⚠️ Confirmar Anulación de Venta #{venta_id}")
        modal.geometry("400x340")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="⚠️ Anular Transacción", font=("Segoe UI", 16, "bold"), text_color="#EF4444").pack(pady=(20, 5))
        
        ctk.CTkLabel(
            modal, 
            text=f"¿Estás seguro de anular la Venta #{venta_id} por ${int(total_venta):,}?\n\nEsta acción sumará las unidades de regreso\nal stock y actualizará las métricas financieras.",
            font=("Segoe UI", 11),
            text_color="#94A3B8",
            justify="center"
        ).pack(padx=25, pady=5)

        ctk.CTkLabel(
            modal, 
            text="Requiere Contraseña de Administrador:", 
            font=("Segoe UI", 11, "bold"), 
            text_color="#F8FAFC"
        ).pack(anchor="w", padx=35, pady=(15, 2))

        entry_admin_pw = ctk.CTkEntry(
            modal, 
            show="*", 
            placeholder_text="Contraseña de Administrador", 
            fg_color="#0F172A", 
            width=330,
            font=("Segoe UI", 13)
        )
        entry_admin_pw.pack(padx=35, pady=4)
        entry_admin_pw.focus_set()

        lbl_error = ctk.CTkLabel(modal, text="", font=("Segoe UI", 11), text_color="#EF4444")
        lbl_error.pack(pady=4)

        def ejecutar_anulacion():
            pwd = entry_admin_pw.get().strip()
            clave_esperada = getattr(self.app_ref, "CLAVE_ADMIN", "1234") if self.app_ref else "1234"

            if pwd != clave_esperada:
                lbl_error.configure(text="❌ Contraseña de Administrador incorrecta.")
                return

            exito, msg = self.db.anular_venta(venta_id)
            if exito:
                modal.destroy()
                self.cargar_dashboard()
            else:
                lbl_error.configure(text=f"❌ {msg}")

        entry_admin_pw.bind("<Return>", lambda e: ejecutar_anulacion())

        btn_confirmar = ctk.CTkButton(
            modal, text="Confirmar Anulación y Devolver Stock", command=ejecutar_anulacion,
            fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 12, "bold"), height=38, width=330
        )
        btn_confirmar.pack(pady=10)

        btn_cancelar = ctk.CTkButton(
            modal, text="Cancelar", command=modal.destroy,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 11), width=100
        )
        btn_cancelar.pack(pady=2)

    def cargar_dashboard(self):
        for widget in self.frame_dashboard.winfo_children():
            widget.destroy()

        datos = self.db.get_dashboard_metricas(periodo=self.periodo_actual)

        # BARRA SUPERIOR
        top_bar = ctk.CTkFrame(self.frame_dashboard, fg_color="#1E293B", corner_radius=10)
        top_bar.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(top_bar, text="📊 Dashboard Financiero", font=("Segoe UI", 18, "bold"), text_color="#F8FAFC").pack(side="left", padx=15, pady=10)

        filtros_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        filtros_frame.pack(side="right", padx=10, pady=5)

        opciones_filtros = [("Hoy", "hoy"), ("Esta Semana", "semana"), ("Este Mes", "mes"), ("Histórico", "todos")]

        for texto, clave in opciones_filtros:
            es_activo = (self.periodo_actual == clave)
            btn_f = ctk.CTkButton(
                filtros_frame, text=texto, width=85, height=32,
                fg_color="#2563EB" if es_activo else "#334155",
                hover_color="#1D4ED8" if es_activo else "#475569",
                font=("Segoe UI", 11, "bold" if es_activo else "normal"),
                command=lambda k=clave: self.cambiar_periodo(k)
            )
            btn_f.pack(side="left", padx=3)

        # KPI CARDS
        cards_frame = ctk.CTkFrame(self.frame_dashboard, fg_color="transparent")
        cards_frame.pack(fill="x", pady=10)

        c1 = ctk.CTkFrame(cards_frame, fg_color="#1E293B", corner_radius=10)
        c1.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(c1, text="Ventas Totales", font=("Segoe UI", 13), text_color="#94A3B8").pack(pady=(15, 2))
        ctk.CTkLabel(c1, text=f"${int(datos['total_ventas']):,}", font=("Segoe UI", 22, "bold"), text_color="#F8FAFC").pack(pady=(0, 2))
        ctk.CTkLabel(c1, text=f"{datos['cant_ventas']} transacciones activas", font=("Segoe UI", 11), text_color="#64748B").pack(pady=(0, 12))

        c2 = ctk.CTkFrame(cards_frame, fg_color="#1E293B", corner_radius=10)
        c2.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(c2, text="Costo de Mercadería", font=("Segoe UI", 13), text_color="#94A3B8").pack(pady=(15, 2))
        ctk.CTkLabel(c2, text=f"${int(datos['costo_total']):,}", font=("Segoe UI", 22, "bold"), text_color="#EF4444").pack(pady=(0, 2))
        ctk.CTkLabel(c2, text="Inversión en productos", font=("Segoe UI", 11), text_color="#64748B").pack(pady=(0, 12))

        c3 = ctk.CTkFrame(cards_frame, fg_color="#1E293B", corner_radius=10)
        c3.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(c3, text="GANANCIA NETA REAL", font=("Segoe UI", 13, "bold"), text_color="#10B981").pack(pady=(15, 2))
        ctk.CTkLabel(c3, text=f"${int(datos['ganancia_neta']):,}", font=("Segoe UI", 24, "bold"), text_color="#10B981").pack(pady=(0, 2))
        ctk.CTkLabel(c3, text="Ventas - Costos", font=("Segoe UI", 11), text_color="#64748B").pack(pady=(0, 12))

        # HISTORIAL DE TRANSACCIONES
        table_frame = ctk.CTkScrollableFrame(
            self.frame_dashboard, 
            label_text=f"📜 Historial de Transacciones ({self.periodo_actual.capitalize()})", 
            label_font=("Segoe UI", 13, "bold"), 
            fg_color="#1E293B"
        )
        table_frame.pack(fill="both", expand=True, pady=5)

        header = ctk.CTkFrame(table_frame, fg_color="#0F172A")
        header.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header, text="ID", width=55, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(header, text="Fecha y Hora", width=145, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(header, text="Cajero", width=100, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(header, text="Medio Pago", width=110, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(header, text="Total", width=95, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(header, text="Estado", width=95, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(header, text="Acciones", width=120, font=("Segoe UI", 11, "bold")).pack(side="left")

        if not datos["ventas_recientes"]:
            ctk.CTkLabel(table_frame, text="No hay ventas registradas.", font=("Segoe UI", 12), text_color="#64748B").pack(pady=20)
            return

        for v in datos["ventas_recientes"]:
            # v contiene: id, fecha, total, medio_pago, cajero_nombre, estado
            v_id, fecha, total, medio, cajero, estado = v
            es_anulada = (estado == "Anulada")

            row_bg = "#151F30" if es_anulada else "#0F172A"
            row = ctk.CTkFrame(table_frame, fg_color=row_bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            id_color = "#64748B" if es_anulada else "#F8FAFC"
            ctk.CTkLabel(row, text=f"#{v_id}", width=55, font=("Segoe UI", 11, "bold"), text_color=id_color).pack(side="left")
            ctk.CTkLabel(row, text=fecha, width=145, text_color="#94A3B8" if es_anulada else "#CBD5E1").pack(side="left")
            ctk.CTkLabel(row, text=cajero, width=100, font=("Segoe UI", 11, "bold"), text_color="#64748B" if es_anulada else "#38BDF8").pack(side="left")
            ctk.CTkLabel(row, text=medio, width=110, text_color="#64748B" if es_anulada else "#F59E0B").pack(side="left")
            
            total_color = "#64748B" if es_anulada else "#10B981"
            ctk.CTkLabel(row, text=f"${int(total):,}", width=95, font=("Segoe UI", 12, "bold"), text_color=total_color).pack(side="left")

            # Columna Estado
            color_badge = "#EF4444" if es_anulada else "#10B981"
            lbl_est = ctk.CTkLabel(
                row, text=estado, width=95, font=("Segoe UI", 11, "bold"), text_color=color_badge
            )
            lbl_est.pack(side="left")

            # Acciones Frame
            acc_frame = ctk.CTkFrame(row, fg_color="transparent", width=120)
            acc_frame.pack(side="left", padx=5)

            # Botón Ver Detalle
            btn_det = ctk.CTkButton(
                acc_frame, text="👁️ Detalle", width=68, height=26,
                fg_color="#2563EB", hover_color="#1D4ED8", font=("Segoe UI", 10, "bold"),
                command=lambda vid=v_id: self.abrir_modal_detalle(vid)
            )
            btn_det.pack(side="left", padx=2)

            # Botón Anular
            if not es_anulada:
                btn_anular = ctk.CTkButton(
                    acc_frame, text="🗑️", width=34, height=26,
                    fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 10, "bold"),
                    command=lambda vid=v_id, tot=total: self.abrir_modal_anular(vid, tot)
                )
                btn_anular.pack(side="left", padx=2)
            else:
                lbl_bloq = ctk.CTkLabel(acc_frame, text="🚫", width=34, font=("Segoe UI", 11), text_color="#64748B")
                lbl_bloq.pack(side="left", padx=2)
