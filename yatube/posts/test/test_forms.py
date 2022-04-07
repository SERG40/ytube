import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.models import Group, Post
from posts.forms import PostForm
from http import HTTPStatus

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.group2 = Group.objects.create(
            title=('Заголовок для тестовой группы2'),
            slug='test_slug2',
            description='Тестовое описание2'
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.user = User.objects.create_user(username='author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post(self):
        """Cоздаётся новая запись в базе данных"""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_1 = Post.objects.order_by('pub_date').last()
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': f'{self.user}'}))
        self.assertEqual(post_1.text, form_data['text'])
        self.assertEqual(post_1.author, self.user)
        self.assertEqual(post_1.group, self.group)

    def test_edit_post(self):
        """Изменение поста с post_id в базе данных"""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост Тестовый пост',
            group=self.group
        )
        form_data = {
            'text': 'Измененный текст',
            'group': self.group2.id
        }
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': post.id
                    }),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.latest('id')
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_2.text, form_data['text'])
        self.assertEqual(post_2.author, self.user)
        self.assertEqual(post_2.group, self.group2)
        self.assertEqual(post_2.pub_date, post.pub_date)

    def create_post_with_group(self):
        """ Корректно создается пост без группы"""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Данные из формы'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.last()
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': f'{self.user}'}))
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)

    def test_if_form_no_valid(self):
        """Не создаются посты, если передаем не валидную форму"""
        BAD_ID = 3
        count_posts = Post.objects.count()
        # Тест на пустую строчку
        form_data = {
            'text': ''
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), count_posts)
        # Тест на неверный id группы
        form_data2 = {
            'text': 'Данные из формы',
            'group': BAD_ID
        }
        response2 = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data2,
            follow=True,
        )
        self.assertEqual(response2.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), count_posts)

    def test_post_edit_without_change_group(self):
        """Проверяем, что валидная форма, без изменения группы
        редактирует запись в Post."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост Тестовый пост',
            group=self.group,
        )
        form_data = {
            'text': '123'
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        get_post = Post.objects.get(id=post.id)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id}))
        self.assertEqual(get_post.text, form_data['text'])
        self.assertEqual(get_post.author, self.user)

    def test_POST_request_guest_client(self):
        """При POST запросе неавторизованного пользователя пост
        не будет отредактирован, произойдет редирект
        на корректную страницу"""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост Тестовый пост',
            group=self.group,
        )
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Данные из формы',
            'group': ''
        }

        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data)
        response2 = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        get_post = Post.objects.get(id=post.id)
        self.assertEqual(get_post.author, self.user)
        self.assertEqual(get_post.group, self.group)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            reverse('users:login') + '?next='
            + reverse('posts:post_edit', kwargs={'post_id': post.id}))
        self.assertRedirects(
            response2,
            reverse('users:login') + '?next='
            + reverse('posts:post_create'))
        self.assertEqual(Post.objects.count(), count_posts)

    def test_POST_request_authorized_not_author(self):
        """При POST запросе авторизованного пользователя, но не автора поста,
        post не будет отредактирован, произойдет редирект
        на корректную страницу"""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост Тестовый пост',
            group=self.group,
        )
        form_data = {
            'text': 'Данные из формы',
            'group': ''
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data)
        get_post = Post.objects.get(id=post.id)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(get_post.author, self.user)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.id}))

    def test_create_post(self):
        count_posts = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Пост с картинкой',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': f'{self.user}'}))
