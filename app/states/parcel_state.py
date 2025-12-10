import logging

import reflex as rx
from sqlmodel import Session, select

from app.models import Parcel, ParcelTechnician, Sensor, User
from app.states.auth_state import AuthState
from app.utils import engine


class ParcelState(rx.State):
    parcels: list[Parcel] = []
    assigned_technicians: list[dict] = []
    available_technicians: list[dict] = []
    selected_technician_id: str = ""
    selected_parcel_id: int | None = None
    show_add_modal: bool = False
    new_parcel_name: str = ""
    new_parcel_location: str = ""
    new_parcel_area: float = 0.0

    @rx.event
    async def load_parcels(self):
        """Carga las parcelas según el rol del usuario"""
        auth_state = await self.get_state(AuthState)
        
        user_role = auth_state.user_role
        user_id = auth_state.user_id
        
        if not user_id:
            self.parcels = []
            return

        with Session(engine) as session:
            if user_role == "farmer":
                self.parcels = session.exec(select(Parcel)).all()
            else:
                assigned_subq = select(ParcelTechnician.parcel_id).where(
                    ParcelTechnician.user_id == user_id
                )
                self.parcels = session.exec(
                    select(Parcel).where(
                        (Parcel.owner_id == user_id) | (Parcel.id.in_(assigned_subq))
                    )
                ).all()

    @rx.event
    def open_add_modal(self):
        self.show_add_modal = True

    @rx.event
    def close_add_modal(self):
        self.show_add_modal = False
        self.new_parcel_name = ""
        self.new_parcel_location = ""
        self.new_parcel_area = 0.0

    @rx.event
    def set_new_parcel_name(self, value: str):
        self.new_parcel_name = value

    @rx.event
    def set_new_parcel_location(self, value: str):
        self.new_parcel_location = value

    @rx.event
    def set_new_parcel_area(self, value: str):
        try:
            self.new_parcel_area = float(value)
        except ValueError as e:
            logging.exception(f"Error parsing parcel area: {e}")

    @rx.event
    async def add_parcel(self):
        if not self.new_parcel_name or not self.new_parcel_location:
            return
        auth_state = await self.get_state(AuthState)
        if not auth_state.user_id:
            return
        with Session(engine) as session:
            new_parcel = Parcel(
                name=self.new_parcel_name,
                location=self.new_parcel_location,
                area=self.new_parcel_area,
                owner_id=auth_state.user_id,
            )
            session.add(new_parcel)
            session.commit()
            session.refresh(new_parcel)
        self.close_add_modal()
        await self.load_parcels()

    @rx.var
    def parcel_id(self) -> int:
        pid_str = self.router.page.params.get("id", "")
        if not pid_str:
            return 0
        try:
            return int(pid_str)
        except ValueError:
            return 0

    @rx.event
    def load_assigned_techs(self):
        """Carga técnicos asignados y disponibles para la parcela actual"""
        pid = self.parcel_id
        if not pid:
            self.assigned_technicians = []
            self.available_technicians = []
            return

        with Session(engine) as session:
            # Técnicos asignados
            rows = session.exec(
                select(ParcelTechnician).where(ParcelTechnician.parcel_id == pid)
            ).all()
            tech_ids = [r.user_id for r in rows]
            
            # ✅ CORREGIDO: Solo buscar si hay IDs
            if tech_ids:
                users = session.exec(select(User).where(User.id.in_(tech_ids))).all()
                self.assigned_technicians = [
                    {"id": u.id, "username": u.username} for u in users
                ]
            else:
                self.assigned_technicians = []

            # ✅ CORREGIDO: Técnicos disponibles (manejar lista vacía)
            if tech_ids:
                available = session.exec(
                    select(User).where(
                        (User.role == "technician") & (~User.id.in_(tech_ids))
                    )
                ).all()
            else:
                # Si no hay técnicos asignados, mostrar todos
                available = session.exec(
                    select(User).where(User.role == "technician")
                ).all()
            
            self.available_technicians = [
                {"id": u.id, "username": u.username} for u in available
            ]

    @rx.event
    def set_selected_technician_id(self, val: str):
        """Actualiza el técnico seleccionado"""
        self.selected_technician_id = val

    @rx.event
    async def assign_technician(self, technician_id: int):
        """Asigna un técnico a la parcela actual"""
        pid = self.parcel_id
        if not pid or not technician_id:
            return
        with Session(engine) as session:
            exists = session.exec(
                select(ParcelTechnician).where(
                    (ParcelTechnician.parcel_id == pid) & (ParcelTechnician.user_id == technician_id)
                )
            ).first()
            if not exists:
                assign = ParcelTechnician(parcel_id=pid, user_id=technician_id)
                session.add(assign)
                session.commit()

        self.load_assigned_techs()
        await self.load_parcels()

    @rx.event
    async def assign_technician_from_select(self):
        """Asignar técnico desde el select"""
        if not self.selected_technician_id:
            return
        
        try:
            tech_id = int(self.selected_technician_id)
        except ValueError:
            return
        
        await self.assign_technician(tech_id)
        self.selected_technician_id = ""

    @rx.event
    async def remove_technician(self, technician_id: int):
        """Quita asignación de técnico de la parcela actual"""
        pid = self.parcel_id
        if not pid or not technician_id:
            return
        with Session(engine) as session:
            row = session.exec(
                select(ParcelTechnician).where(
                    (ParcelTechnician.parcel_id == pid) & (ParcelTechnician.user_id == technician_id)
                )
            ).first()
            if row:
                session.delete(row)
                session.commit()

        self.load_assigned_techs()
        await self.load_parcels()

    @rx.event
    def delete_parcel(self, parcel_id: int):
        with Session(engine) as session:
            parcel = session.get(Parcel, parcel_id)
            if parcel:
                session.delete(parcel)
                session.commit()
        self.load_parcels()

    @rx.event
    def navigate_to_parcel(self, parcel_id: int):
        return rx.redirect(f"/parcels/{parcel_id}")
