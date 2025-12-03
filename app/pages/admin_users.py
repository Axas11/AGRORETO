from datetime import datetime

import reflex as rx
from sqlmodel import select

from app.components.styles import M3Styles
from app.models import User
from app.states.auth_state import AuthState


class AdminUserState(rx.State):
    """State para gestionar usuarios"""
    pending_users: list[dict] = []
    all_users: list[dict] = []
    selected_tab: str = "pending"
    
    def on_mount(self):
        """Cargar datos al montar el componente"""
        return AdminUserState.load_users
    
    @rx.event(background=True)
    async def load_users(self):
        """Cargar usuarios pendientes y aprobados"""
        async with self:
            with rx.session() as session:
                # Usuarios pendientes de aprobación
                pending = session.exec(
                    select(User).where(User.role == "registered")
                ).all()
                
                # Todos los usuarios aprobados
                approved = session.exec(
                    select(User).where(User.role != "registered")
                ).all()
                
                self.pending_users = [
                    {
                        "id": u.id,
                        "username": u.username,
                        "created_at": u.created_at.strftime("%d/%m/%Y %H:%M") if u.created_at else "",
                    }
                    for u in pending
                ]
                
                self.all_users = [
                    {
                        "id": u.id,
                        "username": u.username,
                        "role": u.role,
                        "created_at": u.created_at.strftime("%d/%m/%Y %H:%M") if u.created_at else "",
                    }
                    for u in approved
                ]
    
    @rx.event(background=True)
    async def approve_user(self, user_id: int):
        """Aprobar usuario (cambiar rol a technician)"""
        async with self:
            with rx.session() as session:
                user = session.exec(
                    select(User).where(User.id == user_id)
                ).first()
                
                if user:
                    user.role = "technician"
                    session.add(user)
                    session.commit()
        
        # Recargar usuarios
        await self.load_users()
    
    @rx.event(background=True)
    async def reject_user(self, user_id: int):
        """Rechazar usuario (eliminar)"""
        async with self:
            with rx.session() as session:
                user = session.exec(
                    select(User).where(User.id == user_id)
                ).first()
                
                if user:
                    session.delete(user)
                    session.commit()
        
        # Recargar usuarios
        await self.load_users()


def pending_users_table() -> rx.Component:
    """Tabla de usuarios pendientes de aprobación"""
    return rx.cond(
        AdminUserState.pending_users.length() > 0,
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Usuarios Pendientes de Aprobación",
                    class_name=f"text-xl font-bold text-slate-800 {M3Styles.FONT_FAMILY}",
                ),
                rx.el.p(
                    f"Total: {AdminUserState.pending_users.length()}",
                    class_name="text-sm text-slate-500 mt-1",
                ),
                class_name="mb-6",
            ),
            rx.foreach(
                AdminUserState.pending_users,
                lambda user: rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.div(
                                rx.el.h4(
                                    user["username"],
                                    class_name="text-lg font-semibold text-slate-800",
                                ),
                                rx.el.p(
                                    f"Registrado: {user['created_at']}",
                                    class_name="text-xs text-slate-500 mt-1",
                                ),
                                class_name="flex-1",
                            ),
                            rx.el.div(
                                rx.button(
                                    rx.icon("check", class_name="w-4 h-4"),
                                    "Aprobar",
                                    on_click=lambda: AdminUserState.approve_user(user["id"]),
                                    class_name=f"{M3Styles.BUTTON_PRIMARY} text-sm",
                                ),
                                rx.button(
                                    rx.icon("x", class_name="w-4 h-4"),
                                    "Rechazar",
                                    on_click=lambda: AdminUserState.reject_user(user["id"]),
                                    class_name=f"{M3Styles.BUTTON_SECONDARY} text-sm",
                                ),
                                class_name="flex gap-2",
                            ),
                            class_name="flex items-center justify-between p-4 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors",
                        ),
                        class_name="w-full",
                    ),
                    class_name="mb-3",
                ),
            ),
            class_name=f"{M3Styles.CARD} {M3Styles.ELEVATION_1} p-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("check_circle", class_name="w-12 h-12 text-green-500 mb-3"),
                rx.el.h3(
                    "¡Todos aprobados!",
                    class_name="text-lg font-semibold text-slate-800",
                ),
                rx.el.p(
                    "No hay usuarios pendientes de aprobación.",
                    class_name="text-slate-500 text-sm mt-2",
                ),
                class_name=f"flex flex-col items-center justify-center py-12 {M3Styles.CARD} {M3Styles.ELEVATION_1}",
            ),
        ),
    )


def approved_users_table() -> rx.Component:
    """Tabla de usuarios aprobados"""
    return rx.cond(
        AdminUserState.all_users.length() > 0,
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Usuarios Aprobados",
                    class_name=f"text-xl font-bold text-slate-800 {M3Styles.FONT_FAMILY}",
                ),
                rx.el.p(
                    f"Total: {AdminUserState.all_users.length()}",
                    class_name="text-sm text-slate-500 mt-1",
                ),
                class_name="mb-6",
            ),
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th("Usuario", class_name="px-4 py-3 text-left text-sm font-semibold text-slate-700"),
                            rx.el.th("Rol", class_name="px-4 py-3 text-left text-sm font-semibold text-slate-700"),
                            rx.el.th("Registrado", class_name="px-4 py-3 text-left text-sm font-semibold text-slate-700"),
                            class_name="border-b border-slate-200",
                        ),
                    ),
                    rx.foreach(
                        AdminUserState.all_users,
                        lambda user: rx.el.tr(
                            rx.el.td(user["username"], class_name="px-4 py-3 text-sm text-slate-800"),
                            rx.el.td(
                                rx.el.span(
                                    user["role"],
                                    class_name=rx.cond(
                                        user["role"] == "technician",
                                        "px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800",
                                        "px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800"
                                    ),
                                ),
                                class_name="px-4 py-3 text-sm",
                            ),
                            rx.el.td(user["created_at"], class_name="px-4 py-3 text-sm text-slate-600"),
                            class_name="border-b border-slate-100 hover:bg-slate-50",
                        ),
                    ),
                    class_name="w-full text-sm",
                ),
                class_name="overflow-x-auto",
            ),
            class_name=f"{M3Styles.CARD} {M3Styles.ELEVATION_1} p-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("users", class_name="w-12 h-12 text-slate-400 mb-3"),
                rx.el.h3(
                    "Sin usuarios aprobados",
                    class_name="text-lg font-semibold text-slate-800",
                ),
                rx.el.p(
                    "No hay usuarios aprobados aún.",
                    class_name="text-slate-500 text-sm mt-2",
                ),
                class_name=f"flex flex-col items-center justify-center py-12 {M3Styles.CARD} {M3Styles.ELEVATION_1}",
            ),
        ),
    )


def admin_users_page() -> rx.Component:
    """Página de administración de usuarios"""
    return rx.box(
        # Verificar que sea admin/farmer
        rx.cond(
            AuthState.is_farmer,
            rx.box(
                rx.el.div(
                    rx.el.h1(
                        "Gestión de Usuarios",
                        class_name=f"text-4xl font-bold text-slate-800 mb-2 {M3Styles.FONT_FAMILY}",
                    ),
                    rx.el.p(
                        "Aprobar o rechazar solicitudes de nuevos usuarios",
                        class_name="text-slate-500 text-lg mb-8",
                    ),
                    class_name="mb-8",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.button(
                            "Pendientes de Aprobación",
                            on_click=AdminUserState.set_selected_tab("pending"),
                            class_name=rx.cond(
                                AdminUserState.selected_tab == "pending",
                                f"px-6 py-2 rounded-lg font-semibold transition-all {M3Styles.BUTTON_PRIMARY}",
                                f"px-6 py-2 rounded-lg font-semibold transition-all {M3Styles.BUTTON_SECONDARY}"
                            ),
                        ),
                        rx.button(
                            "Usuarios Aprobados",
                            on_click=AdminUserState.set_selected_tab("approved"),
                            class_name=rx.cond(
                                AdminUserState.selected_tab == "approved",
                                f"px-6 py-2 rounded-lg font-semibold transition-all {M3Styles.BUTTON_PRIMARY}",
                                f"px-6 py-2 rounded-lg font-semibold transition-all {M3Styles.BUTTON_SECONDARY}"
                            ),
                        ),
                        rx.button(
                            "Volver al Inicio",
                            on_click=rx.redirect("/dashboard"),
                            class_name="px-6 py-2 rounded-lg font-semibold transition-all bg-slate-200 text-slate-700 hover:bg-slate-300",
                        ),
                        class_name="flex gap-3 mb-8",
                    ),
                    rx.cond(
                        AdminUserState.selected_tab == "pending",
                        pending_users_table(),
                        approved_users_table(),
                    ),
                    class_name="w-full",
                ),
                class_name="max-w-6xl mx-auto p-6",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("shield_alert", class_name="w-16 h-16 text-red-500 mb-4"),
                    rx.el.h2(
                        "Acceso Denegado",
                        class_name=f"text-2xl font-bold text-slate-800 {M3Styles.FONT_FAMILY}",
                    ),
                    rx.el.p(
                        "Solo los administradores pueden acceder a esta página.",
                        class_name="text-slate-600 mt-2",
                    ),
                    rx.button(
                        "Volver al Inicio",
                        on_click=rx.redirect("/"),
                        class_name=f"{M3Styles.BUTTON_PRIMARY} mt-6",
                    ),
                    class_name="flex flex-col items-center justify-center min-h-screen",
                ),
            ),
        ),
        class_name="min-h-screen bg-slate-50",
        # ✅ MOVIDO: on_load aquí en rx.box que sí lo soporta
        on_mount=AdminUserState.load_users,
    )
