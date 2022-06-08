from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase


from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.user_author = User.objects.create_user(username='user_author')
        cls.authorized_user_author = Client()
        cls.authorized_user_author.force_login(cls.user_author)
        Post.objects.create(
            text='Тестовый пост',
            author=cls.user_author,
            id=1
        )

    def test_url_available_any_user(self):
        """Страницы доступны любому пользователю"""
        template_url_names = (
            '/',
            '/group/test-slug/',
            '/profile/auth/',
            '/posts/1/',
        )
        for addres in template_url_names:
            with self.subTest(addres=addres):
                response = self.guest_client.get(addres)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_unexisting_page(self):
        """Несуществующая страница выдаст ошибку 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_unexisting_page_correct_template(self):
        """Несуществующая страница использует соответствующий шаблон"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_url_available_author_user(self):
        """Страница /posts/1/edit/ доступна автору"""
        response = self.authorized_user_author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_available_login_user(self):
        """Страница /create/ доступна авторизованному пользователю"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_list_url_redirect_anonymous_on_admin_login(self):
        """Страницы по адресам перенаправят анонимуса на авторизацию"""
        template_url_names = (
            '/posts/1/edit/',
            '/create/',
            '/posts/1/comment/'
        )
        for addres in template_url_names:
            with self.subTest(addres=addres):
                response = self.guest_client.get(addres, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={addres}')

    def test_url_edit_redirect_post_detail(self):
        """Страница /posts/1/edit/ перенаправит авторизованного пользователя
        на адрес поста.
        """
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        template_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in template_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_user_author.get(address)
                self.assertTemplateUsed(response, template)
