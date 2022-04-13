from django import forms

from .models import Post, Comment


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
