from django import forms
from .models import Schedule

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['doctor', 'day', 'time_start', 'time_end', 'interval']
        widgets = {
            # day - больше не трогаем, Django сам сделает выпадающий список
            'time_start': forms.TimeInput(attrs={'type': 'time'}),
            'time_end': forms.TimeInput(attrs={'type': 'time'}),
            # Для интервала можно оставить текстовое поле, формат ввода: чч:мм:сс (например, 00:20:00)
            'interval': forms.TextInput(attrs={'placeholder': '00:20:00'}),
        }


from .models import Prescription, Drug, Diagnosis

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        # id_rec (Запись) мы проставим автоматически во view, поэтому исключаем из формы
        fields = ['id_diag', 'id_drug', 'frequency', 'duration', 'treatment']
        widgets = {
            'treatment': forms.Textarea(attrs={'rows': 3}),
            'duration': forms.TextInput(attrs={'placeholder': 'Например: 7 days'}),
        }



from .models import Appointment

class AppointmentEditForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'visit_time', 'cabinet']
        widgets = {
            # Для красоты используем HTML5 календарь
            'visit_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем секунды из формата, чтобы input type=datetime-local корректно отображал время
        if self.instance and self.instance.visit_time:
            self.initial['visit_time'] = self.instance.visit_time.strftime('%Y-%m-%dT%H:%M')