import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from profile_user.models import UserProfile
from ticketing.models import Event, Ticket, Booking
from ticketing.forms import TicketForm, BookingForm
from ticketing import views

# Jika pakai Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TicketBookingModelTest(TestCase):
    def setUp(self):
        # Buat user & profile
        self.user = User.objects.create_user(username='testuser', password='password')
        UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            phone='0000000000',
            role='user'
        )
        # Buat event
        self.event = Event.objects.create(
            name='Event Test',
            description='Desc',
            start_time='2025-10-25T10:00:00Z',
            end_time='2025-10-25T12:00:00Z'
        )
        # Buat ticket
        self.ticket = Ticket.objects.create(
            event=self.event,
            ticket_type='VIP',
            price=100,
            available=10
        )
        # Buat booking
        self.booking = Booking.objects.create(
            user=self.user,
            ticket=self.ticket,
            quantity=2
        )

    def test_booking_str_and_total_price(self):
        self.assertEqual(str(self.booking), f'{self.ticket.ticket_type} booking by {self.user.username}')
        self.assertEqual(self.booking.total_price(), 200)

    def test_ticket_str(self):
        self.assertEqual(str(self.ticket), f'{self.ticket.ticket_type} - {self.event.name}')


class TicketingFormsTest(TestCase):
    def setUp(self):
        # User & profile
        self.user = User.objects.create_user(username='formuser', password='password')
        UserProfile.objects.create(user=self.user, full_name='Form User', phone='000', role='user')
        # Event & ticket
        self.event = Event.objects.create(name='Event Form', description='Desc', start_time='2025-10-25T10:00:00Z', end_time='2025-10-25T12:00:00Z')
        self.ticket = Ticket.objects.create(event=self.event, ticket_type='Regular', price=50, available=5)

    def test_booking_form_valid(self):
        form = BookingForm(data={'quantity': 2})
        self.assertTrue(form.is_valid())

    def test_ticket_form_filter_user_events(self):
        form = TicketForm(user=self.user)
        self.assertIn(self.event, form.fields['event'].queryset)


class TicketingURLsTest(TestCase):
    def test_urls_resolve_to_correct_views(self):
        match = resolve('/ticketing/my-bookings/')
        self.assertEqual(match.func, views.my_bookings)


class TicketingViewsTest(TestCase):
    def setUp(self):
        # User & profile
        self.user = User.objects.create_user(username='viewuser', password='password')
        UserProfile.objects.create(user=self.user, full_name='View User', phone='000', role='user')
        # Event & ticket
        self.event = Event.objects.create(name='Event View', description='Desc', start_time='2025-10-25T10:00:00Z', end_time='2025-10-25T12:00:00Z')
        self.ticket = Ticket.objects.create(event=self.event, ticket_type='VIP', price=100, available=10)
        # Client login
        self.client = Client()
        self.client.login(username='viewuser', password='password')

    def test_book_ticket_get_redirect(self):
        url = reverse('ticketing:book_ticket', args=[str(self.ticket.id)])
        response = self.client.get(url)
        # Pastikan redirect ke detail event
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('event:event_detail', kwargs={'id': self.event.id}), response.url)

    def test_create_ticket_ajax(self):
        # Login sebagai admin
        admin = User.objects.create_user(username='adminuser', password='password')
        UserProfile.objects.create(user=admin, full_name='Admin', phone='000', role='admin')
        self.client.login(username='adminuser', password='password')

        url = reverse('ticketing:create_ticket')
        payload = {
            'event': str(self.event.id),
            'ticket_type': 'VIP',
            'price': 100,
            'available': 5
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)


class TicketingSeleniumTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = webdriver.Chrome()  # pastikan chromedriver ada di PATH

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def test_login_and_view_my_bookings(self):
        self.driver.get('http://127.0.0.1:8000/accounts/login/')
        username_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.send_keys('seleniumuser')
        self.driver.find_element(By.NAME, "password").send_keys('password')
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/ticketing/my-bookings/')
        )
        self.assertIn('/ticketing/my-bookings/', self.driver.current_url)
