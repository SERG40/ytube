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

    def test_urls_uses_correct_template(self):
        """URL использует соответствующий шаблон для всех пользователей."""
        # Шаблоны по адресам
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_detail(self):
        """Test post_detail"""
        response = self.guest_client.get(f'/posts/{self.post.id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_authorized(self):
        """Test post_create авторизованным"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_create_or_edit_guest_client(self):
        """Test post_create не авторизованным"""
        response = self.guest_client.get(f'posts/{self.post.id}/edit/')
        response2 = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response2.status_code, HTTPStatus.FOUND)

    def test_create_or_edit_authorized_client_not_author(self):
        """Test post_edit авторизованым"""
        response = self.authorized_client.get(f'posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_create_authorized_author(self):
        """Test post_edit авторизованым автором"""
        response = self.authorized_client1.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_authorized_not_author(self):
        """Test post_create авторизованым не автором"""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_template_post_edit(self):
        """Test шаблона post_edit авторизованым не автором"""
        response = self.authorized_client1.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_page_404(self):
        """Тест ошибки 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
