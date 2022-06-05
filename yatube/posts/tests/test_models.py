from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 5,
        )

    def test_post_has_correct_object_name(self):
        self.assertEqual(PostModelTest.post.text[:15], str(PostModelTest.post))

    def test_group_has_correct_object_name(self):
        self.assertEqual(PostModelTest.group.title, str(PostModelTest.group))
