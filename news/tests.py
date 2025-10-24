import uuid
import time
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import Article
from django.http import JsonResponse

# --- Test 1: Model (Article) ---

class ArticleModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Setup data sekali untuk semua tes model."""
        cls.user = User.objects.create_user(username='modeluser', password='password')
        
        cls.article = Article.objects.create(
            author=cls.user,
            title="Test Article",
            content="Test content.",
            category='sepakbola',
            news_views=15,
            created_at=timezone.now() - timedelta(days=5) 
        )
        
        cls.hot_article = Article.objects.create(
            author=cls.user,
            title="Hot Article",
            content="Hot content.",
            category='moto gp',
            news_views=25,
            created_at=timezone.now() - timedelta(days=1)
        )
        
        cls.old_hot_article = Article.objects.create(
            author=cls.user,
            title="Old Hot Article",
            content="Old content.",
            category='f1',
            news_views=1000,
            created_at=timezone.now() - timedelta(days=3)
        )
        
        cls.new_cold_article = Article.objects.create(
            author=cls.user,
            title="New Cold Article",
            content="Cold content.",
            category='raket',
            news_views=5,
            created_at=timezone.now() - timedelta(days=1)
        )

    def test_str_method(self):
        """Test metode __str__ mengembalikan judul."""
        self.assertEqual(str(self.article), "Test Article")
        self.assertEqual(str(self.hot_article), "Hot Article")

    def test_default_values(self):
        """Test nilai default (news_views=0, category='sepakbola')"""
        user2 = User.objects.create_user(username='modeluser2', password='pw')
        new_article = Article.objects.create(author=user2, title="Default Test")
        self.assertEqual(new_article.news_views, 0)
        self.assertEqual(new_article.category, 'sepakbola') 
        self.assertIsNotNone(new_article.created_at) 
        self.assertIsInstance(new_article.id, uuid.UUID) 

    def test_get_absolute_url(self):
        """Test get_absolute_url mengarah ke URL detail yang benar."""
        expected_url = reverse('news:article-detail', kwargs={'pk': self.article.pk})
        self.assertEqual(self.article.get_absolute_url(), expected_url)

    def test_increment_views(self):
        """Test metode increment_views menambah views + 1 di database."""
        initial_views = self.article.news_views 
        self.article.increment_views()
        self.assertEqual(self.article.news_views, initial_views + 1)
        
        self.article.increment_views()
        self.assertEqual(self.article.news_views, initial_views + 2)

    def test_is_news_hot_property(self):
        """Test logika @property is_news_hot."""
        self.assertTrue(self.hot_article.is_news_hot)
        self.assertFalse(self.old_hot_article.is_news_hot)
        self.assertFalse(self.new_cold_article.is_news_hot)
        self.assertFalse(self.article.is_news_hot) 

# --- Test 2: Views Publik (Landing, List, Detail) ---

class PublicViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password')
        cls.client = Client()
        cls.list_url = reverse('news:article-list')
        cls.landing_url = reverse('landing-page') 

        Article.objects.create(title='Article 1 (Old)', content='Old.', author=cls.user, created_at=timezone.now() - timedelta(days=1))
        time.sleep(0.01) 
        cls.article_recent_3 = Article.objects.create(title='Article 2 (Recent 3)', content='Recent.', author=cls.user)
        time.sleep(0.01)
        cls.article_recent_2 = Article.objects.create(title='Article 3 (Recent 2)', content='Recent.', author=cls.user)
        time.sleep(0.01)
        cls.article_recent_1 = Article.objects.create(title='Article 4 (Recent 1)', content='Recent.', author=cls.user)
        
        for i in range(5, 11): 
            time.sleep(0.01) 
            Article.objects.create(
                title=f'Article {i}', content=f'Content {i}',
                author=cls.user,
                category='f1' if i % 2 == 0 else 'sepakbola' 
            )
        
        cls.detail_article = Article.objects.get(title='Article 10') 
        cls.detail_url = reverse('news:article-detail', kwargs={'pk': cls.detail_article.pk})

    def test_landing_page_status_code_and_template(self):
        """Test LandingPageView: status 200 dan template benar."""
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_landing_page_context(self):
        """Test LandingPageView: context 'hottest_articles' berisi 3 artikel terbaru."""
        response = self.client.get(self.landing_url)
        self.assertTrue('hottest_articles' in response.context)
        hottest = response.context['hottest_articles']
        self.assertEqual(len(hottest), 3)
        self.assertEqual(hottest[0].title, 'Article 10')
        self.assertEqual(hottest[1].title, 'Article 9')
        self.assertEqual(hottest[2].title, 'Article 8')

    def test_article_list_view_pagination(self):
        """Test ArticleListView: paginate_by = 9."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'news/article_list.html')
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['articles']), 9) 

    def test_article_list_view_page_2(self):
        """Test ArticleListView: halaman 2 berisi sisa artikel."""
        response = self.client.get(self.list_url + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['articles']), 1) 

    def test_article_list_category_filter(self):
        """Test ArticleListView: ?category=f1 berfungsi."""
        response = self.client.get(self.list_url + '?category=f1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_category'], 'f1')
        self.assertEqual(len(response.context['articles']), 3) 
        for article in response.context['articles']:
            self.assertEqual(article.category, 'f1')

    def test_article_list_ajax_refresh(self):
        """Test ArticleListView: request AJAX mengembalikan JSON partial HTML."""
        response = self.client.get(self.list_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse) 
        
        data = response.json()
        self.assertIn('html', data)
        self.assertIn('class="grid grid-cols-1', data['html'])
        self.assertNotIn('<nav x-data="{ isOpen: false }"', data['html'])
        self.assertIn('Halaman 1 dari 2.', data['html'])
    
    def test_article_list_ajax_refresh_with_filter(self):
        """Test AJAX refresh dengan filter tetap menggunakan filter."""
        response = self.client.get(self.list_url + '?category=f1', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['html'].count('class="bg-gray-800 rounded-lg'), 3)

    def test_article_detail_view(self):
        """Test ArticleDetailView: status 200, template, dan increment views."""
        initial_views = self.detail_article.news_views
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'news/article_detail.html')
        self.assertEqual(response.context['article'], self.detail_article)

        self.detail_article.refresh_from_db()
        self.assertEqual(self.detail_article.news_views, initial_views + 1)

    def test_article_detail_404(self):
        """Test ArticleDetailView: 404 untuk UUID yang tidak ada."""
        invalid_pk = uuid.uuid4()
        response = self.client.get(reverse('news:article-detail', kwargs={'pk': invalid_pk}))
        self.assertEqual(response.status_code, 404)


# --- Test 3: Views CRUD Terproteksi (Create, Update, Delete) ---

class ProtectedViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_author = User.objects.create_user(username='author', password='password')
        cls.user_other = User.objects.create_user(username='otheruser', password='password')
        cls.user_admin = User.objects.create_superuser(username='testadmin', password='password')

        cls.article = Article.objects.create(
            author=cls.user_author,
            title="Author's Article",
            content="Original Content",
            category='raket'
        )
        
        cls.create_url = reverse('news:article-create')
        cls.update_url = reverse('news:article-update', kwargs={'pk': cls.article.pk})
        cls.delete_url = reverse('news:article-delete', kwargs={'pk': cls.article.pk})
        cls.success_url = reverse('news:article-list') 
        cls.login_url = reverse('profile_user:login') 

    def test_create_view_redirects_anonymous(self):
        """Test ArticleCreateView: redirect jika belum login."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'{self.login_url}?next={self.create_url}')

    def test_logged_in_uses_correct_template(self):
        """Test view renders form template for logged-in users."""
        self.client.login(username='author', password='password')
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'news/article_form.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_create_article_post_anonymous(self):
        """Test anonymous POST redirects to login."""
        response = self.client.post(self.create_url, {
            'title': 'Anon Post', 'content': 'Should fail.', 'category': 'sepakbola'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'{self.login_url}?next={self.create_url}')
        self.assertEqual(Article.objects.count(), 1) 

    def test_create_article_post_logged_in_valid(self):
        """Test logged-in POST creates article and redirects."""
        self.client.login(username='author', password='password')
        post_data = {
            'title': 'New Post by Author', 
            'content': 'Valid content.', 
            'category': 'raket'
        }
        initial_count = Article.objects.count()
        response = self.client.post(self.create_url, post_data)
        
        self.assertEqual(Article.objects.count(), initial_count + 1)
        new_article = Article.objects.latest('created_at')
        self.assertEqual(new_article.title, 'New Post by Author')
        self.assertEqual(new_article.content, 'Valid content.')
        self.assertEqual(new_article.category, 'raket')
        self.assertEqual(new_article.author, self.user_author)
        
        self.assertRedirects(response, new_article.get_absolute_url())

    def test_create_article_post_toast_message(self):
        """Test create view shows success toast message."""
        self.client.login(username='author', password='password')
        response_followed = self.client.post(self.create_url, {
            'title': 'Another Post', 
            'content': '...',
            'category': 'sepakbola' 
        }, follow=True)
        
        self.assertContains(response_followed, "berhasil dibuat")
        messages_list = list(response_followed.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level_tag, 'success') 

    def test_create_article_post_logged_in_invalid(self):
        """Test logged-in POST with invalid data re-renders form."""
        self.client.login(username='author', password='password')
        initial_count = Article.objects.count()
        response = self.client.post(self.create_url, {
            'title': '', 
            'content': 'Invalid attempt.', 
            'category': 'f1'
        })
        self.assertEqual(response.status_code, 200) 
        self.assertTemplateUsed(response, 'news/article_form.html')
        self.assertFormError(response.context['form'], 'title', 'Bidang ini tidak boleh kosong.')
        self.assertEqual(Article.objects.count(), initial_count) 

    def test_update_view_permissions(self):
        """Test ArticleUpdateView: Cek izin akses (anonymous, other user, author, admin)."""
        response_anon = self.client.get(self.update_url)
        self.assertRedirects(response_anon, f'{self.login_url}?next={self.update_url}')
        
        self.client.login(username='otheruser', password='password')
        response_other = self.client.get(self.update_url)
        self.assertEqual(response_other.status_code, 403) 
        
        self.client.login(username='author', password='password')
        response_author = self.client.get(self.update_url)
        self.assertEqual(response_author.status_code, 200)
        self.assertTemplateUsed(response_author, 'news/article_form.html')
        self.assertContains(response_author, 'Original Content') 

        self.client.login(username='testadmin', password='password') 
        response_admin = self.client.get(self.update_url)
        self.assertEqual(response_admin.status_code, 200) 

    def test_update_view_post_no_changes(self):
        """Test ArticleUpdateView: POST tanpa perubahan memicu toast 'info'."""
        self.client.login(username='author', password='password')
        post_data = {
            'title': self.article.title, 
            'content': self.article.content,
            'category': self.article.category
        }
        response = self.client.post(self.update_url, post_data, follow=True)
        
        self.assertEqual(response.status_code, 200) 
        self.assertContains(response, "Tidak ada perubahan yang disimpan.")
        self.assertNotContains(response, "berhasil diperbarui")
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level_tag, 'info') 

    def test_update_view_post_with_changes(self):
        """Test ArticleUpdateView: POST dengan perubahan memicu toast 'success'."""
        self.client.login(username='author', password='password')
        post_data = {
            'title': 'UPDATED Title',
            'content': 'UPDATED Content',
            'category': 'moto gp'
        }
        response = self.client.post(self.update_url, post_data, follow=True)
        
        self.assertEqual(response.status_code, 200) 
        self.assertContains(response, "berhasil diperbarui")
        self.assertNotContains(response, "Tidak ada perubahan")
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level_tag, 'success') 
        
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'UPDATED Title')

    def test_delete_view_permissions(self):
        """Test ArticleDeleteView: Cek izin akses (anonymous, other user, author, admin)."""
        response_anon = self.client.get(self.delete_url)
        self.assertRedirects(response_anon, f'{self.login_url}?next={self.delete_url}')
        
        self.client.login(username='otheruser', password='password')
        response_other = self.client.get(self.delete_url)
        self.assertEqual(response_other.status_code, 403)
        
        self.client.login(username='author', password='password')
        response_author = self.client.get(self.delete_url)
        self.assertEqual(response_author.status_code, 200)
        self.assertTemplateUsed(response_author, 'news/article_confirm_delete.html')

        self.client.login(username='testadmin', password='password') 
        response_admin = self.client.get(self.delete_url)
        self.assertEqual(response_admin.status_code, 200)

    def test_delete_view_post_success(self):
        """Test ArticleDeleteView: POST berhasil menghapus objek dan memicu toast 'error' (merah)."""
        self.client.login(username='author', password='password')
        
        self.assertEqual(Article.objects.count(), 1)
        
        response = self.client.post(self.delete_url, follow=True)
        
        self.assertEqual(Article.objects.count(), 0)
        
        self.assertRedirects(response, self.success_url, status_code=302, target_status_code=200)

        self.assertContains(response, "berhasil dihapus")
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level_tag, 'error')