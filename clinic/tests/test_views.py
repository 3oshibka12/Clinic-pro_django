from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from clinic.models import Doctor, Patient, Schedule, Appointment
from datetime import date, timedelta

class ViewIntegrationTest(TestCase):
    def setUp(self):
        self.user_pat = User.objects.create_user('patient1', 'pat@test.com', 'testpass')
        self.patient = Patient.objects.create(
            user=self.user_pat,
            fname='Patient', lname='One',
            birth_date='2000-01-01', region=1, email='pat@test.com'
        )
        self.user_doc = User.objects.create_user('doctor1', 'doc@test.com', 'testpass')
        self.doctor = Doctor.objects.create(
            user=self.user_doc,
            fname='Doc', lname='Two',
            specialization='General', region=1
        )
        Schedule.objects.create(
            doctor=self.doctor,
            day=1,
            time_start='08:00',
            time_end='12:00',
            interval=timedelta(minutes=30)
        )
        self.user_staff = User.objects.create_user(
            'manager', 'man@test.com', 'testpass', is_staff=True
        )

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clinic/home.html')

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'patient1',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('profile'))

    def test_profile_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('profile')}"
        )

    @patch('clinic.views.send_appointment_confirmation')
    def test_patient_booking_with_schedule(self, mock_send):
        self.client.login(username='patient1', password='testpass')
        days_until_monday = (7 - date.today().weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        booking_date = date.today() + timedelta(days=days_until_monday)

        url = reverse('doctor_booking', args=[self.doctor.pk])
        response = self.client.post(url, {
            'visit_date': booking_date.strftime('%Y-%m-%d'),
            'visit_time': '08:30'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('profile'))
        self.assertTrue(Appointment.objects.filter(patient=self.patient).exists())
        mock_send.assert_called_once()

    def test_manager_can_access_schedules(self):
        self.client.login(username='manager', password='testpass')
        response = self.client.get(reverse('manager_schedules'))
        self.assertEqual(response.status_code, 200)