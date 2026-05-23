from django.test import TestCase
from clinic.forms import ScheduleForm, PrescriptionForm
from clinic.models import Doctor, Diagnosis, Drug
from datetime import time, timedelta

class ScheduleFormTest(TestCase):
    def setUp(self):
        self.doctor = Doctor.objects.create(
            fname='Test', lname='Doctor',
            specialization='General', region=1
        )

    def test_invalid_interval_format(self):
        form = ScheduleForm(data={
            'doctor': self.doctor.pk,
            'day': 1,
            'time_start': '09:00',
            'time_end': '17:00',
            'interval': 'bad',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('interval', form.errors)

    def test_missing_required_fields(self):
        form = ScheduleForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('doctor', form.errors)
        self.assertIn('day', form.errors)
        self.assertIn('time_start', form.errors)
        self.assertIn('time_end', form.errors)

    def test_valid_data(self):
        form = ScheduleForm(data={
            'doctor': self.doctor.pk,
            'day': 1,
            'time_start': '09:00',
            'time_end': '17:00',
            'interval': timedelta(minutes=20),
        })
        self.assertTrue(form.is_valid())

class PrescriptionFormTest(TestCase):
    def setUp(self):
        self.diag = Diagnosis.objects.create(name='Flu')
        self.drug = Drug.objects.create(name='Aspirin', moment='before')

    def test_valid_data(self):
        form = PrescriptionForm(data={
            'id_diag': self.diag.pk,
            'id_drug': self.drug.pk,
            'frequency': 3,
            'duration': '5 days',
            'treatment': 'Some treatment',
        })
        self.assertTrue(form.is_valid())

    def test_missing_frequency(self):
        form = PrescriptionForm(data={
            'id_diag': self.diag.pk,
            'id_drug': self.drug.pk,
            'duration': '5 days',
            'treatment': 'Rest',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('frequency', form.errors)