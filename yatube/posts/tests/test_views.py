import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse


from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestAuthor1')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
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
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            id=1,
            image=uploaded
        )
        cls.group_other = Group.objects.create(
            title='Тестовая группа2',
            slug='other-slug',
            description='Тестовое описание2'
        )
        cls.user2 = User.objects.create_user(username='TestAuthor2')
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def correct_context(self, page_objects):
        """Функция для проверки контекста на страницах"""
        cache.clear()
        template_page_objects = {
            page_objects.text: self.post.text,
            page_objects.pub_date: self.post.pub_date,
            page_objects.author: self.post.author,
            page_objects.group: self.post.group,
            page_objects.image: self.post.image,
        }
        for page_object, context in template_page_objects.items():
            with self.subTest(page_object=page_object):
                self.assertEqual(page_object, context)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'),
            reverse('posts:profile', kwargs={'username': self.user}): (
                'posts/profile.html'),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}): (
                'posts/post_detail.html'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}): (
                'posts/create_post.html'),
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_correct_context_index(self):
        """Правильный контекст на главной странице."""
        response = self.authorized_client.get(reverse('posts:index'))
        page_objects = response.context['page_obj'][0]
        self.correct_context(page_objects)

    def test_correct_context_index_follow(self):
        """Правильный контекст на главной странице подписок."""
        follow = reverse('posts:profile_follow', args=[self.user])
        self.authorized_client2.get(follow)
        response = self.authorized_client2.get(reverse('posts:follow_index'))
        page_objects = response.context['page_obj'][0]
        self.correct_context(page_objects)

    def test_unfollow_no_context(self):
        """
        Пост не попал на главную подписок когда отписался от пользователя.
        """
        unfollow = reverse('posts:profile_unfollow', args=[self.user])
        self.authorized_client2.get(unfollow)
        response = self.authorized_client2.get(reverse('posts:follow_index'))
        self.assertNotContains(response, self.post.text)

    def test_correct_context_group_list(self):
        """Правильный контекст на странице группы (фильтр по группе)."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        page_objects = response.context['page_obj'][0]
        self.correct_context(page_objects)

    def test_correct_context_profile(self):
        """
        Правильный контекст на странице пользователя (фильтр по пользователю).
        """
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user}))
        page_objects = response.context['page_obj'][0]
        self.correct_context(page_objects)

    def test_correct_context_post_detail(self):
        """Правильный контекст на странице поста (фильтр по post_id)."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        page_objects = response.context['post']
        self.correct_context(page_objects)

    def test_correct_context_post_create(self):
        """Правильный контекст создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_correct_context_post_edit(self):
        """Правильный контекст редактирования поста."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form = response.context['form']
        self.assertEqual(form['text'].value(), self.post.text)
        self.assertEqual(form['image'].value(), self.post.image)

    def test_post_create_not_other_group(self):
        """Пост с указанной группой не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_other.slug})
        )
        self.assertNotContains(response, self.post.text)

    def test_cache_index(self):
        """Проверка кэша. При удалении запись остается до очистки кэша."""
        posts1 = self.authorized_client.get(reverse('posts:index')).content
        Post.objects.filter(id=1).delete()
        posts2 = self.authorized_client.get(reverse('posts:index')).content
        self.assertTrue(posts1 == posts2)
        cache.clear()
        posts3 = self.authorized_client.get(reverse('posts:index')).content
        self.assertFalse(posts1 == posts3)

    def test_follow_unfollow(self):
        """Тест подписки на пользователя и отписки"""
        Follow.objects.all().delete()
        follow = reverse('posts:profile_follow', args=[self.user])
        self.authorized_client2.get(follow)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user2,
                author=self.user
            ).exists()
        )
        unfollow = reverse('posts:profile_unfollow', args=[self.user])
        self.authorized_client2.get(unfollow)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user2,
                author=self.user
            ).exists()
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestAuthor1')
        cls.client = Client()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.NUM_POSTS_TWO_PAGE = 5
        for i in (
            range(1, settings.NUMBER_POSTS_PAGE + cls.NUM_POSTS_TWO_PAGE + 1)
        ):
            Post.objects.create(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group,
            )
        cls.dict_one_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user}),
        ]

    def test_paginator_one_page(self):
        """
        Проверка что на страницах index, group_list, profile
        NUMBER_POSTS_PAGE постов
        """
        cache.clear()
        for dict_one_page in self.dict_one_pages:
            response = self.client.get(dict_one_page)
            self.assertEqual(
                len(response.context['page_obj']),
                settings.NUMBER_POSTS_PAGE
            )

    def test_paginator_two_page(self):
        """
        Проверка что на второй странице index, group_list, profile
        NUM_POSTS_TWO_PAGE постов
        """
        cache.clear()
        for dict_one_page in self.dict_one_pages:
            response = self.client.get(dict_one_page + '?page=2')
            self.assertEqual(
                len(response.context['page_obj']),
                self.NUM_POSTS_TWO_PAGE
            )
