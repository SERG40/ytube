from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Пользователь
        cls.user = User.objects.create_user(username='Any')

        # Автор поста
        cls.user1 = User.objects.create_user(username='author')

        # Гость
        cls.guest_client = Client()

        # Авторизованый пользователь
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        # Автор поста
        cls.authorized_client1 = Client()
        cls.authorized_client1.force_login(cls.user1)

        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовая запись для создания нового поста'
        )

        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug',
            description='Описание для теста'
        )

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
