from django import forms

from .models import Post, Comment, Follow


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')

        widgets = {
            'text': forms.Textarea(),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}


class FollowForm(forms.ModelForm):
    class Meta:
        model = Follow
        fields = ('user',)
        labels = {'user': 'Подписка на:', 'author': 'Автор записи'}
