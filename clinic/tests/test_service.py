from django.test import SimpleTestCase
from unittest.mock import patch
from clinic.services import send_appointment_confirmation

class ServicesTest(SimpleTestCase):
    @patch('clinic.services.requests.post')
    def test_send_appointment_confirmation(self, mock_post):
        mock_post.return_value.status_code = 200
        send_appointment_confirmation(
            email='patient@example.com',
            patient_name='Test Patient',
            doctor_name='Test Doctor',
            visit_time=__import__('datetime').datetime(2026, 5, 1, 10, 0),
            cabinet=100
        )
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        self.assertIn('appointment-info', args[0])
        payload = kwargs['json']
        self.assertEqual(payload['email'], 'patient@example.com')