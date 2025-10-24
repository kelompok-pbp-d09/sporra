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
    help = 'Populates the Article database from news/articles/cnn_articles.csv'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Memulai populasi database dari cnn_articles.csv...'))

        # Path ke CSV (menggunakan path yang benar di dalam app 'news')
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        articles_dir = os.path.join(app_dir, 'articles')
        csv_file_path = os.path.join(articles_dir, 'cnn_articles.csv')

        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f"File {csv_file_path} tidak ditemukan. Jalankan 'scrape_cnn' dulu."))
            return
        

        try:
            author = User.objects.get(username='CNN Indonesia')
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR('User "CNN Indonesia" tidak ditemukan di database. Buat dulu.'))
            return
        
        # Mapping bulan (kunci ID, value EN)
        month_mapping_id_to_en = {
            'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Apr', 
            'Mei': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Agu': 'Aug', 
            'Sep': 'Sep', 'Okt': 'Oct', 'Nov': 'Nov', 'Des': 'Dec'
        }

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

                    if Article.objects.filter(title=title).exists():
                        skipped_count += 1
                        continue
                        
                    # --- Blok Parsing Tanggal ---
                    publish_datetime = None
                    if publish_date_str:
                        date_str_cleaned = "" # Definisikan di luar scope try
                        format_string = "%d %b %Y %H:%M" # Definisikan di luar scope try
                        try:
                            # 1. Hapus Nama Hari
                            date_part_only = publish_date_str
                            if ", " in publish_date_str:
                                date_part_only = publish_date_str.split(", ", 1)[1]
                            
                            # 2. Ganti bulan ke Inggris
                            date_str_en = date_part_only 
                            for id_month, en_month in month_mapping_id_to_en.items():
                                if id_month in date_str_en:
                                    date_str_en = date_str_en.replace(id_month, en_month)
                                    break

                            # 3. HAPUS " WIB"
                            if date_str_en.endswith(" WIB"):
                                date_str_cleaned = date_str_en[:-4].strip()
                            else:
                                date_str_cleaned = date_str_en.strip()

                            # 4. Format string (sudah didefinisikan di atas)
                            
                            # 5. Parsing string yang sudah SANGAT bersih
                            # --- INI PERBAIKANNYA ---
                            naive_datetime = datetime.strptime(date_str_cleaned, format_string) 
                            # -------------------------
                            
                            # 6. Jadikan timezone-aware
                            server_timezone = pytz.timezone(settings.TIME_ZONE) 
                            publish_datetime = server_timezone.localize(naive_datetime)
                            
                        except ValueError as ve: 
                            # Log error yang benar
                            self.stderr.write(self.style.ERROR(f" Baris {row_count + 1}: Gagal parsing '{publish_date_str}' (String bersih: '{date_str_cleaned}') -> {ve}"))
                            error_count += 1
                            continue # Lanjut ke baris berikutnya
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f" Baris {row_count + 1}: Error tak terduga parsing tanggal: {e}"))
                            error_count += 1
                            continue # Lanjut ke baris berikutnya
                    # --- Akhir Blok Parsing ---

                    # Tentukan waktu pembuatan (pakai publish jika ada, jika tidak pakai now)
                    creation_time = publish_datetime if publish_datetime else timezone.now()
                    
                    # Validasi kategori
                    valid_categories = [c[0] for c in Article.CATEGORY_CHOICES]
                    if category not in valid_categories:
                        self.stderr.write(self.style.WARNING(f" Baris {row_count + 1}: Kategori '{category}' tidak valid, diubah ke 'olahraga lain'."))
                        category = 'olahraga lain' 

                    # Buat objek Article
                    try:
                        Article.objects.create(
                            title=title,
                            content=row.get('content', ''),
                            thumbnail=row.get('thumbnail') if row.get('thumbnail') else None,
                            category=category,
                            author=author,
                            created_at=creation_time
                        )
                        added_count += 1
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