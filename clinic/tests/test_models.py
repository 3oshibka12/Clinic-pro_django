from django.test import TestCase
from django.contrib.auth.models import User
from clinic.models import Doctor, Patient, Appointment, Diagnosis, Drug, Prescription
from datetime import timedelta
from django.test import SimpleTestCase
from clinic.models import Doctor

class DoctorModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('doc1', 'doc@example.com', 'password')
        self.doctor = Doctor.objects.create(
            user=self.user,
            fname='John', lname='Doe',
            specialization='Cardiology', region=1
        )

    def test_string_representation(self):
        self.assertEqual(str(self.doctor), 'Doe John (Cardiology)')

    def test_full_name_property(self):
        self.assertEqual(self.doctor.full_name, 'Doe John')

class PatientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pat1', 'pat@example.com', 'password')
        self.patient = Patient.objects.create(
            user=self.user,
            fname='Jane', lname='Roe',
            birth_date='1990-01-01', region=2
        )

    def test_string_representation(self):
        self.assertEqual(str(self.patient), 'Roe Jane')

    def test_email_field(self):
        self.assertEqual(self.patient.email, 'lasenkob213@gmail.com')

class AppointmentModelTest(TestCase):
    def setUp(self):
        user_doc = User.objects.create_user('doc2', 'doc2@example.com', 'pass')
        user_pat = User.objects.create_user('pat2', 'pat2@example.com', 'pass')
        self.doctor = Doctor.objects.create(
            user=user_doc, fname='A', lname='B',
            specialization='Derm', region=1
        )
        self.patient = Patient.objects.create(
            user=user_pat, fname='C', lname='D',
            birth_date='1995-05-05', region=1
        )
        self.appointment = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            visit_time='2026-05-01T10:00:00Z', cabinet=101
        )

    def test_get_prescription_when_none(self):
        self.assertIsNone(self.appointment.get_prescription)

    def test_get_prescription_exists(self):
        diag = Diagnosis.objects.create(name='Flu')
        drug = Drug.objects.create(name='Aspirin', moment='before')
        presc = Prescription.objects.create(
            id_rec=self.appointment,
            id_diag=diag,
            id_drug=drug,
            frequency=2,
            duration=timedelta(days=7),
            treatment='Rest'
        )
        self.assertEqual(self.appointment.get_prescription, presc)

# Unit тесты
class DoctorPropertyUnitTest(SimpleTestCase):

    def test_full_name_concatenates_last_and_first_name(self):
        doctor = Doctor(fname='John', lname='Doe')
        self.assertEqual(doctor.full_name, 'Doe John')

    def test_full_name_with_middle_name(self):
        doctor = Doctor(fname='Anna Maria', lname='Sokolova')
        self.assertEqual(doctor.full_name, 'Sokolova Anna Maria')