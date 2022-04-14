from django.contrib.auth import get_user_model
from django.test import TestCase
from django.conf import settings

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text=('Тестовый пост увеличенной длинныыыыыы'
                  [:settings.GLOBAL_NUMBERS_LAST_POST])
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        self.assertEqual(post.text, str(post.text))

    def test_verbose_name(self):
        """verbose_name и image поля совпадает с ожидаемым."""
        post = PostModelTest.post
        verbose = post._meta.get_field('author').verbose_name
        verbose2 = post._meta.get_field('group').verbose_name
        image_test = post._meta.get_field('image').verbose_name
        self.assertEqual(image_test, 'Картинка')
        self.assertEqual(verbose, 'Автор')
        self.assertEqual(verbose2, 'Группы')

    def test_help_text(self):
        """help_text поля совпадает с ожидаемым."""
        post = PostModelTest.post
        help = post._meta.get_field('text').help_text
        help2 = post._meta.get_field('group').help_text
        image_help = post._meta.get_field('image').help_text
        self.assertEqual(image_help, 'Поле изображения')
        self.assertEqual(help, 'Введите текст')
        self.assertEqual(help2, 'Выберите группу')


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_models_group_tittle(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
