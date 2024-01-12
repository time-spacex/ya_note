from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING


User = get_user_model()


NOTE_TITLE = 'Заголовок'
NOTE_TEXT = 'Текст заметки'
NOTE_SLUG = 'note-slug'


class TestNotes(TestCase):
    """Класс тестов логики работы с заметками."""

    @classmethod
    def setUpTestData(cls):
        """Подготовка данных перед всеми тестами."""
        cls.reader = User.objects.create(username='Reader')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.author = User.objects.create(username='Author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title=NOTE_TITLE,
            text=NOTE_TEXT,
            slug=NOTE_SLUG,
            author=cls.author,
        )
        cls.note_slug = (cls.note.slug,)
        cls.FORM_DATA = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }

    def test_user_can_create_note(self):
        """Тест возможности создать заметку авторизованному пользователю."""
        Note.objects.all().delete()
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.FORM_DATA)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.FORM_DATA['title'])
        self.assertEqual(new_note.text, self.FORM_DATA['text'])
        self.assertEqual(new_note.slug, self.FORM_DATA['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Тест невозможности создать заметку анонимному пользователю."""
        notes_count = Note.objects.count()
        url = reverse('notes:add')
        response = self.client.post(url, data=self.FORM_DATA)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), notes_count)

    def test_not_unique_slug(self):
        """Тест невозможности создания заметки с неуникальным полем slug."""
        notes_count = Note.objects.count()
        url = reverse('notes:add')
        self.FORM_DATA['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.FORM_DATA)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), notes_count)

    def test_empty_slug(self):
        """Тест автоматического формирования поля slug."""
        Note.objects.all().delete()
        url = reverse('notes:add')
        self.FORM_DATA.pop('slug')
        response = self.author_client.post(url, data=self.FORM_DATA)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.FORM_DATA['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Тест возможности автором редактирования совей заметки."""
        url = reverse('notes:edit', args=self.note_slug)
        response = self.author_client.post(url, data=self.FORM_DATA)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.FORM_DATA['title'])
        self.assertEqual(self.note.text, self.FORM_DATA['text'])
        self.assertEqual(self.note.slug, self.FORM_DATA['slug'])

    def test_other_user_cant_edit_note(self):
        """Тест невозможности редактирования не совей заметки."""
        url = reverse('notes:edit', args=self.note_slug)
        response = self.reader_client.post(url, self.FORM_DATA)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, NOTE_TITLE)
        self.assertEqual(self.note.text, NOTE_TEXT)
        self.assertEqual(self.note.slug, NOTE_SLUG)

    def test_author_can_delete_note(self):
        """Тест возможности удаления автором совей заметки."""
        notes_count = Note.objects.count()
        url = reverse('notes:delete', args=self.note_slug)
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), notes_count - 1)

    def test_other_user_cant_delete_note(self):
        """Тест невозможности удаления несовей заметки."""
        notes_count = Note.objects.count()
        url = reverse('notes:delete', args=self.note_slug)
        response = self.reader_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), notes_count)
