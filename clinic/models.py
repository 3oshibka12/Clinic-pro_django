from django.db import models
from django.contrib.auth.models import User

class Doctor(models.Model):
    id_doc = models.AutoField(primary_key=True)
    fname = models.CharField("Имя", max_length=150)
    lname = models.CharField("Фамилия", max_length=150)
    specialization = models.CharField("Специализация", max_length=200)
    region = models.IntegerField("Регион")
    
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Аккаунт для входа"
    )

    def __str__(self):
        return f"{self.lname} {self.fname} ({self.specialization})"

    @property
    def full_name(self):
        return f"{self.lname} {self.fname}"


class Patient(models.Model):
    id_pat = models.AutoField(primary_key=True)
    fname = models.CharField("Имя", max_length=150)
    lname = models.CharField("Фамилия", max_length=150)
    birth_date = models.DateField("Дата рождения")
    region = models.IntegerField("Регион")

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Аккаунт для входа"
    )

    def __str__(self):
        return f"{self.lname} {self.fname}"

    @property
    def full_name(self):
        return f"{self.lname} {self.fname}"

class Schedule(models.Model):
    DAYS_OF_WEEK = (
        (1, 'Понедельник'), (2, 'Вторник'), (3, 'Среда'),
        (4, 'Четверг'), (5, 'Пятница'), (6, 'Суббота'), (7, 'Воскресенье'),
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        verbose_name="Врач",
        db_column='id_doc'
    )
    day = models.IntegerField("День недели", choices=DAYS_OF_WEEK)
    time_start = models.TimeField("Начало приёма")
    time_end = models.TimeField("Конец приёма")
    interval = models.DurationField("Интервал", default='00:20:00')

    class Meta:
        unique_together = ('doctor', 'day', 'time_start')
        verbose_name = "Пункт расписания"
        verbose_name_plural = "Расписания"

    def __str__(self):
        return f"Расписание для {self.doctor} в {self.get_day_display()}"


class Appointment(models.Model):
    id_rec = models.AutoField(primary_key=True)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        verbose_name="Пациент",
        db_column='id_pat'
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        verbose_name="Врач",
        db_column='id_doc'
    )
    visit_time = models.DateTimeField("Дата и время визита")
    cabinet = models.IntegerField("Кабинет")

    class Meta:
        verbose_name = "Запись на приём"
        verbose_name_plural = "Записи на приём"

    def __str__(self):
        return f"Запись {self.patient} к {self.doctor} на {self.visit_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def get_prescription(self):
        # Пытаемся найти рецепт, связанный с этой записью
        # Так как связь через ForeignKey в Prescription (id_rec), используем reverse relation
        # В Prescription поле называется id_rec, значит обратная связь prescription_set
        return self.prescription_set.first()


class Diagnosis(models.Model):
    id_diag = models.AutoField(primary_key=True)
    name = models.CharField("Диагноз", max_length=200)
    description = models.TextField("Описание", null=True, blank=True)

    class Meta:
        verbose_name = "Диагноз"
        verbose_name_plural = "Диагнозы"

    def __str__(self):
        return self.name


class Drug(models.Model):
    id_drug = models.AutoField(primary_key=True)
    name = models.CharField("Название", max_length=200)

    class ReceptionTime(models.TextChoices):
        BEFORE = 'before', 'До приема'
        DURING = 'during', 'Во время приема'
        AFTER = 'after', 'После приема'
    
    moment = models.CharField(
        max_length=10,
        choices=ReceptionTime.choices,
    )

    class Meta:
        verbose_name = "Лекарство"
        verbose_name_plural = "Лекарства"

    def __str__(self):
        return self.name


class Prescription(models.Model):
    id_rec = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Запись")
    id_diag = models.ForeignKey(Diagnosis, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Диагноз")
    id_drug = models.ForeignKey(Drug, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Лекарство")
    frequency = models.IntegerField("Частота применения")
    duration = models.DurationField("Продолжительность")
    treatment = models.TextField("Лечение")

    class Meta:
        unique_together = ('id_rec', 'id_drug')
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return f"Рецепт {self.id_rec}"




# История изменения данных 

class HistoryAppointment(models.Model):
    id_change = models.AutoField(primary_key=True)
    # БЫЛО: models.ForeignKey(...)
    # СТАЛО: models.IntegerField(...)
    id_rec = models.IntegerField("ID Записи") 
    id_pat = models.IntegerField("ID Пациента")
    id_doc = models.IntegerField("ID Врача")
    
    visit_time = models.DateTimeField("Дата и время визита")
    cabinet = models.IntegerField("Кабинет")

    class Meta:
        managed = False # Желательно добавить, раз мы правим таблицу руками через SQL
        verbose_name = "История изменения данных"
        verbose_name_plural = "История изменения данных"
    








class DoctorFutureAppointmentView(models.Model):
    id_rec = models.IntegerField(primary_key=True)
    visit_time = models.DateTimeField()
    cabinet = models.IntegerField()
    patient_name = models.CharField(max_length=300)
    birth_date = models.DateField()

    class Meta:
        managed = False  # Django не создает эту таблицу
        db_table = 'view_doctor_future_appointments' # Имя VIEW в базе

class DoctorPastAppointmentView(models.Model):
    id_rec = models.IntegerField(primary_key=True)
    visit_time = models.DateTimeField()
    patient_name = models.CharField(max_length=300)
    has_prescription = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'view_doctor_past_appointments'

class PatientHistoryView(models.Model):
    id_rec = models.IntegerField(primary_key=True)
    visit_time = models.DateTimeField()
    doctor_info = models.CharField(max_length=300)
    cabinet = models.IntegerField()
    # Поля рецепта могут быть NULL (если рецепта нет)
    diagnosis = models.CharField(max_length=200, null=True)
    drug_name = models.CharField(max_length=200, null=True)
    treatment = models.TextField(null=True)
    frequency = models.IntegerField(null=True)
    duration = models.DurationField(null=True)

    class Meta:
        managed = False
        db_table = 'view_patient_history'


class AnalystStatsView(models.Model):
    id = models.IntegerField(primary_key=True)
    fname = models.CharField(max_length=150)
    lname = models.CharField(max_length=150)
    specialization = models.CharField(max_length=200)
    appointment_count = models.IntegerField()

    class Meta:
        managed = False  # Это SQL View
        db_table = 'static_per_month'
        verbose_name = "Статистика за месяц"