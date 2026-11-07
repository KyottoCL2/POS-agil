import customtkinter as ctk
import database as db
from views.pos_view import POSView
from views.cash_view import CashView
from views.inventory_view import InventoryView
from views.reports_view import ReportsView

class PuntoAgilApp(ctk.CTk):
    CLAVE_ADMIN = "1234"

    def __init__(self):
        super().__init__()

        self.title("Punto Ágil - Sistema POS")
        self.geometry("1120x700")
        self.minsize(980, 620)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        db.init_db()

        self.rol_actual = None
        self.usuario_actual = ""
        self.caja_obligatoria = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.iniciar_pantalla_login()

    def iniciar_pantalla_login(self):
        self.frame_login = ctk.CTkFrame(self, fg_color="#0F172A")
        self.frame_login.grid(row=0, column=0, sticky="nsew")
        self.frame_login.grid_columnconfigure(0, weight=1)
        self.frame_login.grid_columnconfigure(1, weight=1)
        self.frame_login.grid_rowconfigure(0, weight=1)

        # --- TARJETA IZQUIERDA ---
        card_login = ctk.CTkFrame(self.frame_login, fg_color="#1E293B", corner_radius=16, width=420)
        card_login.grid(row=0, column=0, padx=(40, 20), pady=40, sticky="e")

        ctk.CTkLabel(card_login, text="⚡ PUNTO ÁGIL", font=("Segoe UI", 26, "bold"), text_color="#38BDF8").pack(pady=(25, 5))
        ctk.CTkLabel(card_login, text="Selecciona tu perfil de acceso:", font=("Segoe UI", 13), text_color="#94A3B8").pack(pady=(0, 15))

        self.tab_login = ctk.CTkTabview(card_login, width=340, height=270)
        self.tab_login.pack(padx=20, pady=(0, 15))
        
        tab_cajero = self.tab_login.add("🧑‍💻 Cajero")
        tab_admin = self.tab_login.add("🔒 Administrador")

        # --- TAB CAJERO ---
        ctk.CTkLabel(tab_cajero, text="Selecciona tu Perfil:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", pady=(5, 2))
        
        self.cajeros_data = db.get_cajeros()
        nombres_cajeros = [c[1] for c in self.cajeros_data] if self.cajeros_data else ["Sin Cajeros Registrados"]

        self.combo_cajeros = ctk.CTkComboBox(
            tab_cajero, 
            values=nombres_cajeros, 
            width=280, 
            font=("Segoe UI", 13)
        )
        self.combo_cajeros.pack(pady=4)

        ctk.CTkLabel(tab_cajero, text="Contraseña de Cajero:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", pady=(5, 2))
        self.entry_pass_cajero = ctk.CTkEntry(tab_cajero, show="*", width=280, font=("Segoe UI", 13), fg_color="#0F172A")
        self.entry_pass_cajero.pack(pady=4)
        self.entry_pass_cajero.bind("<Return>", lambda e: self.ingresar_cajero())

        self.lbl_err_cajero = ctk.CTkLabel(tab_cajero, text="", font=("Segoe UI", 11), text_color="#EF4444")
        self.lbl_err_cajero.pack(pady=2)

        btn_entrar_cajero = ctk.CTkButton(
            tab_cajero, text="Ingresar al Sistema", 
            command=self.ingresar_cajero, fg_color="#10B981", hover_color="#059669", 
            font=("Segoe UI", 13, "bold"), height=36, width=280
        )
        btn_entrar_cajero.pack(pady=8)

        frame_acciones_cajero = ctk.CTkFrame(tab_cajero, fg_color="transparent")
        frame_acciones_cajero.pack(fill="x", pady=5)

        btn_crear = ctk.CTkButton(
            frame_acciones_cajero, text="➕ Crear Perfil", width=135, height=28,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 11),
            command=self.abrir_modal_crear_cajero
        )
        btn_crear.pack(side="left", padx=5)

        btn_eliminar = ctk.CTkButton(
            frame_acciones_cajero, text="🗑️ Eliminar Perfil", width=135, height=28,
            fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 11),
            command=self.abrir_modal_eliminar_cajero
        )
        btn_eliminar.pack(side="right", padx=5)

        # --- TAB ADMIN ---
        ctk.CTkLabel(tab_admin, text="Ingresa contraseña de Administrador:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", pady=(15, 2))
        self.entry_pass_admin = ctk.CTkEntry(tab_admin, show="*", width=280, font=("Segoe UI", 14), justify="center", fg_color="#0F172A")
        self.entry_pass_admin.pack(pady=5)
        self.entry_pass_admin.bind("<Return>", lambda e: self.ingresar_admin())

        self.lbl_err_admin = ctk.CTkLabel(tab_admin, text="", font=("Segoe UI", 11), text_color="#EF4444")
        self.lbl_err_admin.pack(pady=5)

        btn_entrar_admin = ctk.CTkButton(
            tab_admin, text="Ingresar como Administrador", 
            command=self.ingresar_admin, fg_color="#2563EB", hover_color="#1D4ED8", 
            font=("Segoe UI", 13, "bold"), height=38, width=280
        )
        btn_entrar_admin.pack(pady=15)

        # --- TARJETA DERECHA: AVATAR ---
        card_perfil = ctk.CTkFrame(self.frame_login, fg_color="#1E293B", corner_radius=16, width=320, height=380)
        card_perfil.grid(row=0, column=1, padx=(20, 40), pady=40, sticky="w")
        card_perfil.pack_propagate(False)

        ctk.CTkLabel(card_perfil, text="VISTA PREVIA DEL PERFIL", font=("Segoe UI", 11, "bold"), text_color="#64748B").pack(pady=(25, 15))

        avatar_box = ctk.CTkFrame(card_perfil, width=140, height=140, corner_radius=70, fg_color="#334155")
        avatar_box.pack(pady=10)
        avatar_box.pack_propagate(False)

        lbl_avatar_icon = ctk.CTkLabel(avatar_box, text="👤", font=("Segoe UI", 64), text_color="#94A3B8")
        lbl_avatar_icon.pack(expand=True)

        self.lbl_nombre_avatar = ctk.CTkLabel(card_perfil, text="", font=("Segoe UI", 22, "bold"), text_color="#38BDF8")
        self.lbl_nombre_avatar.pack(pady=(15, 5))

        ctk.CTkLabel(card_perfil, text="Rol: Cajero Operativo", font=("Segoe UI", 11), text_color="#10B981").pack(pady=(0, 20))

        def actualizar_avatar(choice=None):
            nombre = self.combo_cajeros.get().strip() or "Cajero"
            self.lbl_nombre_avatar.configure(text=nombre.title())

        self.combo_cajeros.configure(command=actualizar_avatar)
        actualizar_avatar()

    def recargar_lista_cajeros(self):
        self.cajeros_data = db.get_cajeros()
        nombres = [c[1] for c in self.cajeros_data] if self.cajeros_data else ["Sin Cajeros Registrados"]
        self.combo_cajeros.configure(values=nombres)
        if nombres:
            self.combo_cajeros.set(nombres[0])
            self.lbl_nombre_avatar.configure(text=nombres[0].title())

    def ingresar_cajero(self):
        nombre = self.combo_cajeros.get().strip()
        pwd = self.entry_pass_cajero.get().strip()

        if not self.cajeros_data or nombre == "Sin Cajeros Registrados":
            self.lbl_err_cajero.configure(text="❌ Crea un perfil primero.")
            return

        if db.verificar_cajero_password(nombre, pwd):
            self.rol_actual = "cajero"
            self.usuario_actual = nombre.title()
            
            # Comprobar si hay caja abierta. Si no, obligar a abrir caja
            caja = db.get_caja_abierta()
            self.caja_obligatoria = (caja is None)

            self.frame_login.destroy()
            self.inicializar_app_principal()

            if self.caja_obligatoria:
                self.bloquear_por_caja_obligatoria()
        else:
            self.lbl_err_cajero.configure(text="❌ Contraseña de cajero incorrecta.")

    def ingresar_admin(self):
        clave = self.entry_pass_admin.get()
        if clave == self.CLAVE_ADMIN:
            self.rol_actual = "admin"
            self.usuario_actual = "Administrador"
            self.caja_obligatoria = False  # El Administrador no está obligado a abrir caja para usar el sistema
            self.frame_login.destroy()
            self.inicializar_app_principal()
        else:
            self.lbl_err_admin.configure(text="❌ Clave incorrecta (Defecto: 1234)")

    def bloquear_por_caja_obligatoria(self):
        self.btn_pos.configure(state="disabled", fg_color="#1E293B", text_color="#64748B")
        self.btn_inv.configure(state="disabled", fg_color="#1E293B", text_color="#64748B")
        self.show_view("cash")

    def desbloquear_caja_obligatoria(self):
        self.caja_obligatoria = False
        self.btn_pos.configure(state="normal", text_color="#FFFFFF")
        self.btn_inv.configure(state="normal", text_color="#FFFFFF")
        self.show_view("pos")

    def abrir_modal_crear_cajero(self):
        modal = ctk.CTkToplevel(self)
        modal.title("➕ Crear Nuevo Perfil de Cajero")
        modal.geometry("360x320")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="🧑‍💻 Nuevo Cajero", font=("Segoe UI", 16, "bold"), text_color="#38BDF8").pack(pady=(20, 10))

        ctk.CTkLabel(modal, text="Nombre del Cajero(a):", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=30, pady=(2, 0))
        entry_nom = ctk.CTkEntry(modal, placeholder_text="Ej: Antonella", fg_color="#0F172A", width=300)
        entry_nom.pack(padx=30, pady=4)
        entry_nom.focus_set()

        ctk.CTkLabel(modal, text="Asignar Contraseña:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=30, pady=(2, 0))
        entry_pw = ctk.CTkEntry(modal, show="*", placeholder_text="Contraseña personal", fg_color="#0F172A", width=300)
        entry_pw.pack(padx=30, pady=4)

        lbl_msg = ctk.CTkLabel(modal, text="", font=("Segoe UI", 11), text_color="#EF4444")
        lbl_msg.pack(pady=4)

        def guardar():
            nom = entry_nom.get().strip()
            pw = entry_pw.get().strip()
            if not nom or not pw:
                lbl_msg.configure(text="❌ Completa nombre y contraseña.")
                return

            exito, m = db.crear_cajero(nom, pw)
            if exito:
                self.recargar_lista_cajeros()
                modal.destroy()
            else:
                lbl_msg.configure(text=f"❌ {m}")

        ctk.CTkButton(modal, text="Guardar Perfil", command=guardar, fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 13, "bold"), height=36, width=300).pack(pady=15)

    def abrir_modal_eliminar_cajero(self):
        modal = ctk.CTkToplevel(self)
        modal.title("🗑️ Eliminar Perfil de Cajero")
        modal.geometry("360x340")
        modal.resizable(False, False)
        modal.configure(fg_color="#1E293B")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="⚠️ Confirmación de Administrador", font=("Segoe UI", 14, "bold"), text_color="#EF4444").pack(pady=(15, 5))
        ctk.CTkLabel(modal, text="Selecciona el perfil a eliminar e ingresa\nla clave del Administrador:", font=("Segoe UI", 11), text_color="#94A3B8").pack(pady=(0, 10))

        nombres = [c[1] for c in self.cajeros_data] if self.cajeros_data else []
        combo_del = ctk.CTkComboBox(modal, values=nombres if nombres else ["Ninguno"], width=300)
        combo_del.pack(pady=5)

        ctk.CTkLabel(modal, text="Clave del Administrador:", font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w", padx=30, pady=(5, 0))
        entry_admin_pw = ctk.CTkEntry(modal, show="*", placeholder_text="Clave (1234)", fg_color="#0F172A", width=300)
        entry_admin_pw.pack(pady=5)

        lbl_msg = ctk.CTkLabel(modal, text="", font=("Segoe UI", 11), text_color="#EF4444")
        lbl_msg.pack(pady=2)

        def confirmar_borrado():
            nom_borrar = combo_del.get()
            admin_pw = entry_admin_pw.get().strip()

            if admin_pw != self.CLAVE_ADMIN:
                lbl_msg.configure(text="❌ Clave de Administrador incorrecta.")
                return

            if not nom_borrar or nom_borrar == "Ninguno":
                lbl_msg.configure(text="❌ Selecciona un perfil válido.")
                return

            db.eliminar_cajero(nom_borrar)
            self.recargar_lista_cajeros()
            modal.destroy()

        ctk.CTkButton(modal, text="Eliminar Definitivamente", command=confirmar_borrado, fg_color="#EF4444", hover_color="#DC2626", font=("Segoe UI", 13, "bold"), height=36, width=300).pack(pady=15)

    # --- APP PRINCIPAL ---
    def inicializar_app_principal(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()

        self.container = ctk.CTkFrame(self, fg_color="#0F172A")
        self.container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.views = {
            "pos": POSView(self.container, db, self),
            "cash": CashView(self.container, db, self),
            "inventory": InventoryView(self.container, db, self),
            "reports": ReportsView(self.container, db, self)
        }

        for name, view in self.views.items():
            view.grid(row=0, column=0, sticky="nsew")
            view.grid_remove()

        if self.caja_obligatoria and self.rol_actual != "admin":
            self.show_view("cash")
        else:
            self.show_view("pos")

    def setup_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color="#1E293B")
        sidebar.grid(row=0, column=0, sticky="nsew")

        lbl_logo = ctk.CTkLabel(sidebar, text="⚡ PUNTO ÁGIL", font=("Segoe UI", 20, "bold"), text_color="#38BDF8")
        lbl_logo.pack(pady=(20, 5))

        lbl_user = ctk.CTkLabel(sidebar, text=f"👤 {self.usuario_actual}", font=("Segoe UI", 12, "bold"), text_color="#F59E0B")
        lbl_user.pack(pady=(0, 20))

        # BOTÓN PUNTO DE VENTA
        self.btn_pos = ctk.CTkButton(
            sidebar, text="🛒 Punto de Venta", command=lambda: self.show_view("pos"), 
            height=40, font=("Segoe UI", 13, "bold"), fg_color="#2563EB", hover_color="#1D4ED8", corner_radius=8
        )
        self.btn_pos.pack(fill="x", padx=15, pady=5)

        # BOTÓN CONTROL DE CAJA
        self.btn_cash = ctk.CTkButton(
            sidebar, text="💰 Control de Caja", command=lambda: self.show_view("cash"), 
            height=40, font=("Segoe UI", 13, "bold"), fg_color="#334155", hover_color="#475569", corner_radius=8
        )
        self.btn_cash.pack(fill="x", padx=15, pady=5)

        # BOTÓN INVENTARIO (ACCESIBLE PARA AMBOS)
        self.btn_inv = ctk.CTkButton(
            sidebar, text="📦 Inventario", command=lambda: self.show_view("inventory"), 
            height=40, font=("Segoe UI", 13, "bold"), fg_color="#334155", hover_color="#475569", corner_radius=8
        )
        self.btn_inv.pack(fill="x", padx=15, pady=5)

        # REPORTES VISIBLE SOLO PARA ADMINISTRADOR
        if self.rol_actual == "admin":
            self.btn_rep = ctk.CTkButton(
                sidebar, text="📊 Reportes", command=lambda: self.show_view("reports"), 
                height=40, font=("Segoe UI", 13, "bold"), fg_color="#334155", hover_color="#475569", corner_radius=8
            )
            self.btn_rep.pack(fill="x", padx=15, pady=5)

        btn_logout = ctk.CTkButton(
            sidebar, text="🚪 Cerrar Sesión", command=self.cerrar_sesion, 
            height=34, font=("Segoe UI", 11, "bold"), fg_color="#EF4444", hover_color="#DC2626", corner_radius=8
        )
        btn_logout.pack(side="bottom", fill="x", padx=15, pady=15)

    def cerrar_sesion(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.iniciar_pantalla_login()

    def update_sidebar_colors(self, active_name):
        self.btn_pos.configure(fg_color="#2563EB" if active_name == "pos" else "#334155")
        self.btn_cash.configure(fg_color="#2563EB" if active_name == "cash" else "#334155")
        self.btn_inv.configure(fg_color="#2563EB" if active_name == "inventory" else "#334155")
        if self.rol_actual == "admin":
            self.btn_rep.configure(fg_color="#2563EB" if active_name == "reports" else "#334155")

    def show_view(self, view_name):
        # Bloquear cualquier pantalla si la caja es obligatoria y no está abierta (excepto si es admin)
        if self.caja_obligatoria and self.rol_actual != "admin" and view_name != "cash":
            return

        # Bloquear únicamente "reports" si el rol es cajero
        if self.rol_actual == "cajero" and view_name == "reports":
            return

        self.update_sidebar_colors(view_name)

        for name, view in self.views.items():
            if name == view_name:
                view.grid(row=0, column=0, sticky="nsew")
            else:
                view.grid_remove()

        if view_name == "pos":
            self.after(30, self.views["pos"].focus_codigo)
        elif view_name == "cash":
            self.after(30, self.views["cash"].cargar_caja)
        elif view_name == "reports":
            self.after(30, self.views["reports"].cargar_reporte)
        elif view_name == "inventory":
            self.after(30, self.views["inventory"].cargar_productos)

if __name__ == "__main__":
    app = PuntoAgilApp()
    app.mainloop()
