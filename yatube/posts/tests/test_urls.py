from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostsURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test text',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTest.user)

    def test_static_url(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_templates(self):
        url_template_names = {
            '/': 'posts/index.html',
            f'/group/{PostsURLTest.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostsURLTest.user.username}/': 'posts/profile.html',
            f'/posts/{PostsURLTest.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostsURLTest.post.id}/edit/': 'posts/create_post.html',
            'unexisting_page': 'core/404.html',
        }
        for address, template in url_template_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_available_to_author(self):
        response = self.authorized_client.get(
            f'/posts/{PostsURLTest.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirects_anonymous_on_post_detail(self):
        response = self.guest_client.get(
            f'/posts/{PostsURLTest.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page_returns_404(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_exists_at_desired_location_authorized(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirects_anonymous_on_auth_login(self):
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_comment_url_redirects_anonymous_on_auth_login(self):
        response = self.guest_client.get(reverse('posts:add_comment', kwargs={
                                         'post_id': PostsURLTest.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_follow_url_redirects_anonymous_on_auth_login(self):
        response = self.guest_client.get(
            f'/profile/{PostsURLTest.user.username}/follow/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unfollow_url_redirects_anonymous_on_auth_login(self):
        response = self.guest_client.get(
            f'/profile/{PostsURLTest.user.username}/unfollow/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_follow_url_available_to_authorized_client(self):
        response = self.authorized_client.get(
            f'/profile/{PostsURLTest.user.username}/follow/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
