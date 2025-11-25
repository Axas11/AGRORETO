import reflex as rx
from sqlmodel import select
from app.models import User
from app.utils import verify_password, seed_database
import asyncio


class AuthState(rx.State):
    username: str = ""
    password: str = ""
    error_message: str = ""
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
                self.error_message = "Please enter both username and password."
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
                    return rx.redirect("/")
                else:
                    self.is_loading = False
                    self.error_message = "Invalid username or password."

    @rx.event
    def logout(self):
        """Log the user out and clear session."""
        self.user_id = None
        self.user_role = None
        self.user_name = None
        self.username = ""
        self.password = ""
        self.error_message = ""
        return rx.redirect("/login")

    @rx.event
    def ensure_db_seeded(self):
        """Called on app load to ensure DB has data."""
        seed_database()

    @rx.var
    def is_authenticated(self) -> bool:
        return self.user_id is not None

    @rx.var
    def is_farmer(self) -> bool:
        return self.user_role == "farmer"

    @rx.var
    def is_technician(self) -> bool:
        return self.user_role == "technician"