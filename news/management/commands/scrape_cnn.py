import requests
from bs4 import BeautifulSoup
import time # Untuk jeda
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from news.models import Article # Impor model Article kamu

class Command(BaseCommand):
    help = 'Scrapes news articles from CNN Indonesia Olahraga'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Memulai scraping CNN Indonesia Olahraga...'))

        HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # --- Dapatkan User "CNN Indonesia" ---
        try:
            cnn_author = User.objects.get(username='CNN Indonesia')
            self.stdout.write(f"Menggunakan author: {cnn_author.username} (ID: {cnn_author.id})")
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'User "CNN Indonesia" tidak ditemukan! '
                'Buat dulu user dengan username "CNN Indonesia" via admin atau shell, '
                'lalu set password-nya dengan set_unusable_password().'
            ))
            return # Hentikan script jika user tidak ada

        # --- Logika Scraper ---
        BASE_URL = "https://www.cnnindonesia.com"
        URL = f"{BASE_URL}/olahraga/indeks/7"

        try:
            page = requests.get(URL, headers=HEADERS, timeout=10)
            page.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f'Gagal mengambil URL daftar: {e}'))
            return

        soup = BeautifulSoup(page.content, "html.parser")

        # --- Selector Halaman Daftar (List Page) ---
        list_container = soup.find("div", class_="flex flex-col gap-5")
        if not list_container:
            self.stderr.write(self.style.ERROR(
                "Gagal menemukan list container utama (div.flex.flex-col.gap-5). "
                "Struktur HTML CNN mungkin berubah."
            ))
            return

        article_elements = list_container.find_all("article")
        self.stdout.write(f"Menemukan {len(article_elements)} potensi artikel di halaman daftar.")

        created_count = 0
        processed_count = 0
        # --- Batasi jumlah artikel untuk testing (misal 5) ---
        MAX_ARTICLES_TO_SCRAPE = 6

        for article_element in article_elements[:MAX_ARTICLES_TO_SCRAPE]: # Ambil beberapa saja
            processed_count += 1
            self.stdout.write(f"\n--- Memproses Artikel {processed_count}/{MAX_ARTICLES_TO_SCRAPE} ---")
            try:
                link_element = article_element.find("a")
                if not (link_element and link_element.has_attr('href')):
                    self.stdout.write(self.style.WARNING("  > Lewati item: tidak ada link ditemukan."))
                    continue

                # --- Ambil data dari halaman daftar ---
                link = link_element['href']
                if not link.startswith('http'):
                    link = f"{BASE_URL}{link}" # Pastikan URL absolut

                title_tag = link_element.find("h2")
                img_tag = link_element.find("img")

                if not title_tag:
                    self.stdout.write(self.style.WARNING(f"  > Lewati item: tidak ada judul ditemukan di {link}"))
                    continue
                
                title = title_tag.text.strip()
                thumbnail = img_tag['src'] if img_tag and img_tag.has_attr('src') else None

                self.stdout.write(f"  > Judul: {title}")
                self.stdout.write(f"  > Link: {link}")

                # --- Jeda sebelum request halaman detail ---
                self.stdout.write("  > Menunggu 1 detik...")
                time.sleep(1) 

                # --- Ambil Halaman Detail ---
                try:
                    detail_page = requests.get(link, headers=HEADERS, timeout=10)
                    detail_page.raise_for_status()
                except requests.RequestException as e:
                    self.stderr.write(self.style.ERROR(f"  > Gagal mengambil URL detail {link}: {e}"))
                    continue # Lanjut ke artikel berikutnya

                detail_soup = BeautifulSoup(detail_page.content, "html.parser")

                # --- Selector Halaman Detail (Konten) ---
                content_div = detail_soup.find("div", class_="detail-text")

                if not content_div:
                    self.stderr.write(self.style.ERROR(f"  > Gagal menemukan konten (div#detail-text) di {link}. Struktur detail mungkin berubah."))
                    content = "Konten tidak ditemukan." # Simpan pesan error saja
                else:
                    paragraphs = content_div.find_all("p")
                    # Gabungkan paragraf, bersihkan iklan/embed, hapus spasi berlebih
                    content_lines = [
                        p.text.strip() for p in paragraphs 
                        if not p.find('a', class_="embed") and p.text.strip() # Hindari embed & paragraf kosong
                    ]

                    content = "\n\n".join(content_lines)

                    #Hapus teks iklan
                    content = content.replace("ADVERTISEMENT", "")
                    content = content.replace("SCROLL TO CONTINUE WITH CONTENT", "")

                    content = "\n".join([line for line in content.splitlines() if line.strip()])

                    self.stdout.write(f"  > Konten ditemukan ({len(content_lines)} paragraf).")


                # --- Tentukan Kategori (Contoh Sederhana) ---
                # Kamu bisa buat logika lebih canggih di sini
                category = "sepakbola" # Default
                if "/moto-gp/" in link:
                    category = "moto gp"
                elif "/f1/" in link:
                    category = "f1"
                elif "/raket/" in link or "bulu tangkis" in title.lower():
                    category = "bulu tangkis"
                # ... tambahkan kategori lain jika perlu


                # --- Simpan ke Database Django ---
                article, created = Article.objects.get_or_create(
                    title=title, # Anggap judul unik untuk mencegah duplikat
                    defaults={
                        'content': content,
                        'thumbnail': thumbnail,
                        'category': category,
                        'author': cnn_author, # User "CNN Indonesia"
                        # 'created_at' akan otomatis diisi
                        # 'news_views' default 0
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  > SUKSES: Artikel baru disimpan ke database!"))
                else:
                    self.stdout.write(self.style.WARNING(f"  > INFO: Artikel dengan judul ini sudah ada, dilewati."))

            except Exception as e:
                # Tangkap error spesifik item agar loop tidak berhenti
                self.stderr.write(self.style.ERROR(f"  > ERROR saat memproses item: {e}"))
                # Pertimbangkan untuk log error ini ke file jika perlu

        # --- Selesai ---
        self.stdout.write(self.style.SUCCESS(
            f"\nScraping selesai! {created_count} artikel baru ditambahkan dari {processed_count} item yang diproses."
        ))