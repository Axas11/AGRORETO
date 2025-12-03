import asyncio

import reflex as rx
from sqlmodel import select

from app.models import User
from app.utils import seed_database, verify_password


class AuthState(rx.State):
    username: str = ""
    password: str = ""
    error_message: str = ""
    success_message: str = ""
    is_loading: bool = False
    user_id: int | None = None
    user_role: str | None = None
    user_name: str | None = None

    @rx.event
    def toggle_loading(self):
        self.is_loading = not self.is_loading

    @rx.event(background=True)
    async def check_login(self, form_data: dict):
        """Attempt to log the user in."""
        async with self:
            self.username = form_data.get("username", "")
            self.password = form_data.get("password", "")
            if not self.username or not self.password:
                self.error_message = "Por favor ingresa usuario y contraseña."
                return
            self.is_loading = True
            self.error_message = ""
        await asyncio.sleep(0.8)
        async with self:
            with rx.session() as session:
                user = session.exec(
                    select(User).where(User.username == self.username)
                ).first()
                if user and verify_password(self.password, user.password_hash):
                    self.user_id = user.id
                    self.user_role = user.role
                    self.user_name = user.username
                    self.is_loading = False
                    self.password = ""
                    return rx.redirect("/dashboard")  # ← CAMBIO AQUÍ
                else:
                    self.is_loading = False
                    self.error_message = "Usuario o contraseña inválidos."

    @rx.event(background=True)
    async def register_user(self, form_data: dict):
        """Registrar un nuevo usuario con rol 'tech' por defecto."""
        async with self:
            username = form_data.get("username", "").strip()
            password = form_data.get("password", "")
            confirm_password = form_data.get("confirm_password", "")
            
            self.error_message = ""
            self.success_message = ""
            
            # Validaciones
            if not username or not password or not confirm_password:
                self.error_message = "Todos los campos son obligatorios."
                return
            
            if len(username) < 3:
                self.error_message = "El nombre de usuario debe tener al menos 3 caracteres."
                return
            
            if len(password) < 6:
                self.error_message = "La contraseña debe tener al menos 6 caracteres."
                return
            
            if password != confirm_password:
                self.error_message = "Las contraseñas no coinciden."
                return
            
            self.is_loading = True
        
        await asyncio.sleep(0.5)
        
        async with self:
            from app.utils import get_password_hash
            
            with rx.session() as session:
                # Verificar si el usuario ya existe
                existing_user = session.exec(
                    select(User).where(User.username == username)
                ).first()
                
                if existing_user:
                    self.is_loading = False
                    self.error_message = "El nombre de usuario ya está en uso."
                    return
                
                # Crear nuevo usuario con rol 'technician'
                new_user = User(
                    username=username,
                    password_hash=get_password_hash(password),
                    role="technician"
                )
                
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
                
                self.is_loading = False
                self.success_message = "¡Cuenta creada exitosamente! Redirigiendo al login..."
                
        await asyncio.sleep(1.5)
        return rx.redirect("/login")

    @rx.event
    def logout(self):
        """Log the user out and clear session."""
        self.user_id = None
        self.user_role = None
        self.user_name = None
        self.username = ""
        self.password = ""
        self.error_message = ""
        self.success_message = ""
        return rx.redirect("/login")

    @rx.event
    def ensure_db_seeded(self):
        """Called on app load to ensure DB has data."""
        seed_database()
    
    @rx.event
    def check_authentication(self):
        """Verifica autenticación antes de acceder a páginas protegidas"""
        if not self.is_authenticated:
            return rx.redirect("/login") 

    @rx.event
    def check_auth_or_index(self):
        """Verifica autenticación y redirige a la página de inicio si no está autenticado."""
        if not self.is_authenticated:
            return rx.redirect("/")

    @rx.var
    def is_authenticated(self) -> bool:
        return self.user_id is not None

    @rx.var
    def is_farmer(self) -> bool:
        return self.user_role == "farmer"

    @rx.var
    def is_technician(self) -> bool:
        return self.user_role == "technician"
