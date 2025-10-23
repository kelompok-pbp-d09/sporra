import csv
import os
import locale
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from news.models import Article
from django.conf import settings
import pytz
from django.utils import timezone

class Command(BaseCommand):
    help = 'Populates the Article database from cnn_articles.csv file in project root'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Memulai populasi database dari cnn_articles.csv...'))

        # Dapatkan path root project dan path file CSV
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_file_path = os.path.join(project_root + '/articles', 'cnn_articles.csv')

        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f"File {csv_file_path} tidak ditemukan. Jalankan 'scrape_cnn' dulu."))
            return

        # Set locale untuk parsing tanggal (sama seperti scraper)
        try:
            locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
        except locale.Error:
            self.stderr.write(self.style.WARNING("Gagal set locale 'id_ID.UTF-8'. Parsing tanggal mungkin gagal."))

        # Dapatkan user author
        try:
            author = User.objects.get(username='CNN Indonesia')
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR('User "CNN Indonesia" tidak ditemukan di database. Buat dulu.'))
            return

        added_count = 0
        skipped_count = 0
        error_count = 0
        row_count = 0
        
        try:
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    row_count += 1
                    title = row.get('title', '').strip()
                    publish_date_str = row.get('publish_date_str', '').strip()
                    category = row.get('category', '').strip()
                    
                    if not title:
                        self.stderr.write(self.style.ERROR(f" Baris {row_count + 1}: Judul kosong, dilewati."))
                        error_count += 1
                        continue

                    # Cek duplikat berdasarkan judul
                    if Article.objects.filter(title=title).exists():
                        # self.stdout.write(f" Baris {row_count + 1}: Artikel '{title[:30]}...' sudah ada, dilewati.")
                        skipped_count += 1
                        continue
                        
                    # Parse tanggal
                    publish_datetime = None
                    if publish_date_str:
                        try:
                            naive_datetime = datetime.strptime(publish_date_str, "%A, %d %b %Y %H:%M WIB")
                            server_timezone = pytz.timezone(settings.TIME_ZONE) 
                            publish_datetime = server_timezone.localize(naive_datetime)
                        except ValueError:
                            self.stderr.write(self.style.ERROR(f" Baris {row_count + 1}: Gagal parsing tanggal '{publish_date_str}'"))
                            # Tetap lanjut, created_at akan pakai default timezone.now()
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f" Baris {row_count + 1}: Error tak terduga saat parsing tanggal: {e}"))
                    
                    # Tentukan waktu pembuatan (pakai publish jika ada, jika tidak pakai now)
                    creation_time = publish_datetime if publish_datetime else timezone.now()
                    
                    # Validasi kategori (pastikan ada di choices)
                    valid_categories = [c[0] for c in Article.CATEGORY_CHOICES]
                    if category not in valid_categories:
                        self.stderr.write(self.style.WARNING(f" Baris {row_count + 1}: Kategori '{category}' tidak valid, diubah ke 'olahraga lain'."))
                        category = 'olahraga lain' # Fallback ke default

                    # Buat objek Article
                    try:
                        Article.objects.create(
                            title=title,
                            content=row.get('content', ''),
                            thumbnail=row.get('thumbnail', None), # Ambil None jika kosong
                            category=category,
                            author=author,
                            created_at=creation_time
                            # news_views akan default ke 0
                        )
                        added_count += 1
                        # self.stdout.write(self.style.SUCCESS(f" Baris {row_count + 1}: Artikel '{title[:30]}...' berhasil ditambahkan."))
                    except Exception as e:
                         self.stderr.write(self.style.ERROR(f" Baris {row_count + 1}: Gagal menyimpan artikel '{title[:30]}...': {e}"))
                         error_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"\nPopulasi selesai! {added_count} artikel baru ditambahkan. "
                f"{skipped_count} dilewati (duplikat). {error_count} error. Total {row_count} baris diproses."
            ))

        except FileNotFoundError:
             self.stderr.write(self.style.ERROR(f"File {csv_file_path} tidak ditemukan."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error saat membaca atau memproses CSV: {e}"))