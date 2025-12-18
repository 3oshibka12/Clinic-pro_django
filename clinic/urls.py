# clinic/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- 1. Общие страницы ---
    path('', views.home_page, name='home'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/<int:doctor_pk>/', views.doctor_schedule, name='doctor_schedule'),
    
    # --- 2. Авторизация ---
    path('login/', views.MyLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # --- 3. Функционал ПАЦИЕНТА ---
    path('patient/find-doctor/', views.find_doctor_view, name='find_doctor'),
    path('doctor/<int:doctor_pk>/book/', views.doctor_booking, name='doctor_booking'),
    
    # --- 4. Функционал ВРАЧА ---
    path('doctor/appointment/<int:appointment_pk>/prescribe/', views.add_prescription, name='add_prescription'),

    # --- 5. Функционал РЕГИСТРАТОРА (Менеджера) ---
    # Главные списки
    path('manager/schedules/', views.manager_schedules_list, name='manager_schedules'),
    path('manager/appointments/', views.manager_appointments_list, name='manager_appointments'),

    # Управление РАСПИСАНИЕМ (CRUD)
    path('manager/schedule/add/', views.manage_schedule, name='add_schedule'),
    path('manager/schedule/<int:pk>/edit/', views.edit_schedule, name='edit_schedule'),
    path('manager/schedule/<int:pk>/delete/', views.delete_schedule, name='delete_schedule'),

    # --- 6. Действия с ЗАПИСЯМИ (Отмена и Редактирование) ---
    
    # Отмена записи (доступна и Пациенту, и Менеджеру)
    path('appointment/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    
    # Редактирование записи (доступно только Менеджеру)
    path('manager/appointment/<int:pk>/edit/', views.edit_appointment_manager, name='edit_appointment_manager'),

    # Истории для пользователей
    path('patient/history/', views.patient_history_view, name='patient_history'),
    path('doctor/calendar/', views.doctor_calendar_view, name='doctor_calendar'),
]