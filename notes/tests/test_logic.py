from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING

from pytils.translit import slugify


User = get_user_model()


class TestNotes(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Подготовка данных перед всеми тестами."""
        cls.admin = User.objects.create(username='Admin', is_staff=True)
        cls.admin_client = Client()
        cls.admin_client.force_login(cls.admin)
        cls.author = User.objects.create(username='Author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
    
    def setUp(self):
        """Подготовка данных перед каждым тестом."""
        self.FORM_DATA = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=self.author,
        )

    def test_user_can_create_note(self):
        """Тест возможности создать заметку авторизованному пользователю."""
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.FORM_DATA)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.last()
        self.assertEqual(new_note.title, self.FORM_DATA['title'])
        self.assertEqual(new_note.text, self.FORM_DATA['text'])
        self.assertEqual(new_note.slug, self.FORM_DATA['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Тест невозможности создать заметку анонимному пользователю."""
        url = reverse('notes:add')
        response = self.client.post(url, data=self.FORM_DATA)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        """Тест невозможности создания заметки с неуникальным полем slug."""
        url = reverse('notes:add')
        self.FORM_DATA['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.FORM_DATA)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """Тест автоматического формирования поля slug."""
        url = reverse('notes:add')
        self.FORM_DATA.pop('slug')
        response = self.author_client.post(url, data=self.FORM_DATA)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.last()
        expected_slug = slugify(self.FORM_DATA['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Тест возможности автором редактирования совей заметки."""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, data=self.FORM_DATA)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.FORM_DATA['title'])
        self.assertEqual(self.note.text, self.FORM_DATA['text'])
        self.assertEqual(self.note.slug, self.FORM_DATA['slug'])

    def test_other_user_cant_edit_note(self):
        """Тест невозможности редактирования не совей заметки."""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.admin_client.post(url, self.FORM_DATA)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        """Тест возможности удаления автором совей заметки."""
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)
    
    def test_other_user_cant_delete_note(self):
        """Тест невозможности удаления несовей заметки."""
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.admin_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
