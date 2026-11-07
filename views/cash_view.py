import customtkinter as ctk
from datetime import datetime

class CashView(ctk.CTkFrame):
    def __init__(self, parent, db, app_reference=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.app_ref = app_reference
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

    def cargar_caja(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        resumen = self.db.get_resumen_caja()

        if not resumen or resumen["estado"] != "Abierta":
            self.render_caja_cerrada()
        else:
            self.render_caja_abierta(resumen)

    # --- VISTA 1: CAJA CERRADA (FORMULARIO DE APERTURA) ---
    def render_caja_cerrada(self):
        usuario_actual = getattr(self.app_ref, "usuario_actual", "Cajero") if self.app_ref else "Cajero"

        center_scroll = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        center_scroll.pack(fill="both", expand=True)

        card_apertura = ctk.CTkFrame(center_scroll, fg_color="#1E293B", corner_radius=14, width=500)
        card_apertura.pack(pady=(20, 20), padx=40)

        ctk.CTkLabel(card_apertura, text="🔒 CONTROL DE CAJA", font=("Segoe UI", 20, "bold"), text_color="#38BDF8").pack(pady=(25, 5))
        ctk.CTkLabel(
            card_apertura, 
            text="La caja se encuentra cerrada actualmente.\nIngresa el monto de dinero base (cambio / sencillo) para abrir el turno.",
            font=("Segoe UI", 12), text_color="#94A3B8", justify="center"
        ).pack(pady=(0, 15), padx=25)

        info_box = ctk.CTkFrame(card_apertura, fg_color="#0F172A", corner_radius=8)
        info_box.pack(fill="x", padx=35, pady=5)
        ctk.CTkLabel(info_box, text=f"👤 Usuario Responsable: {usuario_actual}", font=("Segoe UI", 12, "bold"), text_color="#F8FAFC").pack(pady=8)

        ctk.CTkLabel(card_apertura, text="Monto Base Inicial en Efectivo ($):", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=35, pady=(15, 2))
        
        entry_monto_ini = ctk.CTkEntry(
            card_apertura, 
            placeholder_text="Ej: 30000", 
            fg_color="#0F172A", 
            font=("Segoe UI", 16, "bold"), 
            justify="center",
            height=42
        )
        entry_monto_ini.pack(fill="x", padx=35, pady=4)
        entry_monto_ini.insert(0, "0")
        entry_monto_ini.focus_set()

        lbl_error = ctk.CTkLabel(card_apertura, text="", font=("Segoe UI", 11), text_color="#EF4444")
        lbl_error.pack(pady=4)

        def ejecutar_apertura():
            txt = entry_monto_ini.get().strip()
            try:
                monto = float(txt) if txt else 0.0
                if monto < 0: raise ValueError
            except ValueError:
                lbl_error.configure(text="❌ Ingresa un monto numérico válido (mayor o igual a 0).")
                return

            exito, msg = self.db.abrir_caja(monto, usuario_actual)
            if exito:
                if getattr(self.app_ref, "caja_obligatoria", False):
                    self.app_ref.desbloquear_caja_obligatoria()
                else:
                    self.cargar_caja()
            else:
                lbl_error.configure(text=f"❌ {msg}")

        entry_monto_ini.bind("<Return>", lambda e: ejecutar_apertura())

        btn_abrir = ctk.CTkButton(
            card_apertura, text="🟢 ABRIR CAJA / INICIAR TURNO", command=ejecutar_apertura,
            fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 14, "bold"), height=45
        )
        btn_abrir.pack(fill="x", padx=35, pady=(10, 10))

        # Si es Administrador, permitir saltarse la apertura de caja
        rol_actual = getattr(self.app_ref, "rol_actual", "cajero") if self.app_ref else "cajero"
        if rol_actual == "admin":
            btn_saltar = ctk.CTkButton(
                card_apertura, text="⏩ Continuar sin abrir caja (Admin)", command=lambda: self.app_ref.show_view("pos"),
                fg_color="#334155", hover_color="#475569", font=("Segoe UI", 11), height=30
            )
            btn_saltar.pack(fill="x", padx=35, pady=(0, 20))
        else:
            card_apertura.pack_configure(pady=(20, 20))

        # Tabla de Historial de Cierres Previos
        self.render_historial_cierres(center_scroll)

    # --- VISTA 2: CAJA ABIERTA (PANEL DE CONTROL, MOVIMIENTOS Y ARQUEO) ---
    def render_caja_abierta(self, resumen):
        usuario_actual = getattr(self.app_ref, "usuario_actual", "Cajero") if self.app_ref else "Cajero"

        scroll_caja = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll_caja.pack(fill="both", expand=True)

        # Barra Superior de Estado
        header_bar = ctk.CTkFrame(scroll_caja, fg_color="#1E293B", corner_radius=10)
        header_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header_bar, text="🟢 CAJA ACTIVA (Turno en Curso)", font=("Segoe UI", 16, "bold"), text_color="#10B981"
        ).pack(side="left", padx=15, pady=12)

        info_turno = f"Apertura: {resumen['fecha_apertura']} | Responsable: {resumen['usuario_apertura']}"
        ctk.CTkLabel(header_bar, text=info_turno, font=("Segoe UI", 11), text_color="#94A3B8").pack(side="right", padx=15, pady=12)

        # Fila 1 de Tarjetas KPI
        cards_frame = ctk.CTkFrame(scroll_caja, fg_color="transparent")
        cards_frame.pack(fill="x", pady=5)

        def make_kpi(parent, title, val, subtext="", color="#F8FAFC"):
            f = ctk.CTkFrame(parent, fg_color="#1E293B", corner_radius=10)
            f.pack(side="left", expand=True, fill="both", padx=4)
            ctk.CTkLabel(f, text=title, font=("Segoe UI", 11), text_color="#94A3B8").pack(pady=(10, 2))
            ctk.CTkLabel(f, text=val, font=("Segoe UI", 18, "bold"), text_color=color).pack(pady=(0, 2))
            if subtext:
                ctk.CTkLabel(f, text=subtext, font=("Segoe UI", 10), text_color="#64748B").pack(pady=(0, 8))
            return f

        make_kpi(cards_frame, "Fondo Inicial", f"${int(resumen['monto_inicial']):,}", "Base en efectivo")
        make_kpi(cards_frame, "Ventas en Efectivo (+)", f"${int(resumen['ventas_efectivo']):,}", "Cobros en caja", "#10B981")
        make_kpi(cards_frame, "Entradas de Dinero (+)", f"${int(resumen['entradas']):,}", "Aportes manuales", "#38BDF8")
        make_kpi(cards_frame, "Salidas / Egresos (-)", f"${int(resumen['salidas']):,}", "Gastos caja chica", "#EF4444")

        # Fila 2 de Tarjetas: Destacado Efectivo Esperado en Cajón
        fila2 = ctk.CTkFrame(scroll_caja, fg_color="transparent")
        fila2.pack(fill="x", pady=6)

        c_destacada = ctk.CTkFrame(fila2, fg_color="#0F172A", border_color="#10B981", border_width=2, corner_radius=10)
        c_destacada.pack(side="left", expand=True, fill="both", padx=4)
        ctk.CTkLabel(c_destacada, text="💵 EFECTIVO ESPERADO EN CAJÓN FÍSICO", font=("Segoe UI", 12, "bold"), text_color="#38BDF8").pack(pady=(12, 2))
        ctk.CTkLabel(c_destacada, text=f"${int(resumen['efectivo_esperado']):,}", font=("Segoe UI", 26, "bold"), text_color="#10B981").pack(pady=(0, 2))
        ctk.CTkLabel(c_destacada, text="Monto Inicial + Ventas Efectivo + Entradas - Salidas", font=("Segoe UI", 10), text_color="#94A3B8").pack(pady=(0, 10))

        c_otros = ctk.CTkFrame(fila2, fg_color="#1E293B", corner_radius=10)
        c_otros.pack(side="left", expand=True, fill="both", padx=4)
        ctk.CTkLabel(c_otros, text="💳 Ventas Tarjeta / Transferencia", font=("Segoe UI", 12, "bold"), text_color="#F59E0B").pack(pady=(12, 2))
        ctk.CTkLabel(c_otros, text=f"${int(resumen['ventas_otros']):,}", font=("Segoe UI", 22, "bold"), text_color="#F8FAFC").pack(pady=(0, 2))
        ctk.CTkLabel(c_otros, text="Dinero recibido en banco (fuera de cajón)", font=("Segoe UI", 10), text_color="#64748B").pack(pady=(0, 10))

        # Botones de Acción
        actions_bar = ctk.CTkFrame(scroll_caja, fg_color="#1E293B", corner_radius=10)
        actions_bar.pack(fill="x", pady=10)

        ctk.CTkButton(
            actions_bar, text="➕ Registrar Entrada de Dinero", height=38,
            fg_color="#2563EB", hover_color="#1D4ED8", font=("Segoe UI", 12, "bold"),
            command=lambda: self.abrir_modal_movimiento(resumen["sesion_id"], "Entrada")
        ).pack(side="left", padx=12, pady=10)

        ctk.CTkButton(
            actions_bar, text="➖ Registrar Salida de Dinero (Gasto)", height=38,
            fg_color="#D97706", hover_color="#B45309", font=("Segoe UI", 12, "bold"),
            command=lambda: self.abrir_modal_movimiento(resumen["sesion_id"], "Salida")
        ).pack(side="left", padx=4, pady=10)

        ctk.CTkButton(
            actions_bar, text="🔒 Realizar Cierre de Caja (Arqueo)", height=38,
            fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 12, "bold"),
            command=lambda: self.abrir_modal_cierre(resumen)
        ).pack(side="right", padx=12, pady=10)

        # Tabla de Movimientos de la Sesión Actual
        ctk.CTkLabel(scroll_caja, text="📋 Movimientos Manuales del Turno Actual (Entradas y Salidas)", font=("Segoe UI", 13, "bold"), text_color="#F8FAFC").pack(anchor="w", pady=(10, 4))

        movs_frame = ctk.CTkFrame(scroll_caja, fg_color="#1E293B", corner_radius=10)
        movs_frame.pack(fill="both", expand=True, pady=4)

        h_row = ctk.CTkFrame(movs_frame, fg_color="#0F172A")
        h_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(h_row, text="Hora", width=120, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h_row, text="Tipo", width=100, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h_row, text="Monto", width=100, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h_row, text="Motivo / Justificación", width=240, font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(h_row, text="Registrado Por", width=120, font=("Segoe UI", 11, "bold")).pack(side="left")

        if not resumen["movimientos"]:
            ctk.CTkLabel(movs_frame, text="No hay entradas ni salidas manuales registradas en este turno.", font=("Segoe UI", 11), text_color="#64748B").pack(pady=15)
        else:
            for m in resumen["movimientos"]:
                # m: id, tipo, monto, motivo, fecha_hora, usuario
                _, m_tipo, m_monto, m_motivo, m_fecha, m_user = m
                row = ctk.CTkFrame(movs_frame, fg_color="#0F172A", corner_radius=6)
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(row, text=m_fecha, width=120, font=("Segoe UI", 10)).pack(side="left")
                
                color_tipo = "#10B981" if m_tipo == "Entrada" else "#EF4444"
                ctk.CTkLabel(row, text=m_tipo, width=100, font=("Segoe UI", 11, "bold"), text_color=color_tipo).pack(side="left")
                
                prefijo = "+" if m_tipo == "Entrada" else "-"
                ctk.CTkLabel(row, text=f"{prefijo}${int(m_monto):,}", width=100, font=("Segoe UI", 11, "bold"), text_color=color_tipo).pack(side="left")
                ctk.CTkLabel(row, text=m_motivo, width=240, font=("Segoe UI", 11), anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(row, text=m_user, width=120, font=("Segoe UI", 11, "bold"), text_color="#38BDF8").pack(side="left")

        # Historial de Turnos Pasados
        self.render_historial_cierres(scroll_caja)

    # --- MODAL: REGISTRAR ENTRADA / SALIDA ---
    def abrir_modal_movimiento(self, sesion_id, tipo):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Registro de {tipo} de Dinero")
        modal.geometry("400x380")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        color_tipo = "#10B981" if tipo == "Entrada" else "#EF4444"
        ctk.CTkLabel(modal, text=f"{'➕' if tipo == 'Entrada' else '➖'} Registrar {tipo} de Efectivo", font=("Segoe UI", 16, "bold"), text_color=color_tipo).pack(pady=(20, 10))

        usuario_actual = getattr(self.app_ref, "usuario_actual", "Cajero") if self.app_ref else "Cajero"
        ctk.CTkLabel(modal, text=f"Registrado por: 👤 {usuario_actual}", font=("Segoe UI", 11, "bold"), text_color="#94A3B8").pack(pady=(0, 10))

        ctk.CTkLabel(modal, text="Monto en Efectivo ($):", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=35, pady=(5, 2))
        entry_monto = ctk.CTkEntry(modal, placeholder_text="Ej: 15000", fg_color="#0F172A", width=330, font=("Segoe UI", 14, "bold"))
        entry_monto.pack(padx=35, pady=4)
        entry_monto.focus_set()

        ctk.CTkLabel(modal, text="Motivo o Justificación:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=35, pady=(5, 2))
        placeholder_motivo = "Ej: Aporte de cambio" if tipo == "Entrada" else "Ej: Pago proveedor panadería"
        entry_motivo = ctk.CTkEntry(modal, placeholder_text=placeholder_motivo, fg_color="#0F172A", width=330)
        entry_motivo.pack(padx=35, pady=4)

        lbl_err = ctk.CTkLabel(modal, text="", font=("Segoe UI", 11), text_color="#EF4444")
        lbl_err.pack(pady=4)

        def guardar():
            try:
                monto = float(entry_monto.get().strip())
                if monto <= 0: raise ValueError
            except ValueError:
                lbl_err.configure(text="❌ Ingresa un monto numérico mayor a 0.")
                return

            motivo = entry_motivo.get().strip()
            if not motivo:
                lbl_err.configure(text="❌ Ingresa el motivo del movimiento.")
                return

            exito, msg = self.db.registrar_movimiento_caja(sesion_id, tipo, monto, motivo, usuario_actual)
            if exito:
                modal.destroy()
                self.cargar_caja()
            else:
                lbl_err.configure(text=f"❌ {msg}")

        btn_conf = ctk.CTkButton(
            modal, text=f"Confirmar {tipo}", command=guardar,
            fg_color=color_tipo, hover_color="#059669" if tipo == "Entrada" else "#DC2626",
            font=("Segoe UI", 13, "bold"), height=38, width=330
        )
        btn_conf.pack(pady=15)

    # --- MODAL: ARQUEO Y CIERRE DE CAJA ---
    def abrir_modal_cierre(self, resumen):
        modal = ctk.CTkToplevel(self)
        modal.title("🔒 Arqueo y Cierre de Turno de Caja")
        modal.geometry("440x520")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="🔒 Cierre de Turno / Arqueo", font=("Segoe UI", 18, "bold"), text_color="#EF4444").pack(pady=(18, 5))
        
        usuario_actual = getattr(self.app_ref, "usuario_actual", "Cajero") if self.app_ref else "Cajero"
        ctk.CTkLabel(modal, text=f"Cajero responsable: 👤 {usuario_actual}", font=("Segoe UI", 11, "bold"), text_color="#94A3B8").pack(pady=(0, 10))

        # Tarjeta Efectivo Esperado
        box_esp = ctk.CTkFrame(modal, fg_color="#0F172A", corner_radius=8)
        box_esp.pack(fill="x", padx=30, pady=5)
        ctk.CTkLabel(box_esp, text="Efectivo Esperado por Sistema:", font=("Segoe UI", 11), text_color="#94A3B8").pack(pady=(8, 2))
        ctk.CTkLabel(box_esp, text=f"${int(resumen['efectivo_esperado']):,}", font=("Segoe UI", 22, "bold"), text_color="#38BDF8").pack(pady=(0, 8))

        ctk.CTkLabel(modal, text="Dinero Físico Real Contado en Cajón ($):", font=("Segoe UI", 11, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=30, pady=(10, 2))
        entry_real = ctk.CTkEntry(modal, placeholder_text="Ingresa el dinero físico total contado...", fg_color="#0F172A", width=380, font=("Segoe UI", 16, "bold"), justify="center")
        entry_real.pack(padx=30, pady=4)
        entry_real.focus_set()

        lbl_dif = ctk.CTkLabel(modal, text="Diferencia: $0 (Exacto)", font=("Segoe UI", 13, "bold"), text_color="#10B981")
        lbl_dif.pack(pady=6)

        def calcular_diferencia(event=None):
            try:
                txt = entry_real.get().strip()
                real = float(txt) if txt else 0.0
                dif = real - resumen["efectivo_esperado"]
                if dif == 0:
                    lbl_dif.configure(text="Diferencia: $0 (Cuadre Exacto ✔️)", text_color="#10B981")
                elif dif > 0:
                    lbl_dif.configure(text=f"Diferencia: +${int(dif):,} (Sobrante de dinero)", text_color="#38BDF8")
                else:
                    lbl_dif.configure(text=f"Diferencia: -${int(abs(dif)):,} (Faltante de dinero ⚠️)", text_color="#EF4444")
            except ValueError:
                lbl_dif.configure(text="Ingresa un monto numérico válido", text_color="#F59E0B")

        entry_real.bind("<KeyRelease>", calcular_diferencia)

        ctk.CTkLabel(modal, text="Observaciones / Comentarios del cierre:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=30, pady=(6, 2))
        entry_obs = ctk.CTkEntry(modal, placeholder_text="Ej: Todo cuadrado sin novedades...", fg_color="#0F172A", width=380)
        entry_obs.pack(padx=30, pady=4)

        lbl_error = ctk.CTkLabel(modal, text="", font=("Segoe UI", 11), text_color="#EF4444")
        lbl_error.pack(pady=2)

        def confirmar_cierre():
            try:
                real_monto = float(entry_real.get().strip())
                if real_monto < 0: raise ValueError
            except ValueError:
                lbl_error.configure(text="❌ Ingresa el dinero contado correctamente.")
                return

            obs = entry_obs.get().strip()
            exito, msg = self.db.cerrar_caja(resumen["sesion_id"], real_monto, usuario_actual, obs)
            if exito:
                modal.destroy()
                self.cargar_caja()
            else:
                lbl_error.configure(text=f"❌ {msg}")

        btn_cierre_def = ctk.CTkButton(
            modal, text="🔒 CONFIRMAR Y CERRAR TURNO", command=confirmar_cierre,
            fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 13, "bold"), height=42, width=380
        )
        btn_cierre_def.pack(pady=12)

    # --- HISTORIAL DE AUDITORÍA DE CIERRES ANTERIORES ---
    def render_historial_cierres(self, parent):
        ctk.CTkLabel(parent, text="📜 Historial de Turnos de Caja Pasados", font=("Segoe UI", 13, "bold"), text_color="#F8FAFC").pack(anchor="w", pady=(15, 4))

        hist_frame = ctk.CTkFrame(parent, fg_color="#1E293B", corner_radius=10)
        hist_frame.pack(fill="x", pady=4)

        h_row = ctk.CTkFrame(hist_frame, fg_color="#0F172A")
        h_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(h_row, text="ID", width=40, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h_row, text="Apertura", width=120, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h_row, text="Cierre", width=120, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h_row, text="Cajero Cierre", width=110, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h_row, text="Esperado", width=85, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h_row, text="Real", width=85, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h_row, text="Diferencia", width=95, font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h_row, text="Estado", width=75, font=("Segoe UI", 11, "bold")).pack(side="left")

        cierres = self.db.get_historial_cajas(limite=15)
        cierres_pasados = [c for c in cierres if c[9] == "Cerrada"]

        if not cierres_pasados:
            ctk.CTkLabel(hist_frame, text="No hay cierres de caja registrados todavía.", font=("Segoe UI", 11), text_color="#64748B").pack(pady=15)
            return

        for c in cierres_pasados:
            c_id, u_ap, f_ap, m_ini, u_ci, f_ci, esp, real, dif, est, obs = c
            row = ctk.CTkFrame(hist_frame, fg_color="#0F172A", corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=f"#{c_id}", width=40, font=("Segoe UI", 11, "bold")).pack(side="left")
            ctk.CTkLabel(row, text=f_ap[:16] if f_ap else "-", width=120, font=("Segoe UI", 10)).pack(side="left")
            ctk.CTkLabel(row, text=f_ci[:16] if f_ci else "-", width=120, font=("Segoe UI", 10)).pack(side="left")
            ctk.CTkLabel(row, text=u_ci or u_ap, width=110, font=("Segoe UI", 11, "bold"), text_color="#38BDF8").pack(side="left")
            ctk.CTkLabel(row, text=f"${int(esp):,}", width=85, font=("Segoe UI", 10)).pack(side="left")
            ctk.CTkLabel(row, text=f"${int(real):,}", width=85, font=("Segoe UI", 10, "bold")).pack(side="left")

            color_dif = "#10B981" if dif == 0 else ("#38BDF8" if dif > 0 else "#EF4444")
            signo = "+" if dif > 0 else ""
            ctk.CTkLabel(row, text=f"{signo}${int(dif):,}", width=95, font=("Segoe UI", 11, "bold"), text_color=color_dif).pack(side="left")
            ctk.CTkLabel(row, text="Cerrada", width=75, font=("Segoe UI", 10), text_color="#64748B").pack(side="left")
