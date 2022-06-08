import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_create_post(self):
        form_data = {
            'text': 'Проверка поста',
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:profile', kwargs={
                             'username': PostFormTest.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(text=form_data.get('text')).exists()
        )

    def test_post_edit(self):
        form_data = {
            'text': 'Новый тестовый текст',
        }
        self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTest.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.get(
            id=PostFormTest.post.id).text, 'Новый тестовый текст')

    def test_create_post_with_image(self):
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Пост с картинкой',
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(text=form_data.get('text')).exists()
        )

    def test_add_comment(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                    'post_id': PostFormTest.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
