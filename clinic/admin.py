from django.contrib import admin
from .models import (
    Doctor, Patient, Schedule, Appointment, 
    Diagnosis, Drug, Prescription, HistoryAppointment
)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'specialization', 'region', 'user_link')
    search_fields = ('lname', 'fname', 'specialization')
    list_filter = ('specialization', 'region')
    
    def user_link(self, obj):
        return obj.user.username if obj.user else "-"
    user_link.short_description = "Пользователь"

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date', 'region', 'user_link')
    search_fields = ('lname', 'fname')
    list_filter = ('region',)

    def user_link(self, obj):
        return obj.user.username if obj.user else "-"
    user_link.short_description = "Пользователь"

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'get_day_display', 'time_start', 'time_end', 'interval')
    list_filter = ('doctor', 'day')
    ordering = ('doctor', 'day', 'time_start')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'visit_time', 'cabinet')
    list_filter = ('doctor', 'visit_time')
    search_fields = ('patient__lname', 'doctor__lname')
    date_hierarchy = 'visit_time'

@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_moment_display')
    list_filter = ('moment',)

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id_rec', 'id_diag', 'id_drug', 'frequency', 'duration')
    list_filter = ('id_diag', 'id_drug')

@admin.register(HistoryAppointment)
class HistoryAppointmentAdmin(admin.ModelAdmin):
    list_display = ('id_rec', 'visit_time', 'cabinet', 'id_doc', 'id_pat')
    readonly_fields = ('id_rec', 'id_pat', 'id_doc', 'visit_time', 'cabinet')
    
    def has_add_permission(self, request):
        return False  # Историю нельзя создавать вручную через админку