from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):
    """Класс для тестирования маршрутов."""

    def get_response_object(self, client_type, url_namespace, args=None):
        """Универсальный метод получения объекта response."""
        url = reverse(url_namespace, args=args)
        response = client_type.get(url)
        return response

    @classmethod
    def setUpTestData(cls):
        """Подготовка данных перед тестами."""
        cls.reader = User.objects.create(username='Reader')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.author = User.objects.create(username='Author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )
        cls.note_slug = (cls.note.slug,)

    def get_response_object(self, client_type, url_namespace, args=None):
        """Универсальный метод получения объекта response."""
        url = reverse(url_namespace, args=args)
        response = client_type.get(url)
        return response

    def test_pages_availability(self):
        """Тест доступности страниц для всех пользователей."""
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup'
        )
        for name in urls:
            with self.subTest(name=name):
                self.assertEqual(
                    self.get_response_object(
                        client_type=self.client,
                        url_namespace=name
                    ).status_code, HTTPStatus.OK
                )

    def test_pages_availability_for_auth_user(self):
        """Тест доступности страниц для авторизованного пользователя."""
        urls = ('notes:list', 'notes:add', 'notes:success')
        for name in urls:
            with self.subTest(name=name):
                self.assertEqual(
                    self.get_response_object(
                        client_type=self.reader_client,
                        url_namespace=name
                    ).status_code, HTTPStatus.OK
                )

    def test_pages_availability_for_different_users(self):
        """Тест доступа страницы заметки для автора и других пользователей."""
        users_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )
        urls = ('notes:detail', 'notes:edit', 'notes:delete')
        for user, status in users_statuses:
            for name in urls:
                with self.subTest(user=user, name=name):
                    self.assertEqual(
                        self.get_response_object(
                            client_type=user,
                            url_namespace=name,
                            args=self.note_slug
                        ).status_code, status
                    )

    def test_redirects(self):
        """Тест редиректов для анонимного пользователя."""
        urls_args = (
            ('notes:detail', self.note_slug),
            ('notes:edit', self.note_slug),
            ('notes:delete', self.note_slug),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        login_url = reverse('users:login')
        for name, args in urls_args:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                expected_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                assertRedirects(response, expected_url)
