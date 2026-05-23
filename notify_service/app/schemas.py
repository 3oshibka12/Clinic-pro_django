from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class AppointmentInfoCreate(BaseModel):
    email: EmailStr
    patient_name: str
    doctor_name: str
    visit_time: str
    cabinet: int

class ReminderCreate(BaseModel):
    email: EmailStr
    message: str

class PrescriptionRequest(BaseModel):
    appointment_id: int
    email: EmailStr
    doc_type: str = "recipe"




class NotificationResp(BaseModel):
    id: int
    type: str
    email: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)