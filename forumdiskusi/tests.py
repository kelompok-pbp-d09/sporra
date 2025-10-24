from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.urls import reverse
from django.utils import timezone
from django.contrib import admin

from news.models import Article
from forumdiskusi.models import ForumDiskusi, Post, Vote
from forumdiskusi.admin import ForumDiskusiAdmin, PostAdmin, VoteAdmin


# ==========================
# TESTS FOR VIEWS COVERAGE
# ==========================
class ForumDiskusiViewsCoverageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='pass123')
        self.article = Article.objects.create(title="Test Article", content="Lorem ipsum", news_views=5)
        self.forum = ForumDiskusi.objects.create(article=self.article)
        self.post = Post.objects.create(forum=self.forum, author=self.user, content="Nice!")

    def test_forum_view_with_authenticated_user_and_votes(self):
        """Covers user_votes and comment.user_vote assignment"""
        Vote.objects.create(post=self.post, user=self.user, value=1)
        self.client.login(username='tester', password='pass123')
        response = self.client.get(reverse('forumdiskusi:forum', args=[self.article.pk]))
        self.assertEqual(response.status_code, 200)
        comments = response.context['comments']
        self.assertTrue(any(hasattr(c, 'user_vote') for c in comments))

    def test_add_comment_empty_content(self):
        """Covers 'Isi komentar tidak boleh kosong'"""
        self.client.login(username='tester', password='pass123')
        url = reverse('forumdiskusi:add_comment', args=[self.article.pk])
        response = self.client.post(url, {'content': ''})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_add_comment_invalid_request_method(self):
        """Covers 'Invalid request'"""
        self.client.login(username='tester', password='pass123')
        url = reverse('forumdiskusi:add_comment', args=[self.article.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_delete_comment_redirect_after_delete(self):
        """Covers redirect to forum after delete (non-AJAX request)"""
        self.client.login(username='tester', password='pass123')
        response = self.client.post(reverse('forumdiskusi:delete_comment', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('forumdiskusi:forum', args=[self.article.pk]), response.url)

    def test_vote_post_toggle_vote(self):
        """Covers branch where vote exists then deleted"""
        self.client.login(username='tester', password='pass123')
        vote_url = reverse('forumdiskusi:vote_post', args=[self.post.id])
        self.client.post(vote_url, {'vote': 'up'})
        response = self.client.post(vote_url, {'vote': 'up'})
        data = response.json()
        self.assertEqual(data['user_vote'], 0)
        self.assertEqual(response.status_code, 200)


# ==========================
# FUNCTIONAL TESTS FOR FORUM
# ==========================
class ForumDiskusiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='naila', password='testpass')
        self.other_user = User.objects.create_user(username='other', password='otherpass')
        self.article = Article.objects.create(title='Test Artikel', content='Isi artikel...', author=self.user)
        self.forum = ForumDiskusi.objects.create(article=self.article)

    def test_forum_view(self):
        url = reverse('forumdiskusi:forum', args=[self.article.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
        self.assertIn('comments', response.context)

    def test_forum_view_not_found(self):
        response = self.client.get(reverse('forumdiskusi:forum', args=['00000000-0000-0000-0000-000000000000']))
        self.assertEqual(response.status_code, 404)

    def test_add_comment_requires_login(self):
        url = reverse('forumdiskusi:add_comment', args=[self.article.pk])
        response = self.client.post(url, {'content': 'Komentar baru'})
        self.assertEqual(response.status_code, 302)

    def test_add_comment_success(self):
        self.client.login(username='naila', password='testpass')
        url = reverse('forumdiskusi:add_comment', args=[self.article.pk])
        response = self.client.post(url, {'content': 'Komentar baru'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(content='Komentar baru').exists())

    def test_add_comment_empty(self):
        self.client.login(username='naila', password='testpass')
        url = reverse('forumdiskusi:add_comment', args=[self.article.pk])
        response = self.client.post(url, {'content': ''}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_add_comment_get_method(self):
        self.client.login(username='naila', password='testpass')
        url = reverse('forumdiskusi:add_comment', args=[self.article.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_edit_comment_by_author(self):
        post = Post.objects.create(forum=self.forum, author=self.user, content='Awal')
        self.client.login(username='naila', password='testpass')
        url = reverse('forumdiskusi:edit_comment', args=[post.id])
        response = self.client.post(url, {'content': 'Edit baru'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        post.refresh_from_db()
        self.assertEqual(post.content, 'Edit baru')
        self.assertEqual(response.status_code, 200)

    def test_edit_comment_by_other_user(self):
        post = Post.objects.create(forum=self.forum, author=self.user, content='Awal')
        self.client.login(username='other', password='otherpass')
        url = reverse('forumdiskusi:edit_comment', args=[post.id])
        response = self.client.post(url, {'content': 'Edit tidak sah'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        post.refresh_from_db()
        self.assertEqual(post.content, 'Awal')

    def test_delete_comment_by_author(self):
        post = Post.objects.create(forum=self.forum, author=self.user, content='Hapus ini')
        self.client.login(username='naila', password='testpass')
        url = reverse('forumdiskusi:delete_comment', args=[post.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(id=post.id).exists())

    def test_delete_comment_by_other_user(self):
        post = Post.objects.create(forum=self.forum, author=self.user, content='Hapus ini')
        self.client.login(username='other', password='otherpass')
        url = reverse('forumdiskusi:delete_comment', args=[post.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(id=post.id).exists())

    def test_vote_up_and_down(self):
        post = Post.objects.create(forum=self.forum, author=self.other_user, content='Post voting')
        self.client.login(username='naila', password='testpass')
        url = reverse('forumdiskusi:vote_post', args=[post.id])
        self.client.post(url, {'vote': 'up'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        post.refresh_from_db()
        self.assertEqual(post.score, 1)
        response = self.client.post(url, {'vote': 'down'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        post.refresh_from_db()
        self.assertEqual(post.score, 0)
        self.assertEqual(response.json()['user_vote'], 0)

    def test_vote_invalid_value(self):
        post = Post.objects.create(forum=self.forum, author=self.other_user, content='Vote invalid')
        self.client.login(username='naila', password='testpass')
        url = reverse('forumdiskusi:vote_post', args=[post.id])
        response = self.client.post(url, {'vote': 'invalid'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)

    def test_vote_post_invalid_request(self):
        post = Post.objects.create(forum=self.forum, author=self.other_user, content='Test invalid vote')
        self.client.login(username='naila', password='testpass')
        url = reverse('forumdiskusi:vote_post', args=[post.id])
        response = self.client.get(url)
        self.assertIn(response.status_code, [400, 405])

    def test_str_methods(self):
        post = Post.objects.create(forum=self.forum, author=self.user, content='Halo dunia')
        vote = Vote.objects.create(post=post, user=self.user, value=1)
        self.assertIn('Forum Diskusi untuk', str(self.forum))
        self.assertIn('Halo dunia', str(post))
        self.assertIn('voted', str(vote))

    def test_admin_permissions(self):
        admin_instance = ForumDiskusiAdmin(ForumDiskusi, admin.site)
        self.assertFalse(admin_instance.has_add_permission(None))
        self.assertFalse(admin_instance.has_change_permission(None))
        self.assertFalse(admin_instance.has_delete_permission(None))

    def test_admin_permissions_all(self):
        admins = [
            ForumDiskusiAdmin(ForumDiskusi, admin.site),
            PostAdmin(Post, admin.site),
            VoteAdmin(Vote, admin.site),
        ]
        for adm in admins:
            self.assertFalse(adm.has_add_permission(None))
            self.assertFalse(adm.has_change_permission(None))
            self.assertFalse(adm.has_delete_permission(None))


# ==========================
# TESTS FOR ADMIN PERMISSIONS
# ==========================
class AdminPermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='naila', password='testpass')
        self.anon = AnonymousUser()
        self.article = Article.objects.create(title='Test Admin Article', content='content', author=self.user)
        self.forum = ForumDiskusi.objects.create(article=self.article)
        self.post = Post.objects.create(forum=self.forum, author=self.user, content='hi')
        self.vote = Vote.objects.create(post=self.post, user=self.user, value=1)

        self.forum_admin = ForumDiskusiAdmin(ForumDiskusi, admin.site)
        self.post_admin = PostAdmin(Post, admin.site)
        self.vote_admin = VoteAdmin(Vote, admin.site)

    def test_admin_has_permissions_return_false_for_anonymous_and_user(self):
        req_anon = self.factory.get('/admin/')
        req_anon.user = self.anon

        req_user = self.factory.get('/admin/')
        req_user.user = self.user

        admins = [self.forum_admin, self.post_admin, self.vote_admin]

        for adm in admins:
            self.assertFalse(adm.has_add_permission(req_anon))
            self.assertFalse(adm.has_change_permission(req_anon))
            self.assertFalse(adm.has_delete_permission(req_anon))
            self.assertFalse(adm.has_add_permission(req_user))
            self.assertFalse(adm.has_change_permission(req_user, obj=None))
            obj = self.forum if isinstance(adm, ForumDiskusiAdmin) else self.post if isinstance(adm, PostAdmin) else self.vote
            self.assertFalse(adm.has_change_permission(req_user, obj=obj))
            self.assertFalse(adm.has_delete_permission(req_user, obj=obj))
