from django.test import TestCase
from django.urls import reverse

from ..urls import app_name

SLUG_OF_GROUP = 'test-slug'
USERNAME = 'TEST'
POST_ID = 1
CASES = [
    ['index', '/', None],
    ['group_list', f'/group/{SLUG_OF_GROUP}/', [SLUG_OF_GROUP]],
    ['profile', f'/profile/{USERNAME}/', [USERNAME]],
    ['post_detail', f'/posts/{POST_ID}/', [POST_ID]],
    ['post_edit', f'/posts/{POST_ID}/edit/', [POST_ID]],
    ['post_create', '/create/', None],
    ['add_comment', f'/posts/{POST_ID}/comment/', [POST_ID]],
    ['follow_index', '/follow/', None],
    ['profile_follow', f'/profile/{USERNAME}/follow/', [USERNAME]],
    ['profile_unfollow', f'/profile/{USERNAME}/unfollow/', [USERNAME]],
]


class PostRoutesTests(TestCase):

    def test_correct_routes(self):
        for route, url, args in CASES:
            with self.subTest(name_of_route=route):
                self.assertEqual(
                    reverse(f'{app_name}:{route}', args=args), url
                )
