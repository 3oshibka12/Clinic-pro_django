from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Doctor, Schedule, Patient, Appointment, DoctorFutureAppointmentView, DoctorPastAppointmentView, PatientHistoryView, AnalystStatsView, AnalystStatsView
from .forms import ScheduleForm, PrescriptionForm

# --- 1. Публичные страницы (доступны всем) ---

def home_page(request):
    """Главная страница"""
    return render(request, 'clinic/home.html')

# clinic/views.py

def doctor_list(request):
    # 1. Базовый список всех врачей
    doctors = Doctor.objects.all().order_by('lname')
    
    # 2. Получаем данные для выпадающих списков (фильтров)
    specializations = Doctor.objects.values_list('specialization', flat=True).distinct().order_by('specialization')
    regions = Doctor.objects.values_list('region', flat=True).distinct().order_by('region')

    # 3. Применяем фильтры, если они пришли в запросе
    spec_filter = request.GET.get('spec')
    region_filter = request.GET.get('region')

    if spec_filter:
        doctors = doctors.filter(specialization=spec_filter)
    
    if region_filter:
        doctors = doctors.filter(region=region_filter)

    context = {
        'doctors': doctors,
        'specializations': specializations,
        'regions': regions,
        # Возвращаем выбранные значения, чтобы они не слетали в форме
        'selected_spec': spec_filter,
        'selected_region': region_filter and int(region_filter) 
    }
    return render(request, 'clinic/doctor_list.html', context)

def doctor_schedule(request, doctor_pk):
    """Просмотр расписания конкретного врача (статичное)"""
    doctor = get_object_or_404(Doctor, pk=doctor_pk)
    schedule_items = Schedule.objects.filter(doctor=doctor).order_by('day', 'time_start')
    context = {'doctor': doctor, 'schedule_items': schedule_items}
    return render(request, 'clinic/doctor_schedule.html', context)


# --- 2. Авторизация ---

class MyLoginView(LoginView):
    template_name = 'clinic/login.html'

def logout_view(request):
    logout(request)
    return redirect('home')


# --- 3. Личный кабинет (Hub) ---

@login_required
def profile_view(request):
    """
    Единый ЛК. Определяет роль и отдает нужный контент.
    """
    user = request.user
    context = {}
    now = timezone.now() 


    # 1. АНАЛИТИК
    if user.username == 'analyst':
        context['role'] = 'analyst'
        # Просто берем всё из View
        context['stats'] = AnalystStatsView.objects.all().order_by('-appointment_count')
        return render(request, 'clinic/profile_analyst.html', context)

    # А. Менеджер (Персонал)
    if user.is_staff:
        context['role'] = 'manager'
        return render(request, 'clinic/profile_manager.html', context)

    elif hasattr(user, 'doctor'):
        doctor = user.doctor
        context['role'] = 'doctor'
        context['doctor'] = doctor        
        context['appointments_today'] = Appointment.objects.filter(
            doctor=doctor,
            visit_time__date=now.date() # Строго сегодняшняя дата
        ).order_by('visit_time')

        return render(request, 'clinic/profile.html', context)

    elif hasattr(user, 'patient'):
        context['role'] = 'patient'
        context['patient'] = user.patient
        context['my_appointments'] = PatientHistoryView.objects.filter(
            visit_time__gte=now
        ).order_by('visit_time')
        
        return render(request, 'clinic/profile.html', context)

    # Г. Неизвестная роль
    else:
        return render(request, 'clinic/profile.html', {'role': 'unknown'})

@login_required
def patient_history_view(request):
    # Проверка на пациента
    if not hasattr(request.user, 'patient'):
        return redirect('profile')
    
    now = timezone.now()
    
    # Берем ТОЛЬКО ПРОШЕДШИЕ записи (Архив)
    history = PatientHistoryView.objects.filter(
        visit_time__lt=now
    ).order_by('-visit_time') # Сначала самые недавние
    
    return render(request, 'clinic/patient_history.html', {'history': history})


@login_required
def doctor_calendar_view(request):
    if not hasattr(request.user, 'doctor'):
        return redirect('profile')
    
    doctor = request.user.doctor
    
    # 1. Получаем дату из URL (?date=2024-05-20) или берем сегодня
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    appointments = Appointment.objects.filter(
        doctor=doctor,
        visit_time__date=selected_date
    ).select_related('patient').order_by('visit_time')

    context = {
        'selected_date': selected_date,
        'appointments': appointments,
        'today': timezone.now().date()
    }
    return render(request, 'clinic/doctor_calendar.html', context)


# --- 4. Функционал Менеджера ---

@login_required
def manage_schedule(request):
    """Страница создания/редактирования расписания"""
    if not request.user.is_staff:
        return redirect('profile')

    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ScheduleForm()
    
    return render(request, 'clinic/schedule_form.html', {'form': form})


# --- 5. Функционал Пациента (Поиск и Запись) ---

@login_required
def find_doctor_view(request):
    """Поиск врача по специализации (учитывая регион пациента)"""
    # Проверка: пускаем только пациентов
    if not hasattr(request.user, 'patient'):
        messages.error(request, "Эта страница доступна только пациентам")
        return redirect('profile')

    patient = request.user.patient
    
    # Список всех специализаций для выпадающего меню
    specializations = Doctor.objects.values_list('specialization', flat=True).distinct().order_by('specialization')

    selected_spec = request.GET.get('specialization')
    doctors = None

    if selected_spec:
        # Ищем врачей: выбранная спец. + тот же регион, что у пациента
        doctors = Doctor.objects.filter(
            specialization=selected_spec,
            region=patient.region
        )

    context = {
        'specializations': specializations,
        'selected_spec': selected_spec,
        'doctors': doctors,
        'patient_region': patient.region
    }
    return render(request, 'clinic/find_doctor.html', context)


@login_required
def doctor_booking(request, doctor_pk):
    """Генерация слотов и запись на прием"""
    if not hasattr(request.user, 'patient'):
        return redirect('home')

    doctor = get_object_or_404(Doctor, pk=doctor_pk)
    patient = request.user.patient
    
    if request.method == 'POST':
        visit_date_str = request.POST.get('visit_date') # YYYY-MM-DD
        visit_time_str = request.POST.get('visit_time') # HH:MM
        
        full_visit_time = datetime.strptime(f"{visit_date_str} {visit_time_str}", "%Y-%m-%d %H:%M")
        full_visit_time = timezone.make_aware(full_visit_time)

        if not Appointment.objects.filter(doctor=doctor, visit_time=full_visit_time).exists():
            Appointment.objects.create(
                doctor=doctor,
                patient=patient,
                visit_time=full_visit_time,
                cabinet=100
            )
            messages.success(request, f"Вы записаны к {doctor.full_name} на {visit_date_str} {visit_time_str}")
            return redirect('profile')
        else:
            messages.error(request, "Извините, это время уже занято.")

    today = timezone.now().date()
    week_schedule = []

    # Цикл на 7 дней вперед
    for i in range(7):
        current_date = today + timedelta(days=i)
        weekday_num = current_date.isoweekday()
        
        sched = Schedule.objects.filter(doctor=doctor, day=weekday_num).first()
        
        slots = []
        if sched:
            start_dt = datetime.combine(current_date, sched.time_start)
            end_dt = datetime.combine(current_date, sched.time_end)
            
            current_slot = start_dt
            while current_slot < end_dt:
                check_time = timezone.make_aware(current_slot)
                
                # Проверяем, есть ли запись в БД на это время
                is_taken = Appointment.objects.filter(
                    doctor=doctor, 
                    visit_time=check_time
                ).exists()

                # Если время не прошло (для сегодня) и не занято
                if check_time > timezone.now() and not is_taken:
                    slots.append(current_slot.time())

                current_slot += sched.interval

        week_schedule.append({
            'date': current_date,
            'weekday_name': current_date.strftime('%A'), # День недели
            'slots': slots
        })

    context = {
        'doctor': doctor,
        'week_schedule': week_schedule,
    }
    return render(request, 'clinic/doctor_booking.html', context)




@login_required
def add_prescription(request, appointment_pk):
    # 1. Получаем запись
    appointment = get_object_or_404(Appointment, pk=appointment_pk, doctor__user=request.user)
    
    # 2. Пытаемся найти уже существующий рецепт для этой записи
    prescription = appointment.get_prescription # Используем наше новое свойство

    # 3. Обработка POST запроса
    if request.method == 'POST':
        # Если рецепт есть — передаем instance=prescription (для редактирования)
        # Если нет — форма пустая (для создания)
        form = PrescriptionForm(request.POST, instance=prescription)
        
        if form.is_valid():
            new_presc = form.save(commit=False)
            new_presc.id_rec = appointment # Привязываем к записи
            new_presc.save()
            
            action = "обновлен" if prescription else "создан"
            messages.success(request, f"Рецепт успешно {action}.")
            return redirect('profile')
    else:
        # GET запрос: заполняем форму существующими данными или показываем пустую
        form = PrescriptionForm(instance=prescription)

    context = {
        'form': form,
        'appointment': appointment,
        'is_edit': bool(prescription) # Флаг для шаблона (чтобы менять заголовок)
    }
    return render(request, 'clinic/prescription_form.html', context)








@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    is_manager = request.user.is_staff
    is_owner = hasattr(request.user, 'patient') and appointment.patient == request.user.patient

    if is_manager or is_owner:
        appointment.delete()
        messages.success(request, "Запись успешно отменена.")
    else:
        messages.error(request, "У вас нет прав для отмены этой записи.")

    return redirect('profile')


@login_required
def edit_appointment_manager(request, pk):
    # Проверка: только персонал
    if not request.user.is_staff:
        return redirect('profile')

    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == 'POST':
        form = AppointmentEditForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save() # Сработает SQL триггер
            messages.success(request, "Запись успешно обновлена.")
            return redirect('profile')
    else:
        form = AppointmentEditForm(instance=appointment)

    return render(request, 'clinic/appointment_edit_manager.html', {'form': form, 'appt': appointment})





@login_required
def manager_schedules_list(request):
    if not request.user.is_staff:
        return redirect('profile')
    
    # Грузим все расписания
    schedules = Schedule.objects.all().order_by('doctor__lname', 'day', 'time_start')
    return render(request, 'clinic/manager_schedules.html', {'schedules': schedules})


# --- 3. Страница СПИСОК ЗАПИСЕЙ ---
@login_required
def manager_appointments_list(request):
    if not request.user.is_staff:
        return redirect('profile')

    # Грузим все будущие записи (можно и прошлые, если надо)
    appointments = Appointment.objects.filter(
        visit_time__gte=timezone.now()
    ).order_by('visit_time')
    
    return render(request, 'clinic/manager_appointments.html', {'appointments': appointments})


# --- 4. Редактирование конкретного слота расписания ---
@login_required
def edit_schedule(request, pk):
    if not request.user.is_staff:
        return redirect('profile')
        
    schedule = get_object_or_404(Schedule, pk=pk)
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, "Расписание обновлено.")
            return redirect('manager_schedules')
    else:
        form = ScheduleForm(instance=schedule)
        
    return render(request, 'clinic/schedule_form.html', {'form': form})

# --- 5. Удаление расписания ---
@login_required
def delete_schedule(request, pk):
    if request.user.is_staff:
        get_object_or_404(Schedule, pk=pk).delete()
        messages.success(request, "Пункт расписания удален.")
    return redirect('manager_schedules')