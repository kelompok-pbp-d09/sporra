import requests
from bs4 import BeautifulSoup
import time 
import locale 
from datetime import datetime
from django.conf import settings 
import pytz 
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from news.models import Article

class Command(BaseCommand):
    help = 'Scrapes news articles from CNN Olahraga, stores publish date in created_at'

    def handle(self, *args, **options):
        # ... (Kode setup Headers, Author, URL, Locale - SAMA) ...
        self.stdout.write(self.style.NOTICE('Memulai scraping CNN Indonesia Olahraga...'))
        HEADERS = { # ... headers ... 
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try: # ... dapatkan cnn_author ...
            cnn_author = User.objects.get(username='CNN Indonesia')
        except User.DoesNotExist: # ... error handling ...
            self.stderr.write(self.style.ERROR('User "CNN Indonesia" tidak ditemukan!')); return
        BASE_URL = "https://www.cnnindonesia.com"; INDEX_BASE_URL = f"{BASE_URL}/olahraga/indeks/7"
        TOTAL_ARTICLES_TARGET = 110; all_article_elements = []; current_page = 1; max_pages_to_try = 11
        try: locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8') 
        except locale.Error: self.stderr.write(self.style.WARNING("Gagal set locale 'id_ID.UTF-8'."))
        
        # ... (Loop pagination - SAMA) ...
        self.stdout.write(f"Target: {TOTAL_ARTICLES_TARGET} artikel dari max {max_pages_to_try} halaman...")
        while len(all_article_elements) < TOTAL_ARTICLES_TARGET and current_page <= max_pages_to_try:
            # ... (kode get halaman list, find container, find articles - SAMA) ...
            if current_page == 1: paginated_url = INDEX_BASE_URL
            else: paginated_url = f"{INDEX_BASE_URL}?page={current_page}"
            self.stdout.write(f"\nMengambil: {paginated_url}")
            try: list_page = requests.get(paginated_url, headers=HEADERS, timeout=15); list_page.raise_for_status()
            except requests.RequestException as e: self.stderr.write(self.style.ERROR(f' Gagal: {e}. Stop.')); break 
            list_soup = BeautifulSoup(list_page.content, "html.parser")
            list_container = list_soup.find("div", class_="flex flex-col gap-5") 
            if not list_container: self.stderr.write(self.style.WARNING(f" No container di hal {current_page}. Stop.")); break 
            page_article_elements = list_container.find_all("article")
            if not page_article_elements: self.stdout.write(self.style.WARNING(f" No <article> di hal {current_page}. Stop.")); break 
            self.stdout.write(f" > Ditemukan {len(page_article_elements)} artikel.")
            all_article_elements.extend(page_article_elements)
            if len(all_article_elements) >= TOTAL_ARTICLES_TARGET: self.stdout.write(f" > Target tercapai."); break
            current_page += 1
            time.sleep(2) 
        
        articles_to_process = all_article_elements[:TOTAL_ARTICLES_TARGET]
        self.stdout.write(f"\nTotal akan diproses: {len(articles_to_process)}.")
        created_count, processed_count, skipped_count = 0, 0, 0
        
        # --- Loop Pemrosesan Artikel ---
        for article_element in articles_to_process: 
            processed_count += 1
            self.stdout.write(f"\n--- Memproses {processed_count}/{len(articles_to_process)} ---")
            
            try:
                # ... (Ambil link, title, thumbnail_small - SAMA) ...
                link_element = article_element.find("a")
                if not (link_element and link_element.has_attr('href')): skipped_count += 1; continue
                link_relative = link_element['href']
                link_absolute = f"{BASE_URL}{link_relative}" if not link_relative.startswith('http') else link_relative
                title_tag = link_element.find("h2"); list_img_tag = link_element.find("img")
                if not title_tag: skipped_count += 1; continue
                title = title_tag.text.strip()
                thumbnail_small = list_img_tag['src'] if list_img_tag and list_img_tag.has_attr('src') else None
                
                # ... (Filter judul - SAMA) ...
                title_lower = title.lower()
                if title_lower.startswith(("video:", "foto:", "link")): skipped_count += 1; self.stdout.write(self.style.WARNING(f"  > Skip: {title[:30]}...")); continue
                self.stdout.write(f"  > Judul: {title}")
                if Article.objects.filter(title=title).exists(): skipped_count += 1; self.stdout.write(self.style.WARNING(f"  > Skip: Sudah ada.")); continue
                
                time.sleep(1) 
                
                # --- Ambil Halaman Detail ---
                try: # ... (ambil detail_page, detail_soup - SAMA) ...
                    detail_page = requests.get(link_absolute, headers=HEADERS, timeout=15)
                    detail_page.raise_for_status()
                    detail_soup = BeautifulSoup(detail_page.content, "html.parser")
                except requests.RequestException as e: skipped_count += 1; self.stderr.write(self.style.ERROR(f"  > Gagal ambil detail: {e}")); continue 

                # ... (Ambil Gambar Utama - SAMA) ...
                image_container = detail_soup.find("div", class_="detail-image")
                thumbnail_large = None
                if image_container: img_tag_detail = image_container.find("img"); thumbnail_large = img_tag_detail['src'] if img_tag_detail and img_tag_detail.has_attr('src') else None
                thumbnail_to_save = thumbnail_large if thumbnail_large else thumbnail_small

                # --- Ambil dan Parse Tanggal Publikasi (SAMA) ---
                publish_datetime = None 
                date_div = detail_soup.find("div", class_="text-cnn_grey text-sm mb-4")
                if date_div:
                    date_text = date_div.text.strip()
                    try:
                        naive_datetime = datetime.strptime(date_text, "%A, %d %b %Y %H:%M WIB")
                        server_timezone = pytz.timezone(settings.TIME_ZONE) 
                        publish_datetime = server_timezone.localize(naive_datetime)
                        self.stdout.write(f"  > Tanggal Publikasi: {publish_datetime.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
                    except ValueError as ve: self.stderr.write(self.style.ERROR(f"  > Gagal parsing tanggal '{date_text}': {ve}"))
                    except Exception as e: self.stderr.write(self.style.ERROR(f"  > Error proses tanggal '{date_text}': {e}"))
                else: self.stdout.write(self.style.WARNING("  > Div tanggal tidak ditemukan."))
                # ----------------------------------------

                # ... (Ambil Konten - SAMA) ...
                content_div = detail_soup.find("div", class_="detail-text")
                if not content_div: content = "Konten tidak dapat diambil."; self.stderr.write(self.style.ERROR(f"  > Gagal ambil konten di {link_absolute}."))
                else: 
                    paragraphs = content_div.find_all("p")
                    content_lines = [ p.text.strip() for p in paragraphs if not p.find('a', class_="embed") and p.text.strip()]
                    content = "\n\n".join(content_lines)
                    content = content.replace("ADVERTISEMENT", "").replace("SCROLL TO CONTINUE WITH CONTENT", "")
                    content = "\n".join([line for line in content.splitlines() if line.strip()]) 
                
                # ... (Deteksi Kategori - SAMA) ...
                detected_category = "olahraga lain"; valid_categories = [c[0] for c in Article.CATEGORY_CHOICES]
                subkanal_meta = detail_soup.find("meta", {"name": "subkanal"}); breadcrumb = detail_soup.find("a", class_="gtm_breadcrumb_subkanal")
                dtk_kw = detail_soup.find("meta", {"name": "dtk:keywords"}); kw = detail_soup.find("meta", {"name": "keywords"})
                if subkanal_meta and subkanal_meta.has_attr('content'): sc = subkanal_meta['content'].lower(); 
                if sc == "sepakbola" and "sepakbola" in valid_categories: detected_category = "sepakbola"
                elif sc == "raket" and "raket" in valid_categories: detected_category = "raket"
                if detected_category == "olahraga lain" and breadcrumb and "Olahraga Lainnya" in breadcrumb.text and "olahraga lain" in valid_categories: detected_category = "olahraga lain"
                if detected_category == "olahraga lain" and dtk_kw and dtk_kw.has_attr('content') and "motogp" in dtk_kw['content'].lower() and "moto gp" in valid_categories: detected_category = "moto gp"
                if detected_category == "olahraga lain" and kw and kw.has_attr('content') and "f1" in kw['content'].lower() and "f1" in valid_categories: detected_category = "f1"
                self.stdout.write(f"  > Kategori: {detected_category}")
                
                creation_time = publish_datetime if publish_datetime else timezone.now()

                Article.objects.create(
                    title=title, 
                    content=content, 
                    thumbnail=thumbnail_to_save, 
                    category=detected_category, 
                    author=cnn_author,
                    created_at=creation_time
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  > SUKSES: Artikel disimpan!"))
                # ---------------------------------

            except Exception as e: 
                self.stderr.write(self.style.ERROR(f"  > ERROR proses item {link_absolute}: {e}"))
                skipped_count += 1; continue
        
        self.stdout.write(self.style.SUCCESS(f"\nSelesai! {created_count} baru, {skipped_count} dilewati, {processed_count} diproses."))