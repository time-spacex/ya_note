from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm


User = get_user_model()


class TestContent(TestCase):
    """Класс для тестирования контента страниц."""

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

    def test_notes_list_for_different_users(self):
        """Тест отображения списка заметок для разных пользователей."""
        user_note_in_list = (
            (self.author_client, True),
            (self.reader_client, False),
        )
        for user, note_in_list in user_note_in_list:
            with self.subTest(user=user):
                url = reverse('notes:list')
                response = user.get(url)
                object_list = response.context['object_list']
                self.assertIs((self.note in object_list), note_in_list)

    def test_pages_contains_form(self):
        """Тест формы на страницах создания и редактирования заметки."""
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
