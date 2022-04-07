from tkinter import CASCADE
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    text = models.TextField(verbose_name='Текст', help_text='Введите текст')
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey('Group', models.SET_NULL, blank=True,
                              null=True,
                              related_name='posts',
                              verbose_name='Группы',
                              help_text='Выберите группу')
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self) -> str:
        return self.text

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Имя')
    slug = models.SlugField(max_length=50, unique=True,)
    description = models.TextField(max_length=300, verbose_name='Описание')

    class Meta:
        ordering = ('-title',)
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments")
    text = models.TextField()
    created = models.DateTimeField("date published", auto_now_add=True)

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following')

    def __str__(self):
        return self.text
