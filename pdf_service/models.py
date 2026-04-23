from sqlalchemy import Column, Integer, String, Date, DateTime, Time, Text, ForeignKey, UniqueConstraint, Boolean, Interval
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Doctor(Base):
    __tablename__ = 'clinic_doctor'
    
    id_doc = Column(Integer, primary_key=True, autoincrement=True)
    fname = Column(String(150), nullable=False)
    lname = Column(String(150), nullable=False)
    specialization = Column(String(200), nullable=False)
    region = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('auth_user.id'), nullable=True, unique=True)
    
    # Relationships
    schedules = relationship("Schedule", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
    
    @property
    def full_name(self):
        return f"{self.lname} {self.fname}"


class Patient(Base):
    __tablename__ = 'clinic_patient'
    
    id_pat = Column(Integer, primary_key=True, autoincrement=True)
    fname = Column(String(150), nullable=False)
    lname = Column(String(150), nullable=False)
    birth_date = Column(Date, nullable=False)
    region = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('auth_user.id'), nullable=True, unique=True)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="patient")
    
    @property
    def full_name(self):
        return f"{self.lname} {self.fname}"


class Schedule(Base):
    __tablename__ = 'clinic_schedule'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey('clinic_doctor.id_doc'), nullable=False)
    day = Column(Integer, nullable=False)
    time_start = Column(Time, nullable=False)
    time_end = Column(Time, nullable=False)
    interval = Column(Interval, nullable=False)
    
    # Relationships
    doctor = relationship("Doctor", back_populates="schedules")
    
    __table_args__ = (
        UniqueConstraint('doctor_id', 'day', 'time_start', name='unique_doctor_day_time'),
    )


class Appointment(Base):
    __tablename__ = 'clinic_appointment'
    
    id_rec = Column(Integer, primary_key=True, autoincrement=True)
    id_pat = Column(Integer, ForeignKey('clinic_patient.id_pat'), nullable=False)
    id_doc = Column(Integer, ForeignKey('clinic_doctor.id_doc'), nullable=False)
    visit_time = Column(DateTime, nullable=False)
    cabinet = Column(Integer, nullable=False)
    
    # Relationships с указанием правильных foreign_keys
    patient = relationship("Patient", back_populates="appointments", foreign_keys=[id_pat])
    doctor = relationship("Doctor", back_populates="appointments", foreign_keys=[id_doc])
    prescriptions = relationship("Prescription", back_populates="appointment")
    
    @property
    def get_prescription(self):
        if self.prescriptions:
            return self.prescriptions[0]
        return None


class Diagnosis(Base):
    __tablename__ = 'clinic_diagnosis'
    
    id_diag = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    prescriptions = relationship("Prescription", back_populates="diagnosis")


class Drug(Base):
    __tablename__ = 'clinic_drug'
    
    id_drug = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    moment = Column(String(10), nullable=False)
    
    # Relationships
    prescriptions = relationship("Prescription", back_populates="drug")


class Prescription(Base):
    __tablename__ = 'clinic_prescription'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_rec = Column('id_rec_id', Integer, ForeignKey('clinic_appointment.id_rec'), nullable=True)
    id_diag = Column('id_diag_id', Integer, ForeignKey('clinic_diagnosis.id_diag'), nullable=True)
    id_drug = Column('id_drug_id', Integer, ForeignKey('clinic_drug.id_drug'), nullable=True)
    frequency = Column(Integer, nullable=False)
    duration = Column(Interval, nullable=False)
    treatment = Column(Text, nullable=False)
    
    # Relationships
    appointment = relationship("Appointment", back_populates="prescriptions", foreign_keys=[id_rec])
    diagnosis = relationship("Diagnosis", back_populates="prescriptions", foreign_keys=[id_diag])
    drug = relationship("Drug", back_populates="prescriptions", foreign_keys=[id_drug])


class HistoryAppointment(Base):
    __tablename__ = 'clinic_historyappointment'
    
    id_change = Column(Integer, primary_key=True, autoincrement=True)
    id_rec = Column(Integer, nullable=False)
    id_pat = Column(Integer, nullable=False)
    id_doc = Column(Integer, nullable=False)
    visit_time = Column(DateTime, nullable=False)
    cabinet = Column(Integer, nullable=False)


# SQL Views
class DoctorFutureAppointmentView(Base):
    __tablename__ = 'view_doctor_future_appointments'
    __table_args__ = {'info': {'is_view': True}}
    
    id_rec = Column(Integer, primary_key=True)
    visit_time = Column(DateTime)
    cabinet = Column(Integer)
    patient_name = Column(String(300))
    birth_date = Column(Date)


class DoctorPastAppointmentView(Base):
    __tablename__ = 'view_doctor_past_appointments'
    __table_args__ = {'info': {'is_view': True}}
    
    id_rec = Column(Integer, primary_key=True)
    visit_time = Column(DateTime)
    patient_name = Column(String(300))
    has_prescription = Column(Boolean)


class PatientHistoryView(Base):
    __tablename__ = 'view_patient_history'
    __table_args__ = {'info': {'is_view': True}}
    
    id_rec = Column(Integer, primary_key=True)
    visit_time = Column(DateTime)
    doctor_info = Column(String(300))
    cabinet = Column(Integer)
    diagnosis = Column(String(200), nullable=True)
    drug_name = Column(String(200), nullable=True)
    treatment = Column(Text, nullable=True)
    frequency = Column(Integer, nullable=True)
    duration = Column(Interval, nullable=True)


class AnalystStatsView(Base):
    __tablename__ = 'static_per_month'
    __table_args__ = {'info': {'is_view': True}}
    
    id = Column(Integer, primary_key=True)
    fname = Column(String(150))
    lname = Column(String(150))
    specialization = Column(String(200))
    appointment_count = Column(Integer)