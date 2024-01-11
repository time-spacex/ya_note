from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytest_django.asserts import assertRedirects

from notes.models import Note


User = get_user_model()


def get_response_object(client_type, url_namespace, args=None):
    """Универсальная функция получения объекта response."""
    url = reverse(url_namespace, args=args)
    response = client_type.get(url)
    return response


class TestRoutes(TestCase):
    """Класс для тестирования маршрутов."""

    @classmethod
    def setUpTestData(cls):
        """Подготовка данных перед тестами."""
        cls.admin = User.objects.create(username='Admin', is_staff=True)
        cls.admin_client = Client()
        cls.admin_client.force_login(cls.admin)
        cls.author = User.objects.create(username='Author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

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
                    get_response_object(
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
                    get_response_object(
                        client_type=self.admin_client,
                        url_namespace=name
                    ).status_code, HTTPStatus.OK
                )

    def test_pages_availability_for_different_users(self):
        """Тест доступа страницы заметки для автора и других пользователей."""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.admin, HTTPStatus.NOT_FOUND),
        )
        urls = ('notes:detail', 'notes:edit', 'notes:delete')
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in urls:
                with self.subTest(user=user, name=name):
                    self.assertEqual(
                        get_response_object(
                            client_type=self.client,
                            url_namespace=name,
                            args=(self.note.slug,)
                        ).status_code, status
                    )

    def test_redirects(self):
        """Тест редиректов для анонимного пользователя."""
        urls_args = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
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
