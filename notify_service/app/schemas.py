from pydantic import BaseModel
from datetime import datetime


class AppointmentInfoCreate(BaseModel):
    email: str
    patient_name: str
    doctor_name: str
    visit_time: str
    cabinet: int

class ReminderCreate(BaseModel):
    email: str
    message: str

class PrescriptionRequest(BaseModel):
    appointment_id: int
    email: str
    doc_type: str = "recipe"




class NotificationResp(BaseModel):
    id: int
    type: str
    email: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True 