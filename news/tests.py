import uuid
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Article
class ArticleModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = User.objects.create_user(username='testuser', password='password')

        cls.article = Article.objects.create(
            title='Test Article Title',
            content='This is the test content.',
            author=cls.user,
            category='f1', 
            news_views=15 
        )
        

        cls.default_article = Article.objects.create(
            title='Default Article',
            content='Default content.',
            author=cls.user

        )

    def test_str_representation(self):

        self.assertEqual(str(self.article), 'Test Article Title')
        self.assertEqual(str(self.default_article), 'Default Article')

    def test_get_absolute_url(self):

        expected_url = reverse('news:article-detail', kwargs={'pk': self.article.pk})
        self.assertEqual(self.article.get_absolute_url(), expected_url)

    def test_is_news_hot_property(self):

        self.assertFalse(self.article.is_news_hot)

        self.article.news_views = 25
        self.article.save()
        self.article.refresh_from_db()
        self.assertTrue(self.article.is_news_hot)

        self.article.news_views = 20
        self.article.save()
        self.article.refresh_from_db()
        self.assertFalse(self.article.is_news_hot)

    def test_increment_views_method(self):

        initial_views = self.article.news_views
        self.article.increment_views()

        updated_article = Article.objects.get(pk=self.article.pk)
        
        self.assertEqual(updated_article.news_views, initial_views + 1)

        updated_article.increment_views()
        final_article = Article.objects.get(pk=self.article.pk)
        self.assertEqual(final_article.news_views, initial_views + 2)

    def test_default_values(self):

        self.assertEqual(self.default_article.category, 'sepakbola')
        self.assertEqual(self.default_article.news_views, 0)
        

        self.assertEqual(self.article.category, 'f1')
        self.assertEqual(self.article.news_views, 15) 

    def test_uuid_primary_key(self):

        self.assertIsInstance(self.article.pk, uuid.UUID)
        self.assertIsInstance(self.default_article.pk, uuid.UUID)