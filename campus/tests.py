from django.test import TestCase
from rest_framework.test import APIClient
from .models import Notification

class NotificationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        Notification.objects.create(
            title="Test Notification",
            message="Test Message",
            notification_type="general"
        )

    def test_get_notifications(self):
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['notification_type'], 'general')
