from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Пользователь
        cls.user = User.objects.create_user(username='Any')

        # Гость
        cls.guest_client = Client()

        # Авторизованый пользователь
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_about(self):
        """Тест about доступность страниц"""
        response_author = self.guest_client.get('/about/author/')
        response_tech = self.guest_client.get('/about/tech/')
        self.assertEqual(response_author.status_code, HTTPStatus.OK)
        self.assertEqual(response_tech.status_code, HTTPStatus.OK)

    def test_users(self):
        """Тест users доступность страниц"""
        response_signup = self.guest_client.get('/auth/signup/')
        response_logout = self.authorized_client.get('/auth/logout/')
        response_login = self.guest_client.get('/auth/login/')
        self.assertEqual(response_signup.status_code, HTTPStatus.OK)
        self.assertEqual(response_logout.status_code, HTTPStatus.OK)
        self.assertEqual(response_login.status_code, HTTPStatus.OK)
