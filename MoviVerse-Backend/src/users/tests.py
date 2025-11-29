from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserTestCase(TestCase):
    def test_create_user(self):
        u = User.objects.create_user(username="test", password="password123")
        self.assertTrue(u.check_password("password123"))
