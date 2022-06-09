from core.models import CreatedModel


from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.db import models


User = get_user_model()


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Текст нового поста',
        validators=[
            MinLengthValidator(
                2,
                'Пост должен состоять минимум из двух символов'
            )
        ]
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='group_posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        help_text='Можете добавить изображение к посту',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text[:settings.NUMBER_SYMBOL_TEXT_POST]

    class Meta:
        ordering = ['-pub_date']


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Comment(CreatedModel):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Текст нового комментария',
        validators=[
            MinLengthValidator(
                1,
                'Комментарий должен состоять минимум из двух символов'
            )
        ]
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь, который подписывается'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Пользователь, на которого подписываются'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow')
        ]
