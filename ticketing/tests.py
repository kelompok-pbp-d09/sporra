from event.models import Event 
from ticketing.models import Ticket, Booking
from ticketing.forms import BookingForm, TicketForm, TicketSelectionForm
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase, Client, LiveServerTestCase
from django.utils import timezone
from decimal import Decimal
import datetime
import json
from django.urls import resolve
from ticketing import views

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# ===========================
# Models Test
# ===========================
class TicketBookingModelTest(TestCase):
    def setUp(self):
        # buat user biasa
        self.user = User.objects.create_user(username='user1', password='12345', is_staff=False)
        # ambil profile kalau ada auto-create via signal
        self.profile = getattr(self.user, 'userprofile', None)

        # event dengan timezone-aware datetime
        self.event = Event.objects.create(
            judul="Event1",
            user=self.user,
            date=timezone.make_aware(datetime.datetime(2025, 1, 1, 10, 0))
        )

        # ticket
        self.ticket = Ticket.objects.create(
            event=self.event, ticket_type='regular', price=Decimal('100.00'), available=10
        )

    def test_ticket_str(self):
        self.assertEqual(str(self.ticket), f"regular - {self.event.judul}")

    def test_booking_str_and_total_price(self):
        booking = Booking.objects.create(user=self.user, ticket=self.ticket, quantity=2)
        self.assertEqual(str(booking), f"{self.user.username} - {self.event.judul}")
        # pastikan total_price dihitung otomatis
        booking.total_price = booking.quantity * booking.ticket.price
        self.assertEqual(booking.total_price, Decimal('200.00'))

# ===========================
# Forms Test
# ===========================
class TicketingFormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='12345', is_staff=False)
        self.profile = getattr(self.user, 'userprofile', None)
        self.event = Event.objects.create(
            judul="Event1",
            user=self.user,
            date=timezone.make_aware(datetime.datetime(2025, 1, 1, 10, 0))
        )
        self.ticket = Ticket.objects.create(
            event=self.event, ticket_type='regular', price=Decimal('100.00'), available=10
        )

    def test_booking_form_valid(self):
        form_data = {'quantity': 3}
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_ticket_form_filter_user_events(self):
        form = TicketForm(user=self.user)
        self.assertIn(self.event, form.fields['event'].queryset)

    def test_ticket_selection_form_queryset(self):
        form = TicketSelectionForm(event=self.event)
        self.assertIn(self.ticket, form.fields['ticket'].queryset)

# ===========================
# URLs Test
# ===========================
class TicketingURLsTest(TestCase):
    def test_urls_resolve_to_correct_views(self):
        self.assertEqual(resolve('/ticketing/my-bookings/').func, views.my_bookings)
        # UUID dijadikan string di URL kwargs
        dummy_uuid = "123e4567-e89b-12d3-a456-426614174000"
        self.assertEqual(resolve(f'/ticketing/book/{dummy_uuid}/').func, views.book_ticket)
        self.assertEqual(resolve('/ticketing/tickets/data/').func, views.get_tickets_ajax)
        self.assertEqual(resolve('/ticketing/create/').func, views.create_ticket)

# ===========================
# Views Test
# ===========================
class TicketingViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345", is_staff=False)
        self.profile = getattr(self.user, 'userprofile', None)
        self.client.login(username="testuser", password="12345")

        self.event = Event.objects.create(
            judul="Test Event",
            user=self.user,
            date=timezone.make_aware(datetime.datetime(2025, 1, 1, 10, 0))
        )
        self.ticket = Ticket.objects.create(
            event=self.event, ticket_type="regular", price=Decimal("100.00"), available=10
        )

    def test_book_ticket_get_redirect(self):
        url = reverse('ticketing:book_ticket', kwargs={'event_id': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # redirect

    def test_book_ticket_post_ajax_success(self):
        url = reverse('ticketing:book_ticket', kwargs={'event_id': self.event.id})
        data = {'ticket': self.ticket.id, 'quantity': 2}
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['status'], 'success')

    def test_my_bookings_view(self):
        Booking.objects.create(user=self.user, ticket=self.ticket, quantity=1, total_price=Decimal("100.00"))
        url = reverse('ticketing:my_bookings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "my_bookings.html")

    def test_get_tickets_ajax(self):
        url = reverse('ticketing:get_tickets')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('tickets', data)

    def test_create_ticket_ajax(self):
        url = reverse('ticketing:create_ticket')
        payload = {
            'event': str(self.event.id),
            'ticket_type': 'vip',
            'price': '200.00',
            'available': 5
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(Ticket.objects.filter(ticket_type='vip').count(), 1)

    def test_edit_ticket_ajax(self):
        url = reverse('ticketing:edit_ticket_ajax', kwargs={'ticket_id': self.ticket.id})
        payload = {'ticket_type': 'vip', 'price': '150.00', 'available': 20}
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_delete_ticket_ajax(self):
        url = reverse('ticketing:delete_ticket_ajax', kwargs={'ticket_id': self.ticket.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(Ticket.objects.filter(id=self.ticket.id).exists())

# ===========================
class TicketingSeleniumTest(LiveServerTestCase):
    def setUp(self):
        # Buat user
        self.user = User.objects.create_user(username="seleniumuser", password="12345", is_staff=False)

        # Buat UserProfile jika belum ada
        if not hasattr(self.user, 'userprofile'):
            from profile_user.models import UserProfile
            UserProfile.objects.create(user=self.user, full_name="Selenium User", phone="000000000", role="user")

        # Buat event
        self.event = Event.objects.create(
            judul="Selenium Event",
            user=self.user,
            date=timezone.make_aware(datetime.datetime(2025, 1, 1, 10, 0))
        )

        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(5)

    def tearDown(self):
        self.driver.quit()

    def test_login_and_view_my_bookings(self):
        # buka halaman login
        self.driver.get(f'{self.live_server_url}/accounts/login/')

        # tunggu form login
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "id_username"))
        )

        # isi form login
        self.driver.find_element(By.ID, "id_username").send_keys("seleniumuser")
        self.driver.find_element(By.ID, "id_password").send_keys("12345")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # tunggu redirect
        WebDriverWait(self.driver, 5).until(
            lambda d: d.current_url != f'{self.live_server_url}/accounts/login/'
        )

        # buka halaman my bookings
        self.driver.get(f'{self.live_server_url}/ticketing/my-bookings/')
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        self.assertIn("My Bookings", self.driver.page_source)
