from datetime import datetime, timedelta, timezone as dt_timezone
import json, uuid
from django.test import TestCase, Client
from django.urls import reverse
from event.forms import EventForm
from .models import Event
from django.contrib.auth.models import User
from django.utils import timezone

class TicketBookingModelTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_event_create(self):
        event = Event.objects.create(
            judul="Test Event",
            deskripsi="Test description",
            date=datetime(2025, 12, 31, 10, 0, tzinfo=dt_timezone.utc),
            lokasi="Test Location",
            kategori="basket",
            user=self.test_user,
            event_views=100
        )  
        self.assertEqual(event.judul, "Test Event")
        self.assertEqual(event.deskripsi, "Test description")
        self.assertEqual(event.lokasi, "Test Location")
        self.assertEqual(event.kategori, "basket")
        self.assertEqual(event.event_views, 100)
        self.assertEqual(event.user, self.test_user)
    
    def test_event_default(self):
        event = Event.objects.create(
            judul="Default Test",
            deskripsi="Test",
            date=timezone.now(),
            lokasi="Location"
        )
        self.assertEqual(event.event_views, 0)
        self.assertEqual(event.kategori, 'basket')
        self.assertIsNone(event.user)
    
    def test_event_id_is_uuid(self):
        event = Event.objects.create(
            judul="UUID Test",
            deskripsi="Test",
            date=timezone.now(),
            lokasi="Location"
        )
        self.assertIsInstance(event.id, uuid.UUID)
        self.assertIsNotNone(event.id)
    
    def test_event_str(self):
        event = Event.objects.create(
            judul="String Test Event",
            deskripsi="Test",
            date=timezone.now(),
            lokasi="Location"
        )
        self.assertEqual(str(event), "String Test Event")
    
    def test_increment_views(self):
        event = Event.objects.create(
            judul="Views Test",
            deskripsi="Test",
            date=timezone.now(),
            lokasi="Location",
            event_views=0
        )
        initial_views = event.event_views
        event.increment_views()
        self.assertEqual(event.event_views, initial_views + 1)
        event.refresh_from_db()
        self.assertEqual(event.event_views, 1)
    
    def test_increment_more_views(self):
        event = Event.objects.create(
            judul="Multiple Views Test",
            deskripsi="Test",
            date=timezone.now(),
            lokasi="Location"
        )
        for i in range(5):
            event.increment_views()
        
        self.assertEqual(event.event_views, 5)
    
    def test_all_category(self):
        categories = ['basket', 'tennis', 'bulu tangkis', 'volley', 
                     'futsal', 'sepak bola', 'renang', 'lainnya']
        
        for category in categories:
            event = Event.objects.create(
                judul=f"Test {category}",
                deskripsi="Test",
                date=timezone.now(),
                lokasi="Location",
                kategori=category
            )
            self.assertEqual(event.kategori, category)
    
    def test_user_foreign_key_null(self):
        user = User.objects.create_user(
            username='deleteme',
            password='pass123'
        )
        event = Event.objects.create(
            judul="User Delete Test",
            deskripsi="Test",
            date=timezone.now(),
            lokasi="Location",
            user=user
        )
        user_id = user.id
        user.delete()
        event.refresh_from_db()
        self.assertIsNone(event.user)
    
    def test_event_no_user(self):
        event = Event.objects.create(
            judul="No User Event",
            deskripsi="Test",
            date=timezone.now(),
            lokasi="Location"
        )
        self.assertIsNone(event.user)
    
    def test_judul_max_length(self):
        max_length = Event._meta.get_field('judul').max_length
        self.assertEqual(max_length, 255)
    
    def test_lokasi_max_length(self):
        max_length = Event._meta.get_field('lokasi').max_length
        self.assertEqual(max_length, 300)
    
    def test_kategori_max_length(self):
        max_length = Event._meta.get_field('kategori').max_length
        self.assertEqual(max_length, 20)
    
    def test_event_views_positive(self):
        field = Event._meta.get_field('event_views')
        self.assertEqual(field.__class__.__name__, 'PositiveIntegerField')
    
    def test_deskripsi_textfield(self):
        long_text = "This is a very long description. " * 100
        event = Event.objects.create(
            judul="Long Description Test",
            deskripsi=long_text,
            date=timezone.now(),
            lokasi="Location"
        )
        self.assertEqual(event.deskripsi, long_text)
    
    def test_date_field_type(self):
        field = Event._meta.get_field('date')
        self.assertEqual(field.__class__.__name__, 'DateTimeField')
    
    def test_multiple_events_different_uuids(self):
        event1 = Event.objects.create(
            judul="Event 1",
            deskripsi="Test",
            date=timezone.now(),
            lokasi="Location"
        )
        event2 = Event.objects.create(
            judul="Event 2",
            deskripsi="Test",
            date=timezone.now(),
            lokasi="Location"
        )
        self.assertNotEqual(event1.id, event2.id)

# Forms
class EventFormTest(TestCase):
    def test_form_correct_fields(self):
        form = EventForm()
        self.assertIn('judul', form.fields)
        self.assertIn('deskripsi', form.fields)
        self.assertIn('date', form.fields)
        self.assertIn('lokasi', form.fields)
        self.assertIn('kategori', form.fields)
    
    def test_date_field_charfield(self):
        form = EventForm()
        self.assertEqual(form.fields['date'].label, 'Tanggal dan Waktu')
        self.assertIn('placeholder', form.fields['date'].widget.attrs)
    
    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'judul': 'Test Event',
            'deskripsi': 'Test Description',
            'date': '12 Juli 2025 15.00',
            'lokasi': 'Test Location',
            'kategori': 'basket'
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_clean_date(self):
        indonesian_months = [
            ('12 Januari 2025 15.00', 1),
            ('15 Februari 2025 10.30', 2),
            ('20 Maret 2025 14.00', 3),
            ('5 April 2025 09.00', 4),
            ('10 Mei 2025 16.00', 5),
            ('25 Juni 2025 11.00', 6),
            ('30 Juli 2025 13.00', 7),
            ('8 Agustus 2025 17.00', 8),
            ('12 September 2025 12.00', 9),
            ('18 Oktober 2025 15.30', 10),
            ('22 November 2025 10.00', 11),
            ('31 Desember 2025 23.59', 12)
        ]
        
        for date_str, expected_month in indonesian_months:
            form_data = {
                'judul': 'Test',
                'deskripsi': 'Test',
                'date': date_str,
                'lokasi': 'Test',
                'kategori': 'basket'
            }
            form = EventForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Failed for date: {date_str}")
            self.assertEqual(form.cleaned_data['date'].month, expected_month)
    
    def test_clean_date_separator(self):
        form_data = {
            'judul': 'Test',
            'deskripsi': 'Test',
            'date': '12 Juli 2025 15:30',
            'lokasi': 'Test',
            'kategori': 'basket'
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['date'].hour, 15)
        self.assertEqual(form.cleaned_data['date'].minute, 30)
    
    def test_clean_date_dot_separator(self):
        form_data = {
            'judul': 'Test',
            'deskripsi': 'Test',
            'date': '12 Juli 2025 15.30',
            'lokasi': 'Test',
            'kategori': 'basket'
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['date'].hour, 15)
        self.assertEqual(form.cleaned_data['date'].minute, 30)
    
    def test_clean_date_invalid(self):
        invalid_dates = [
            '2025-07-12',
            '12/07/2025',
            'invalid date',
            '32 Juli 2025 15.00',
            '12 InvalidMonth 2025 15.00',
        ]
        
        for invalid_date in invalid_dates:
            form_data = {
                'judul': 'Test',
                'deskripsi': 'Test',
                'date': invalid_date,
                'lokasi': 'Test',
                'kategori': 'basket'
            }
            form = EventForm(data=form_data)
            self.assertFalse(form.is_valid())
            self.assertIn('date', form.errors)
    
    def test_clean_date_empty(self):
        form_data = {
            'judul': 'Test',
            'deskripsi': 'Test',
            'date': '',
            'lokasi': 'Test',
            'kategori': 'basket'
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)
    
    def test_clean_date_timezone_aware(self):
        form_data = {
            'judul': 'Test',
            'deskripsi': 'Test',
            'date': '12 Juli 2025 15.00',
            'lokasi': 'Test',
            'kategori': 'basket'
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        parsed_date = form.cleaned_data['date']
        self.assertTrue(timezone.is_aware(parsed_date))
    
    def test_clean_judul_strips_tags(self):
        form_data = {
            'judul': '<script>alert("XSS")</script>Test Event',
            'deskripsi': 'Test',
            'date': '12 Juli 2025 15.00',
            'lokasi': 'Test',
            'kategori': 'basket'
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['judul'], 'Test Event')
        self.assertNotIn('<script>', form.cleaned_data['judul'])
    
    def test_clean_judul_strips_more_tags(self):
        test_cases = [
            ('<b>Bold</b> Title', 'Bold Title'),
            ('<p>Paragraph</p> Title', 'Paragraph Title'),
            ('<a href="#">Link</a> Title', 'Link Title'),
            ('<div>Div</div> Title', 'Div Title'),
        ]
        
        for input_judul, expected_output in test_cases:
            form_data = {
                'judul': input_judul,
                'deskripsi': 'Test',
                'date': '12 Juli 2025 15.00',
                'lokasi': 'Test',
                'kategori': 'basket'
            }
            form = EventForm(data=form_data)
            self.assertTrue(form.is_valid())
            self.assertEqual(form.cleaned_data['judul'], expected_output)
    
    def test_clean_deskripsi_strips_tags(self):
        form_data = {
            'judul': 'Test',
            'deskripsi': '<b>Bold</b> description with <i>italic</i> text',
            'date': '12 Juli 2025 15.00',
            'lokasi': 'Test',
            'kategori': 'basket'
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['deskripsi'], 'Bold description with italic text')
        self.assertNotIn('<b>', form.cleaned_data['deskripsi'])
        self.assertNotIn('<i>', form.cleaned_data['deskripsi'])
        
    def test_form_missing_required(self):
        required_fields = ['judul', 'deskripsi', 'date', 'lokasi', 'kategori']
        
        for field in required_fields:
            form_data = {
                'judul': 'Test',
                'deskripsi': 'Test',
                'date': '12 Juli 2025 15.00',
                'lokasi': 'Test',
                'kategori': 'basket'
            }
            del form_data[field]
            
            form = EventForm(data=form_data)
            self.assertFalse(form.is_valid())
            self.assertIn(field, form.errors)
    
    def test_kategori_valid_choices(self):
        valid_categories = ['basket', 'tennis', 'bulu tangkis', 'volley', 'futsal', 'sepak bola', 'renang', 'lainnya']
        
        for kategori in valid_categories:
            form_data = {
                'judul': 'Test',
                'deskripsi': 'Test',
                'date': '12 Juli 2025 15.00',
                'lokasi': 'Test',
                'kategori': kategori
            }
            form = EventForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Failed for kategori: {kategori}")
    
    def test_kategori_invalid_choice(self):
        form_data = {
            'judul': 'Test',
            'deskripsi': 'Test',
            'date': '12 Juli 2025 15.00',
            'lokasi': 'Test',
            'kategori': 'invalid_category'
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('kategori', form.errors)
    
    def test_form_save(self):
        form_data = {
            'judul': 'Saved Event',
            'deskripsi': 'This event should be saved',
            'date': '12 Juli 2025 15.00',
            'lokasi': 'Saved Location',
            'kategori': 'basket'
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        event = form.save()
        self.assertIsNotNone(event.id)
        self.assertEqual(event.judul, 'Saved Event')
        self.assertEqual(event.lokasi, 'Saved Location')
        self.assertEqual(event.kategori, 'basket')
    
    def test_date_case_insensitive(self):
        test_cases = ['12 JULI 2025 15.00', '12 juli 2025 15.00', '12 JuLi 2025 15.00']
        
        for date_str in test_cases:
            form_data = {
                'judul': 'Test',
                'deskripsi': 'Test',
                'date': date_str,
                'lokasi': 'Test',
                'kategori': 'basket'
            }
            form = EventForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Failed for: {date_str}")
            self.assertEqual(form.cleaned_data['date'].month, 7)
    
    def test_form_field_order(self):
        form = EventForm()
        field_order = list(form.fields.keys())
        expected_order = ["judul", "deskripsi", "date", "lokasi", "kategori"]
        self.assertEqual(field_order, expected_order)
        
#urls
class EventURLsTest(TestCase):
    def test_home_event_url(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_event_detail_url(self):
        event = Event.objects.create(
            judul='Test Event',
            deskripsi='This is a test event.',
            date=timezone.now() + timedelta(days=1),
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
            date=timezone.now() + timedelta(days=1),
            lokasi='Test Location',
            kategori='basket'
        )
        response = self.client.get(f'/event/{event.id}/edit/')
        self.assertEqual(response.status_code, 400)  # GET request returns 400
        
    def test_delete_event_url(self):
        event = Event.objects.create(
            judul='Test Event',
            deskripsi='This is a test event.',
            date=timezone.now() + timedelta(days=1),
            lokasi='Test Location',
            kategori='basket'
        )
        response = self.client.post(f'/event/{event.id}/delete/')
        self.assertEqual(response.status_code, 302)  # Redirect after delete
        
    def test_get_event_ajax_url(self):  
        event = Event.objects.create(
            judul='Test Event',
            deskripsi='This is a test event.',
            date=timezone.now() + timedelta(days=1),
            lokasi='Test Location',
            kategori='basket'
        )
        response = self.client.get(f'/ajax/get-event/{event.id}/')
        self.assertEqual(response.status_code, 200)
    
    def test_get_events_ajax_url(self):
        response = self.client.get('/ajax/get-events/')
        self.assertEqual(response.status_code, 200)

#views
class EventViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.future_event = Event.objects.create(
            judul='Future Event',
            deskripsi='Future event description',
            date=timezone.now() + timedelta(days=7),
            lokasi='Future Location',
            kategori='basket',
            user=self.user
        )
        
        self.past_event = Event.objects.create(
            judul='Past Event',
            deskripsi='Past event description',
            date=timezone.now() - timedelta(days=7),
            lokasi='Past Location',
            kategori='tennis',
            user=self.user
        )
    
    #Home
    def test_home_event_url_exists(self):
        response = self.client.get(reverse('event:home_event'))
        self.assertEqual(response.status_code, 200)
    
    def test_home_event_correct_template(self):
        response = self.client.get(reverse('event:home_event'))
        self.assertTemplateUsed(response, 'home_event.html')
    
    def test_home_event_context_data(self):
        response = self.client.get(reverse('event:home_event'))
        self.assertIn('categories', response.context)
        self.assertIn('upcoming_events', response.context)
        self.assertIn('past_events', response.context)
        self.assertIn('form', response.context)
        self.assertIn('current_category', response.context)
    
    def test_home_event_upcoming_and_past_separate(self):
        response = self.client.get(reverse('event:home_event'))
        upcoming = list(response.context['upcoming_events'])
        past = list(response.context['past_events'])
        self.assertIn(self.future_event, upcoming)
        self.assertIn(self.past_event, past)
    
    def test_home_event_filter_category(self):
        response = self.client.get(reverse('event:home_event'), {'category': 'basket'})
        events = list(response.context['upcoming_events']) + list(response.context['past_events'])
        self.assertIn(self.future_event, events)
        self.assertNotIn(self.past_event, events)
        self.assertEqual(response.context['current_category'], 'basket')
    
    def test_home_event_no_category_show(self):
        response = self.client.get(reverse('event:home_event'))
        all_events = list(response.context['upcoming_events']) + list(response.context['past_events'])
        self.assertEqual(len(all_events), 2)
    
    def test_home_event_upcoming_order_by_date(self):
        event1 = Event.objects.create(
            judul='Event 1',
            deskripsi='Test',
            date=timezone.now() + timedelta(days=1),
            lokasi='Location',
            kategori='basket'
        )
        event2 = Event.objects.create(
            judul='Event 2',
            deskripsi='Test',
            date=timezone.now() + timedelta(days=3),
            lokasi='Location',
            kategori='basket'
        )
        response = self.client.get(reverse('event:home_event'))
        upcoming = list(response.context['upcoming_events'])
        self.assertEqual(upcoming[0], event1)
        self.assertEqual(upcoming[1], event2)
    
    def test_home_event_past_order_by_date(self):
        event1 = Event.objects.create(
            judul='Past Event 1',
            deskripsi='Test',
            date=timezone.now() - timedelta(days=3),
            lokasi='Location',
            kategori='basket'
        )
        event2 = Event.objects.create(
            judul='Past Event 2',
            deskripsi='Test',
            date=timezone.now() - timedelta(days=1),
            lokasi='Location',
            kategori='basket'
        )
        response = self.client.get(reverse('event:home_event'))
        past = list(response.context['past_events'])
        self.assertEqual(past[0], event2)
        self.assertEqual(past[1], event1)
    
    #event detail
    def test_event_detail_url_exists(self):
        response = self.client.get(reverse('event:event_detail', args=[self.future_event.id]))
        self.assertEqual(response.status_code, 200)
    
    def test_event_detail_uses_correct_template(self):
        response = self.client.get(reverse('event:event_detail', args=[self.future_event.id]))
        self.assertTemplateUsed(response, 'event_detail.html')
    
    def test_event_detail_context_data(self):
        response = self.client.get(reverse('event:event_detail', args=[self.future_event.id]))
        self.assertIn('event', response.context)
        self.assertIn('has_ended', response.context)
        self.assertIn('tickets', response.context)
        self.assertEqual(response.context['event'], self.future_event)
    
    def test_event_detail_increments_views(self):
        initial_views = self.future_event.event_views
        self.client.get(reverse('event:event_detail', args=[self.future_event.id]))
        self.future_event.refresh_from_db()
        self.assertEqual(self.future_event.event_views, initial_views + 1)
    
    def test_event_detail_ended_past_event(self):
        response = self.client.get(reverse('event:event_detail', args=[self.past_event.id]))
        self.assertTrue(response.context['has_ended'])
    
    def test_event_detail_nonexist_event_404(self):
        fake_id = uuid.uuid4()
        response = self.client.get(reverse('event:event_detail', args=[fake_id]))
        self.assertEqual(response.status_code, 404)
    
    # create event
    def test_create_event_get_request(self):
        response = self.client.get(reverse('event:create_event'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_event.html')
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], EventForm)
    
    def test_create_event_user_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        form_data = {
            'judul': 'New Event',
            'deskripsi': 'New event description',
            'date': '15 Januari 2026 14.00',
            'lokasi': 'New Location',
            'kategori': 'basket'
        }
        response = self.client.post(reverse('event:create_event'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('event:home_event'))
        self.assertTrue(Event.objects.filter(judul='New Event').exists())
        new_event = Event.objects.get(judul='New Event')
        self.assertEqual(new_event.user, self.user)
    
    def test_create_event_user_unauthenticated(self):
        form_data = {
            'judul': 'Anonymous Event',
            'deskripsi': 'Anonymous event description',
            'date': '15 Januari 2026 14.00',
            'lokasi': 'Location',
            'kategori': 'basket'
        }
        response = self.client.post(reverse('event:create_event'), data=form_data)
        self.assertEqual(response.status_code, 302)
        event = Event.objects.get(judul='Anonymous Event')
        self.assertIsNone(event.user)
    
    def test_create_event_invalid(self):
        form_data = {
            'judul': 'Invalid Event',
            'deskripsi': 'Test',
            'date': 'invalid date',
            'lokasi': 'Location',
            'kategori': 'basket'
        }
        response = self.client.post(reverse('event:create_event'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_event.html')
        self.assertFalse(Event.objects.filter(judul='Invalid Event').exists())
    
    def test_create_event_ajax_request_valid(self):
        self.client.login(username='testuser', password='testpass123')
        form_data = {
            'judul': 'AJAX Event',
            'deskripsi': 'AJAX event description',
            'date': '15 Januari 2026 14.00',
            'lokasi': 'AJAX Location',
            'kategori': 'basket'
        }
        response = self.client.post(
            reverse('event:create_event'),
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['redirect_url'], reverse('event:home_event'))
        self.assertIn('message', data)
        self.assertTrue(Event.objects.filter(judul='AJAX Event').exists())
    
    def test_create_event_ajax_request_invalid(self):
        form_data = {
            'judul': 'Invalid AJAX Event',
            'deskripsi': 'Test',
            'date': 'invalid date',
            'lokasi': 'Location',
            'kategori': 'basket'
        }
        response = self.client.post(
            reverse('event:create_event'),
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('errors', data)
        self.assertIn('date', data['errors'])
    
    # edit event
    
    def test_edit_event_valid(self):
        form_data = {
            'judul': 'Updated Event',
            'deskripsi': 'Updated description',
            'date': '20 Februari 2026 16.00',
            'lokasi': 'Updated Location',
            'kategori': 'tennis'
        }
        response = self.client.post(
            reverse('event:edit_event', args=[self.future_event.id]),
            data=form_data
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.future_event.refresh_from_db()
        self.assertEqual(self.future_event.judul, 'Updated Event')
        self.assertEqual(self.future_event.kategori, 'tennis')
    
    def test_edit_event_invalid(self):
        form_data = {
            'judul': 'Updated Event',
            'deskripsi': 'Test',
            'date': 'invalid date',
            'lokasi': 'Location',
            'kategori': 'basket'
        }
        response = self.client.post(
            reverse('event:edit_event', args=[self.future_event.id]),
            data=form_data
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('errors', data)
    
    def test_edit_event_get_request_invalid(self):
        response = self.client.get(reverse('event:edit_event', args=[self.future_event.id]))
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_edit_event_nonexist_event_404(self):
        fake_id = uuid.uuid4()
        form_data = {
            'judul': 'Test',
            'deskripsi': 'Test',
            'date': '15 Januari 2026 14.00',
            'lokasi': 'Location',
            'kategori': 'basket'
        }
        response = self.client.post(
            reverse('event:edit_event', args=[fake_id]),
            data=form_data
        )
        self.assertEqual(response.status_code, 404)
    
    # delete event
    
    def test_delete_event_success(self):
        event_id = self.future_event.id
        response = self.client.post(reverse('event:delete_event', args=[event_id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('event:home_event'))
        self.assertFalse(Event.objects.filter(id=event_id).exists())
    
    def test_delete_event_nonexist_404(self):
        fake_id = uuid.uuid4()
        response = self.client.post(reverse('event:delete_event', args=[fake_id]))
        self.assertEqual(response.status_code, 404)
    
    # get_event_ajax
    
    def test_get_event_ajax_success(self):
        response = self.client.get(reverse('event:get_event_ajax', args=[self.future_event.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('form_html', data)
        self.assertIn(self.future_event.judul, data['form_html'])
    
    def test_get_event_ajax_nonexist_404(self):
        fake_id = uuid.uuid4()
        response = self.client.get(reverse('event:get_event_ajax', args=[fake_id]))
        self.assertEqual(response.status_code, 404)
    
    def test_get_event_ajax_date_formatting(self):
        response = self.client.get(reverse('event:get_event_ajax', args=[self.future_event.id]))
        data = json.loads(response.content)
        form_html = data['form_html']
        indonesian_months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        has_indonesian_month = any(month in form_html for month in indonesian_months)
        self.assertTrue(has_indonesian_month)
    
    # get_events_ajax
    def test_get_events_ajax_all_events(self):
        response = self.client.get(reverse('event:get_events_ajax'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('upcoming_events', data)
        self.assertIn('past_events', data)
        if data['upcoming_events']:
            event = data['upcoming_events'][0]
            self.assertIn('id', event)
            self.assertIn('judul', event)
            self.assertIn('lokasi', event)
            self.assertIn('kategori_display', event)
            self.assertIn('date_formatted', event)
            self.assertIn('detail_url', event)
            self.assertIn('user_id', event)
    
    def test_get_events_ajax_filter_by_category(self):
        response = self.client.get(reverse('event:get_events_ajax'), {'category': 'basket'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        all_events = data['upcoming_events'] + data['past_events']
        for event in all_events:
            event_obj = Event.objects.get(id=event['id'])
            self.assertEqual(event_obj.kategori, 'basket')
    
    def test_get_events_ajax_upcoming_past_separate(self):
        response = self.client.get(reverse('event:get_events_ajax'))
        data = json.loads(response.content)
        upcoming_ids = [e['id'] for e in data['upcoming_events']]
        past_ids = [e['id'] for e in data['past_events']]
        self.assertIn(str(self.future_event.id), upcoming_ids)
        self.assertIn(str(self.past_event.id), past_ids)
    
    def test_get_events_ajax_event_serialize(self):
        response = self.client.get(reverse('event:get_events_ajax'))
        data = json.loads(response.content)
        future_event_data = None
        for event in data['upcoming_events']:
            if event['id'] == str(self.future_event.id):
                future_event_data = event
                break
        self.assertIsNotNone(future_event_data)
        self.assertEqual(future_event_data['judul'], self.future_event.judul)
        self.assertEqual(future_event_data['lokasi'], self.future_event.lokasi)
        self.assertEqual(future_event_data['user_id'], self.user.id)
    
    def test_get_events_ajax_event_no_user(self):
        event_no_user = Event.objects.create(
            judul='No User Event',
            deskripsi='Test',
            date=timezone.now() + timedelta(days=1),
            lokasi='Location',
            kategori='basket'
        )
        response = self.client.get(reverse('event:get_events_ajax'))
        data = json.loads(response.content)
        event_data = None
        for event in data['upcoming_events']:
            if event['id'] == str(event_no_user.id):
                event_data = event
                break
        
        self.assertIsNotNone(event_data)
        self.assertIsNone(event_data['user_id'])