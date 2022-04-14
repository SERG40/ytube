from http import HTTPStatus

import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.models import Post, Group, Comment, Follow


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsURLTests(TestCase):
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

        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug',
            description='Описание для теста')
        cls.group2 = Group.objects.create(
            title='Заголовок для тестовой группы2',
            slug='test_slug2',
            description='Описание для теста2')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=cls.group)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUP(self):
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.post = Post.objects.create(
            text='Test',
            group=self.group,
            author=self.user,
            image=self.uploaded
        )

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': f'{self.user}'})
            ),
            'posts/group_list.html': (
                reverse('posts:group_list',
                        kwargs={'slug': f'{self.group.slug}'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': f'{self.post.id}'})
            ),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/follow.html': reverse('posts:follow_index')
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_use_correct_template(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text,
                         self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_group_pages_show_correct_context(self):
        """Шаблон группы"""
        response = self.authorized_client.get(
            reverse
            ('posts:group_list',
                kwargs={'slug': f'{self.group.slug}'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text,
                         self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)
        self.assertEqual(self.post.group, self.group)
        # Доп проверка index что пост появился в группе.
        object = response.context.get('page_obj').object_list
        self.assertIn(self.post, object)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': f'{self.user}'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group.slug, self.group.slug)
        self.assertEqual(first_object.image, self.post.image)
        self.assertEqual(self.post.author, self.user)
        # Доп проверка index что пост появился в profile.
        object = response.context.get('page_obj').object_list
        self.assertIn(self.post, object)

    def test_post_detail_correct_context(self):
        """Проверка context post_detail."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'}))
        first_object = response.context['post']
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group.title, self.group.title)
        self.assertEqual(first_object.image, self.post.image)

    def test_comment(self):
        """Проверка коментария."""
        comment_count = Comment.objects.count()
        self.comment = Comment.objects.create(
            author=self.user,
            post=self.post,
            text='test-comment'
        )
        form_data = {
            'text': 'Тестовый комент'
        }
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        form_fields = {
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        """Форма создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_filter_id_show_correct_context(self):
        """Форма редактирования поста отфильтрованого по id."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{self.post.id}'}))
        first_object = response.context['post']
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.text, self.post.text)
        second_object = response.context['is_edit']
        self.assertTrue(second_object)
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_when_setting_a_post_index_create_OK(self):
        """Доп проверка index что пост создался в группе А,но не в группе Б."""
        response = self.authorized_client.get(
            reverse
            ('posts:group_list',
                kwargs={'slug': self.group2.slug}))
        object = response.context.get('page_obj').object_list
        self.assertNotIn(self.post, object)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name',)
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug',
            description='Тестовое описание')
        cls.posts = []
        for i in range(settings.GLOBAL_NUMBER_POSTS):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='User')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        """Работает пагинатор 10 страниц."""
        list_urls = {
            reverse('posts:index'): 'index',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'group_list',
            reverse("posts:profile",
                    kwargs={'username': self.author}): 'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(
                len(response.context.get
                    ('page_obj').object_list), (settings.GLOBAL_FOR_PAGINATOR))

    def test_second_page_contains_three_posts(self):
        """Пагинатор выводит остаток страниц
          все что выше 10 на новой странице."""
        list_urls = {
            reverse('posts:index') + '?page=2': 'index',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2':
            'group_list',
            reverse('posts:profile',
                    kwargs={'username': self.author}) + '?page=2':
            'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list),
                (settings.GLOBAL_NUMBER_POSTS - settings.GLOBAL_FOR_PAGINATOR))


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Any')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест запись')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Тест кэш страницы index"""
        response = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Измененный текст'
        post_1.save()
        response2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response2.content)
        cache.clear()
        response3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response3.content)


class FollowTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        """ Тест follow."""
        count_follow = Follow.objects.count()
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.count(), count_follow + 1)

    def test_unfollow(self):
        """ Тест unfollow."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)

        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_guest(self):
        """Тест что гостя перенаправит на регистрацию."""
        response = self.guest_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
