import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

from ..models import Post, Group, User, Comment, Follow
from ..settings import POSTS_PER_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SLUG_OF_GROUP = 'test_slug'
SLUG_OF_GROUP_2 = 'test_slug2'
USERNAME = 'TEST'
USERNAME_2 = 'TEST2'
USERNAME_3 = 'TEST3'
URL_OF_INDEX = reverse('posts:index')
URL_OF_POSTS_OF_GROUP = reverse('posts:group_list', args=[SLUG_OF_GROUP])
URL_OF_POSTS_OF_GROUP_2 = reverse('posts:group_list', args=[SLUG_OF_GROUP_2])
URL_TO_CREATE_POST = reverse('posts:post_create')
URL_OF_PROFILE = reverse('posts:profile', args=[USERNAME])
URL_OF_INDEX_FOLLOW = reverse('posts:follow_index')
URL_OF_FOLLOW = reverse('posts:profile_follow', args=[USERNAME_2])
URL_OF_UNFOLLOW = reverse('posts:profile_unfollow', args=[USERNAME])
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_2 = User.objects.create_user(username=USERNAME_2)
        cls.user_3 = User.objects.create_user(username=USERNAME_3)
        cls.group_2 = Group.objects.create(
            title='Заголовок 2',
            slug=SLUG_OF_GROUP_2
        )
        cls.group = Group.objects.create(
            title='Заголовок 1',
            slug=SLUG_OF_GROUP
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post=cls.post,
        )
        cls.URL_OF_DETAIL_POST = reverse(
            'posts:post_detail',
            args=[cls.post.pk]
        )
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.user_2,
        )
        cls.URL_TO_EDIT_POST = reverse('posts:post_edit', args=[cls.post.pk])
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.another = Client()
        cls.another_2 = Client()
        cls.authorized_client.force_login(cls.user)
        cls.another.force_login(cls.user_2)
        cls.another_2.force_login(cls.user_3)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def test_pages_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        cases = [
            [URL_OF_INDEX, self.guest_client, 'page_obj'],
            [URL_OF_POSTS_OF_GROUP, self.guest_client, 'page_obj'],
            [URL_OF_PROFILE, self.guest_client, 'page_obj'],
            [self.URL_OF_DETAIL_POST, self.guest_client, 'post'],
            [URL_OF_INDEX_FOLLOW, self.another, 'page_obj'],
        ]
        for url, client, key in cases:
            with self.subTest(url=url):
                response = client.get(url)
                obj = response.context.get(key)
                if key == 'page_obj':
                    self.assertEqual(len(obj), 1)
                    post = obj[0]
                else:
                    post = obj
                self.assertEqual(self.post.text, post.text)
                self.assertEqual(self.post.author, post.author)
                self.assertEqual(self.post.group, post.group)
                self.assertEqual(self.post.image, post.image)
                self.assertEqual(self.post.pk, post.pk)

    def test_group_pages_correct_context(self):
        """Шаблон group_pages сформирован с правильным контекстом."""
        response = self.authorized_client.get(URL_OF_POSTS_OF_GROUP)
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.pk, self.group.pk)
        self.assertEqual(group.description, self.group.description)

    def test_author_in_profile(self):
        response = self.guest_client.get(URL_OF_PROFILE)
        self.assertEqual(self.user, response.context['author'])

    def test_caching_page_of_index(self):
        response = self.guest_client.get(URL_OF_INDEX)
        Post.objects.all().delete()
        response_2 = self.guest_client.get(URL_OF_INDEX)
        self.assertEqual(response.content, response_2.content)
        cache.clear()
        response_3 = self.guest_client.get(URL_OF_INDEX)
        self.assertNotEqual(response.content, response_3.content)

    def test_profile_follow(self):
        Follow.objects.all().delete()
        self.authorized_client.get(URL_OF_FOLLOW)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user_2
            ).exists()
        )

    def test_profile_unfollow(self):
        self.another.get(URL_OF_UNFOLLOW)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_2,
                author=self.user
            ).exists()
        )

    def test_post_in_correct_group_and_follow_index(self):
        urls = [URL_OF_POSTS_OF_GROUP_2, URL_OF_INDEX_FOLLOW]
        for url in urls:
            with self.subTest(url=url):
                self.assertNotIn(
                    self.post,
                    self.authorized_client.get(url).context['page_obj'],
                )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_2 = User.objects.create_user(username=USERNAME_2)
        cls.group = Group.objects.create(
            title='Test group',
            slug=SLUG_OF_GROUP,
            description='Тестовое описание',
        )
        cls.follow = Follow.objects.create(
            user=cls.user_2,
            author=cls.user
        )
        Post.objects.bulk_create(Post(
            text=f'Тестовый пост {number}',
            author=cls.user,
            group=cls.group)
            for number in range(POSTS_PER_PAGE + 1))
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_2)

    def test_paginator(self):
        cases = [
            [URL_OF_INDEX, self.guest_client, POSTS_PER_PAGE],
            [URL_OF_POSTS_OF_GROUP, self.guest_client, POSTS_PER_PAGE],
            [URL_OF_PROFILE, self.guest_client, POSTS_PER_PAGE],
            [URL_OF_INDEX + "?page=2", self.guest_client, 1],
            [URL_OF_POSTS_OF_GROUP + "?page=2", self.guest_client, 1],
            [URL_OF_PROFILE + "?page=2", self.guest_client, 1],
            [URL_OF_INDEX_FOLLOW, self.authorized_client, POSTS_PER_PAGE]
        ]

        for url, client, expected in cases:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(
                    len(response.context.get('page_obj')), expected
                )
