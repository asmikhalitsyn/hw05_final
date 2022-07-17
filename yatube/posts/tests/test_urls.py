from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, Group, User

SLUG_OF_GROUP = 'test-slug'
USERNAME = 'TEST'
USERNAME_2 = 'test123'
URL_OF_INDEX = reverse('posts:index')
URL_OF_POSTS_OF_GROUP = reverse('posts:group_list', args=[SLUG_OF_GROUP])
URL_TO_CREATE_POST = reverse('posts:post_create')
URL_OF_PROFILE = reverse('posts:profile', args=[USERNAME])
URL_OF_404_PAGE = '/unexisting_page/'
URL_NEXT = '?next='
URL_OF_FOLLOW_INDEX = reverse('posts:follow_index')
URL_TO_FOLLOW = reverse('posts:profile_follow', args=[USERNAME])
URL_TO_UNFOLLOW = reverse('posts:profile_unfollow', args=[USERNAME])
LOGIN_URL = reverse('login')
LOGIN_URL_CREATE = f'{LOGIN_URL}{URL_NEXT}{URL_TO_CREATE_POST}'
LOGIN_URL_UNFOLLOW = f'{LOGIN_URL}{URL_NEXT}{URL_TO_UNFOLLOW}'
LOGIN_FOLLOW_INDEX = f'{LOGIN_URL}{URL_NEXT}{URL_OF_FOLLOW_INDEX}'


class PostURLTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.URL_OF_DETAIL_POST = reverse(
            'posts:post_detail',
            args=[cls.post.pk]
        )
        cls.URL_TO_EDIT_POST = reverse('posts:post_edit', args=[cls.post.pk])
        cls.LOGIN_URL_EDIT = f'{LOGIN_URL}{URL_NEXT}{cls.URL_TO_EDIT_POST}'
        cls.LOGIN_TO_FOLLOW = f'{LOGIN_URL}{URL_NEXT}{URL_TO_FOLLOW}'
        cls.guest = Client()
        cls.another = Client()
        cls.another_2 = Client()
        cls.another_2.force_login(cls.user_2)
        cls.another.force_login(cls.user)

    def setUp(self):
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cases = [
            [URL_OF_INDEX, self.guest, 'posts/index.html'],
            [URL_OF_POSTS_OF_GROUP, self.guest, 'posts/group_list.html'],
            [URL_OF_PROFILE, self.guest, 'posts/profile.html'],
            [self.URL_OF_DETAIL_POST, self.guest, 'posts/post_detail.html'],
            [self.URL_TO_EDIT_POST, self.another, 'posts/create_post.html'],
            [URL_TO_CREATE_POST, self.another, 'posts/create_post.html'],
            [URL_OF_FOLLOW_INDEX, self.another, 'posts/follow.html'],
        ]
        for url, client, template in cases:
            with self.subTest(url=url):
                self.assertTemplateUsed(client.get(url), template)

    def test_status_of_pages(self):
        cases = [
            [URL_OF_INDEX, self.guest, 200],
            [URL_OF_POSTS_OF_GROUP, self.guest, 200],
            [URL_OF_PROFILE, self.guest, 200],
            [self.URL_OF_DETAIL_POST, self.guest, 200],
            [self.URL_TO_EDIT_POST, self.guest, 302],
            [URL_TO_CREATE_POST, self.guest, 302],
            [self.URL_TO_EDIT_POST, self.another_2, 302],
            [URL_OF_FOLLOW_INDEX, self.another, 200],
            [URL_OF_FOLLOW_INDEX, self.guest, 302],
            [URL_TO_FOLLOW, self.another_2, 302],
            [URL_TO_FOLLOW, self.another, 302],
            [URL_TO_FOLLOW, self.guest, 302],
            [URL_TO_UNFOLLOW, self.another_2, 302],
            [URL_TO_UNFOLLOW, self.another, 404],
            [URL_TO_UNFOLLOW, self.guest, 302],

        ]
        for url, client, status in cases:
            with self.subTest(case=[url, client, status]):
                self.assertEqual(client.get(url).status_code, status)

    def test_url_redirect(self):
        cases = [
            [URL_TO_CREATE_POST, self.guest, LOGIN_URL_CREATE],
            [self.URL_TO_EDIT_POST, self.guest, self.LOGIN_URL_EDIT],
            [self.URL_TO_EDIT_POST, self.another_2, self.URL_OF_DETAIL_POST],
            [URL_TO_FOLLOW, self.another_2, URL_OF_PROFILE],
            [URL_TO_FOLLOW, self.another, URL_OF_PROFILE],
            [URL_TO_FOLLOW, self.guest, self.LOGIN_TO_FOLLOW],
            [URL_TO_UNFOLLOW, self.another_2, URL_OF_PROFILE],
            [URL_TO_UNFOLLOW, self.guest, LOGIN_URL_UNFOLLOW],
            [URL_OF_FOLLOW_INDEX, self.guest, LOGIN_FOLLOW_INDEX]
        ]
        for url, client, url_redirect in cases:
            with self.subTest(url_redirect=[url, client, url_redirect]):
                self.assertRedirects(
                    client.get(url, follow=True), url_redirect
                )
