import shutil
import tempfile

from ..models import Post, Group, User

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SLUG_OF_GROUP = 'test_slug'
SLUG_OF_GROUP_2 = 'test_slug2'
URL_TO_CREATE_POST = reverse('posts:post_create')
URL_OF_PROFILE = reverse('posts:profile', args=['test'])
URL_OF_POSTS_OF_GROUP = reverse('posts:group_list', args=[SLUG_OF_GROUP])
URL_OF_INDEX = reverse('posts:index')
small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.group = Group.objects.create(
            title='Test group',
            slug=SLUG_OF_GROUP,
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Test group2',
            slug=SLUG_OF_GROUP_2,
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост')
        cls.post_2 = Post.objects.create(
            author=cls.user,
            text='Тестовый пост77')
        cls.URL_OF_DETAIL_POST = reverse(
            'posts:post_detail',
            args=[cls.post.pk]
        )
        cls.URL_TO_EDIT_POST = reverse('posts:post_edit', args=[cls.post.pk])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_task(self):
        post_all = set(Post.objects.all())
        form_data = {
            'text': 'Текст12345',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            URL_TO_CREATE_POST, data=form_data, follow=True
        )
        post_all_with_new_post = set(Post.objects.all())
        posts_obj = post_all_with_new_post.difference(post_all)
        self.assertEqual(len(posts_obj), 1)
        new_post = posts_obj.pop()
        self.assertRedirects(response, URL_OF_PROFILE)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(new_post.author, self.user)

    def test_edit_post(self):
        form_data = {
            'text': 'Измененный пост',
            'group': self.group_2.id
        }
        response_edit = self.authorized_client.post(
            self.URL_TO_EDIT_POST, data=form_data, follow=True
        )
        post = response_edit.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertRedirects(response_edit, self.URL_OF_DETAIL_POST)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit и post_create
          сформированы с правильными контекстами."""
        self.URLS_LIST = [self.URL_TO_EDIT_POST, URL_TO_CREATE_POST]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url in self.URLS_LIST:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_create_with_image(self):
        post_all = set(Post.objects.all())
        tasks_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='img.gif',
            content=small_gif,
            content_type='posts/img.gif'
        )
        form_data = {
            'text': 'Тестовый тексттекст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            URL_TO_CREATE_POST, data=form_data, follow=True
        )
        post_all_with_new_post = set(Post.objects.all())
        posts_obj = post_all_with_new_post.difference(post_all)
        self.assertEqual(len(posts_obj), 1)
        new_post = posts_obj.pop()
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertRedirects(response, URL_OF_PROFILE)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(new_post.image, form_data['image'].content_type)
        self.assertEqual(new_post.author, self.user)
