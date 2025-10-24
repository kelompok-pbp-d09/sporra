from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile, Status
from .forms import CustomUserCreationForm, EditProfileForm
from django.utils import timezone
import json


class UserProfileModelTest(TestCase):
    """Test cases untuk UserProfile model"""
    
    def setUp(self):
        """Setup data untuk testing"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            bio='Test bio',
            phone='081234567890',
            role='user'
        )
        
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='adminpass123'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            full_name='Admin User',
            phone='081234567891',
            role='admin'
        )
    
    def test_user_profile_creation(self):
        """Test pembuatan UserProfile"""
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(self.profile.full_name, 'Test User')
        self.assertEqual(self.profile.role, 'user')
    
    def test_user_profile_str(self):
        """Test __str__ method"""
        expected = f"{self.user.username} ({self.profile.role})"
        self.assertEqual(str(self.profile), expected)
    
    def test_is_admin_property(self):
        """Test is_admin property"""
        self.assertFalse(self.profile.is_admin)
        self.assertTrue(self.admin_profile.is_admin)
    
    def test_add_status(self):
        """Test menambah status"""
        status = self.profile.add_status('Test status content')
        self.assertIsInstance(status, Status)
        self.assertEqual(status.content, 'Test status content')
        self.assertEqual(status.user, self.profile)
    
    def test_get_statuses(self):
        """Test mendapatkan semua status"""
        self.profile.add_status('Status 1')
        self.profile.add_status('Status 2')
        statuses = self.profile.get_statuses()
        self.assertEqual(statuses.count(), 2)
    
    def test_profile_picture_default(self):
        """Test profile picture default (null)"""
        self.assertIsNone(self.profile.profile_picture)
    
    def test_profile_picture_url(self):
        """Test profile picture dengan URL"""
        self.profile.profile_picture = 'https://example.com/image.jpg'
        self.profile.save()
        self.assertEqual(self.profile.profile_picture, 'https://example.com/image.jpg')


class StatusModelTest(TestCase):
    """Test cases untuk Status model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='081234567890'
        )
    
    def test_status_creation(self):
        """Test pembuatan status"""
        status = Status.objects.create(
            user=self.profile,
            content='Test status'
        )
        self.assertEqual(status.content, 'Test status')
        self.assertEqual(status.user, self.profile)
        self.assertIsNotNone(status.created_at)
    
    def test_status_auto_timestamp(self):
        """Test created_at otomatis terisi"""
        status = Status.objects.create(
            user=self.profile,
            content='Test'
        )
        self.assertIsNotNone(status.created_at)
        self.assertLessEqual(status.created_at, timezone.now())


class CustomUserCreationFormTest(TestCase):
    """Test cases untuk CustomUserCreationForm"""
    
    def test_valid_form(self):
        """Test form dengan data valid"""
        form_data = {
            'username': 'newuser',
            'full_name': 'New User',
            'phone': '081234567890',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_missing_fields(self):
        """Test form dengan field yang kurang"""
        form_data = {
            'username': 'newuser',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)
        self.assertIn('phone', form.errors)
    
    def test_password_mismatch(self):
        """Test form dengan password tidak cocok"""
        form_data = {
            'username': 'newuser',
            'full_name': 'New User',
            'phone': '081234567890',
            'password1': 'complexpass123',
            'password2': 'differentpass123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())


class EditProfileFormTest(TestCase):
    """Test cases untuk EditProfileForm"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='081234567890'
        )
    
    def test_valid_edit_form(self):
        """Test edit profile dengan data valid"""
        form_data = {
            'full_name': 'Updated Name',
            'bio': 'Updated bio',
            'phone': '089876543210',
            'profile_picture': 'https://example.com/new.jpg'
        }
        form = EditProfileForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())
    
    def test_edit_form_partial_data(self):
        """Test edit dengan data parsial (bio kosong)"""
        form_data = {
            'full_name': 'Updated Name',
            'phone': '089876543210'
        }
        form = EditProfileForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())


class RegisterViewTest(TestCase):
    """Test cases untuk register view"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('profile_user:register')
    
    def test_register_page_accessible(self):
        """Test halaman register dapat diakses"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')


class LoginViewTest(TestCase):
    """Test cases untuk login view"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('profile_user:login')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='081234567890'
        )
    
    def test_login_page_accessible(self):
        """Test halaman login dapat diakses"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
    
    def test_login_success(self):
        """Test login berhasil"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_invalid_credentials(self):
        """Test login dengan kredensial salah"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class LogoutViewTest(TestCase):
    """Test cases untuk logout view"""
    
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('profile_user:logout')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_logout_success(self):
        """Test logout berhasil"""
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Redirect


class ShowProfileViewTest(TestCase):
    """Test cases untuk show profile view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='081234567890'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_show_own_profile(self):
        """Test melihat profile sendiri"""
        response = self.client.get(reverse('profile_user:show_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_profile.html')
        self.assertTrue(response.context['is_own_profile'])
    
    def test_show_other_user_profile(self):
        """Test melihat profile user lain"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=other_user,
            full_name='Other User',
            phone='089876543210'
        )
        
        response = self.client.get(
            reverse('profile_user:show_profile', kwargs={'username': 'otheruser'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_own_profile'])
    
    def test_show_profile_requires_login(self):
        """Test akses profile memerlukan login"""
        self.client.logout()
        response = self.client.get(reverse('profile_user:show_profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class EditProfileViewTest(TestCase):
    """Test cases untuk edit profile view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='081234567890'
        )
        self.edit_url = reverse('profile_user:edit_profile')
        self.client.login(username='testuser', password='testpass123')
    
    def test_edit_profile_page_accessible(self):
        """Test halaman edit profile dapat diakses"""
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_profile.html')
    
    def test_edit_profile_success(self):
        """Test edit profile berhasil"""
        data = {
            'full_name': 'Updated Name',
            'bio': 'Updated bio',
            'phone': '089876543210',
            'profile_picture': 'https://example.com/new.jpg'
        }
        response = self.client.post(self.edit_url, data)
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, 'Updated Name')
        self.assertEqual(self.profile.bio, 'Updated bio')
        self.assertEqual(self.profile.phone, '089876543210')
    
    def test_edit_profile_requires_login(self):
        """Test edit profile memerlukan login"""
        self.client.logout()
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 302)


class AddStatusViewTest(TestCase):
    """Test cases untuk add status view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='081234567890'
        )
        self.add_status_url = reverse('profile_user:add_status')
        self.client.login(username='testuser', password='testpass123')
    
    def test_add_status_success(self):
        """Test menambah status berhasil"""
        data = {'content': 'Test status content'}
        response = self.client.post(self.add_status_url, data)
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertIn('id', json_data)
        self.assertEqual(json_data['content'], 'Test status content')
        self.assertEqual(Status.objects.count(), 1)
    
    def test_add_empty_status(self):
        """Test menambah status kosong"""
        data = {'content': '   '}
        response = self.client.post(self.add_status_url, data)
        
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.content)
        self.assertIn('error', json_data)
    
    def test_add_status_requires_login(self):
        """Test add status memerlukan login"""
        self.client.logout()
        data = {'content': 'Test status'}
        response = self.client.post(self.add_status_url, data)
        self.assertEqual(response.status_code, 302)


class DeleteStatusViewTest(TestCase):
    """Test cases untuk delete status view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='081234567890'
        )
        self.status = Status.objects.create(
            user=self.profile,
            content='Test status'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_delete_own_status(self):
        """Test hapus status sendiri"""
        url = reverse('profile_user:delete_status', kwargs={'status_id': self.status.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertTrue(json_data['success'])
        self.assertEqual(Status.objects.count(), 0)
    
    def test_admin_delete_any_status(self):
        """Test admin dapat hapus status siapa saja"""
        # Buat user lain
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_profile = UserProfile.objects.create(
            user=other_user,
            full_name='Other User',
            phone='089876543210'
        )
        other_status = Status.objects.create(
            user=other_profile,
            content='Other status'
        )
        
        # Login sebagai admin
        admin_user = User.objects.create_user(
            username='adminuser',
            password='testpass123'
        )
        admin_profile = UserProfile.objects.create(
            user=admin_user,
            full_name='Admin',
            phone='081111111111',
            role='admin'
        )
        self.client.login(username='adminuser', password='testpass123')
        
        url = reverse('profile_user:delete_status', kwargs={'status_id': other_status.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Status.objects.filter(id=other_status.id).exists())
    
    def test_delete_status_without_permission(self):
        """Test hapus status tanpa izin"""
        # Buat user lain
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=other_user,
            full_name='Other User',
            phone='089876543210'
        )
        
        # Login sebagai user lain
        self.client.login(username='otheruser', password='testpass123')
        
        url = reverse('profile_user:delete_status', kwargs={'status_id': self.status.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)


class EditStatusViewTest(TestCase):
    """Test cases untuk edit status view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='081234567890'
        )
        self.status = Status.objects.create(
            user=self.profile,
            content='Original content'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_edit_own_status(self):
        """Test edit status sendiri"""
        url = reverse('profile_user:edit_status', kwargs={'status_id': self.status.id})
        data = {'content': 'Updated content'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['new_content'], 'Updated content')
        
        self.status.refresh_from_db()
        self.assertEqual(self.status.content, 'Updated content')
    
    def test_edit_status_empty_content(self):
        """Test edit status dengan konten kosong"""
        url = reverse('profile_user:edit_status', kwargs={'status_id': self.status.id})
        data = {'content': '   '}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.content)
        self.assertIn('error', json_data)
    
    def test_admin_edit_any_status(self):
        """Test admin dapat edit status siapa saja"""
        admin_user = User.objects.create_user(
            username='adminuser',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=admin_user,
            full_name='Admin',
            phone='081111111111',
            role='admin'
        )
        self.client.login(username='adminuser', password='testpass123')
        
        url = reverse('profile_user:edit_status', kwargs={'status_id': self.status.id})
        data = {'content': 'Admin updated this'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        self.status.refresh_from_db()
        self.assertEqual(self.status.content, 'Admin updated this')
    
    def test_edit_status_without_permission(self):
        """Test edit status tanpa izin"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=other_user,
            full_name='Other User',
            phone='089876543210'
        )
        self.client.login(username='otheruser', password='testpass123')
        
        url = reverse('profile_user:edit_status', kwargs={'status_id': self.status.id})
        data = {'content': 'Trying to edit'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 403)


class UserProfilePropertyTest(TestCase):
    """Test cases untuk property di UserProfile"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='081234567890'
        )
    
    def test_komentar_created_property(self):
        """Test property komentar_created"""
        # Asumsikan ada model Post dari forumdiskusi
        # Jika tidak ada, test ini akan di-skip atau disesuaikan
        count = self.profile.komentar_created
        self.assertEqual(count, 0)
    
    def test_news_created_property(self):
        """Test property news_created"""
        # Asumsikan ada model Article dari news
        # Jika tidak ada, test ini akan di-skip atau disesuaikan
        count = self.profile.news_created
        self.assertEqual(count, 0)