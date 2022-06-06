import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User
from ..views import POSTS_PER_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        cls.user = User.objects.create_user(username='test-user')
        cls.user_no_follows = User.objects.create_user(
            username='user_without_follows')
        cls.user_following = User.objects.create_user(
            username='user_following')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description'
        )
        cls.other_group = Group.objects.create(
            title='Other test group',
            slug='other-test-slug',
            description='Other test description'
        )
        cls.post = Post.objects.create(
            text='Test post',
            author=cls.user,
            group=cls.group,
        )
        posts = [
            Post(
                author=cls.user,
                text=str(i),
                group=cls.group,
            ) for i in range(POSTS_PER_PAGE + 1)
        ]
        Post.objects.bulk_create(posts)

        # cls.small_gif = (
        #     b'\x47\x49\x46\x38\x39\x61\x02\x00'
        #     b'\x01\x00\x80\x00\x00\x00\x00\x00'
        #     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
        #     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
        #     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
        #     b'\x0A\x00\x3B'
        # )
        # cls.uploaded = SimpleUploadedFile(
        #     name='small.gif',
        #     content=cls.small_gif,
        #     content_type='image/gif'
        # )
        # cls.image_form_data = {
        #     'text': 'Пост с картинкой',
        #     'group': cls.group.id,
        #     'image': cls.uploaded,
        # }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTest.user)
        self.author_client = Client()
        self.author_client.force_login(PostsPagesTest.user_following)
        self.user_no_follows = Client()
        self.user_no_follows.force_login(PostsPagesTest.user_no_follows)

    def test_pages_uses_correct_templates(self):
        names_template_pages = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={
                'slug': PostsPagesTest.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': PostsPagesTest.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': PostsPagesTest.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                'post_id': PostsPagesTest.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',

        }

        for reverse_name, template in names_template_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_first_page_contains_ten_records(self):
        urls = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                    'slug': PostsPagesTest.group.slug}),
            reverse('posts:profile', kwargs={
                    'username': PostsPagesTest.user.username})]

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_second_page_contains_records(self):
        reverse_urls = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                    'slug': PostsPagesTest.group.slug}),
            reverse('posts:profile', kwargs={
                'username': PostsPagesTest.user.username})]

        for url in reverse_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url, {'page': 2})
                self.assertEqual(
                    len(response.context['page_obj']),
                    Post.objects.count() - POSTS_PER_PAGE)

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                    'post_id': PostsPagesTest.post.id}),
        )
        self.assertEqual(
            response.context['post'].text, PostsPagesTest.post.text)
        self.assertEqual(
            response.context['post'].author, PostsPagesTest.post.author)
        self.assertEqual(
            response.context['post'].group, PostsPagesTest.post.group)

    def test_post_edit_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsPagesTest.post.id}))

        for value, expected in PostsPagesTest.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))

        for value, expected in PostsPagesTest.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_with_group_exists_at_desired_location(self):
        reverse_urls = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                    'slug': PostsPagesTest.group.slug}),
            reverse('posts:profile', kwargs={
                    'username': PostsPagesTest.user.username
                    }),
        ]
        for url in reverse_urls:
            with self.subTest(reverse_url=url):
                response = self.authorized_client.get(url, {'page': 2})
                self.assertIn(PostsPagesTest.post,
                              response.context['page_obj'])

    def test_post_with_group_not_in_other_group(self):
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={
                'slug': PostsPagesTest.other_group.slug}), {'page': 2})
        self.assertNotIn(PostsPagesTest.post, response.context['page_obj'])

    def test_post_with_image_show_correct_context(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        image_form_data = {
            'text': 'Пост с картинкой',
            'group': PostsPagesTest.group.id,
            'image': uploaded,
        }
        reverse_urls = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={
                'username': PostsPagesTest.user.username
            }),
            reverse('posts:group_posts', kwargs={
                'slug': PostsPagesTest.group.slug
            }),
        ]
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=image_form_data,
            follow=True,
        )
        for url in reverse_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                post_image = response.context['page_obj'][0].image
                self.assertEqual(post_image, 'posts/small.gif')

    def test_post_detail_with_image_show_correct_context(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small1.gif',
            content=small_gif,
            content_type='image/gif'
        )
        image_form_data = {
            'text': 'Пост с картинкой',
            'group': PostsPagesTest.group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=image_form_data,
            follow=True,
        )
        post_detail_response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={
                'post_id': Post.objects.get(
                    text=image_form_data.get('text')).id}))
        post_detail_image = post_detail_response.context['post'].image
        self.assertEqual(post_detail_image, 'posts/small1.gif')

    def test_index_page_cache(self):
        form_data = {
            'text': 'Cache post'
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        cache.clear()
        response_before_delete = self.authorized_client.get(
            reverse('posts:index'))
        Post.objects.get(text=form_data.get('text')).delete()
        response_after_delete = self.authorized_client.get(
            reverse('posts:index'))
        self.assertEqual(response_before_delete.content,
                         response_after_delete.content)
        cache.clear()
        response_after_cache_clear = self.authorized_client.get(
            reverse('posts:index'))
        self.assertNotEqual(response_after_cache_clear.content,
                            response_after_delete.content)

    def test_authorized_user_can_follow(self):
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={
                        'username': PostsPagesTest.user_following.username}),

        )
        self.assertTrue(Follow.objects.filter(user=PostsPagesTest.user).filter(
            author=PostsPagesTest.user_following).exists())

    def test_authorized_user_can_unfollow(self):
        Follow.objects.create(
            user=PostsPagesTest.user, author=PostsPagesTest.user_following
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={
                        'username': PostsPagesTest.user_following.username}),
        )
        self.assertFalse(
            Follow.objects.filter(user=PostsPagesTest.user).filter(
                author=PostsPagesTest.user_following).exists())

    def test_author_post_appears_at_followers(self):
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostsPagesTest.user_following.username}),
        )
        form_data = {
            'text': 'Author post'
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        response_user_with_follows = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertIn(Post.objects.get(text=form_data.get('text')),
                      response_user_with_follows.context['page_obj'])

    def test_author_post_not_appears_at_non_followers(self):
        form_data = {
            'text': 'Author post'
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        response_user_with_no_follows = self.user_no_follows.get(
            reverse('posts:follow_index'))
        self.assertNotIn(Post.objects.get(text=form_data.get(
            'text')), response_user_with_no_follows.context['page_obj'])
