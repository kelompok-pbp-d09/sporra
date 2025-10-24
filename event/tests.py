from django.test import TestCase
from django.test import TestCase, Client
from event.forms import EventForm
from .models import Event
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from django.contrib.auth.models import User

# Create your tests here.
# Models
class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.event = Event.objects.create(
            judul='Test Event',
            deskripsi='This is a test event.',
            date='2024-12-31 10:00:00',
            lokasi='Test Location',
            kategori='basket',
            user=self.user
        )
# Forms
class EventFormTest(TestCase):
    def test_event_form_valid_data(self):
        form_data = {
            'judul': 'Sample Event',
            'deskripsi': 'This is a sample event description.',
            'date': '2024-12-31 10:00:00',
            'lokasi': 'Sample Location',
            'kategori': 'tennis',
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_event_form_invalid_data(self):
        form_data = {
            'judul': '',
            'deskripsi': 'This is a sample event description.',
            'date': '',
            'lokasi': 'Sample Location',
            'kategori': 'tennis',
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())

#urls
class EventURLsTest(TestCase):
    def test_home_event_url(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_event_detail_url(self):
        event = Event.objects.create(
            judul='Test Event',
            deskripsi='This is a test event.',
            date='2024-12-31 10:00:00',
            lokasi='Test Location',
            kategori='basket'
        )
        response = self.client.get(f'/event/{event.id}/')
        self.assertEqual(response.status_code, 200)
        
    def test_create_event_url(self):
        response = self.client.get('/create-event/')
        self.assertEqual(response.status_code, 200)
        
    def test_edit_event_url(self):
        event = Event.objects.create(
            judul='Test Event',
            deskripsi='This is a test event.',
            date='2024-12-31 10:00:00',
            lokasi='Test Location',
            kategori='basket'
        )
        response = self.client.get(f'/event/{event.id}/edit/')
        self.assertEqual(response.status_code, 200)
        
    def test_delete_event_url(self):
        event = Event.objects.create(
            judul='Test Event',
            deskripsi='This is a test event.',
            date='2024-12-31 10:00:00',
            lokasi='Test Location',
            kategori='basket'
        )
        response = self.client.get(f'/event/{event.id}/delete/')
        self.assertEqual(response.status_code, 200)
        
    def test_get_event_ajax_url(self):  
        event = Event.objects.create(
            judul='Test Event',
            deskripsi='This is a test event.',
            date='2024-12-31 10:00:00',
            lokasi='Test Location',
            kategori='basket'
        )
        response = self.client.get(f'/ajax/get-event/{event.id}/')
        self.assertEqual(response.status_code, 200)
    
    def test_get_events_ajax_url(self):
        response = self.client.get('/ajax/get-events/')
        self.assertEqual(response.status_code, 200)

#views

#templates
#create_event_modal.html

#edit_event_modal.html

#event_detail.html

#home_event.html