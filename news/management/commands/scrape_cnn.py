import requests
from bs4 import BeautifulSoup
import time 
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from news.models import Article # Impor model Article kamu

class Command(BaseCommand):
    help = 'Scrapes news articles from CNN Indonesia Olahraga with category detection and filtering'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Memulai scraping CNN Indonesia Olahraga...'))

        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            cnn_author = User.objects.get(username='CNN Indonesia')
            self.stdout.write(f"Menggunakan author: {cnn_author.username} (ID: {cnn_author.id})")
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR('User "CNN Indonesia" tidak ditemukan! Buat dulu.'))
            return

        BASE_URL = "https://www.cnnindonesia.com"
        INDEX_BASE_URL = f"{BASE_URL}/olahraga/indeks/7" # Kategori Olahraga
        
        # --- Logika Pagination ---
        TOTAL_ARTICLES_TARGET = 110
        all_article_elements = []
        current_page = 1
        max_pages_to_try = 11

        self.stdout.write(f"Mencoba mengambil hingga {TOTAL_ARTICLES_TARGET} artikel dari max {max_pages_to_try} halaman...")

        while len(all_article_elements) < TOTAL_ARTICLES_TARGET and current_page <= max_pages_to_try:
            if current_page == 1:
                paginated_url = INDEX_BASE_URL
            else:
                paginated_url = f"{INDEX_BASE_URL}?page={current_page}"
            
            self.stdout.write(f"\nMengambil halaman: {paginated_url}")

            try:
                list_page = requests.get(paginated_url, headers=HEADERS, timeout=15)
                list_page.raise_for_status()
            except requests.RequestException as e:
                self.stderr.write(self.style.ERROR(f' Gagal mengambil {paginated_url}: {e}. Stop.'))
                break 

            list_soup = BeautifulSoup(list_page.content, "html.parser")
            list_container = list_soup.find("div", class_="flex flex-col gap-5") 

            if not list_container:
                self.stderr.write(self.style.WARNING(f" Container artikel tidak ditemukan di hal {current_page}. Stop."))
                break 

            page_article_elements = list_container.find_all("article")
            if not page_article_elements:
                self.stdout.write(self.style.WARNING(f" Tidak ada <article> di hal {current_page}. Stop."))
                break 

            self.stdout.write(f" > Menemukan {len(page_article_elements)} artikel di hal {current_page}.")
            all_article_elements.extend(page_article_elements)
            
            if len(all_article_elements) >= TOTAL_ARTICLES_TARGET:
                 self.stdout.write(f" > Target {TOTAL_ARTICLES_TARGET} artikel tercapai.")
                 break

            current_page += 1
            self.stdout.write(f" > Menunggu 2 detik...")
            time.sleep(2) 

        articles_to_process = all_article_elements[:TOTAL_ARTICLES_TARGET]
        self.stdout.write(f"\nTotal artikel yg akan diproses: {len(articles_to_process)}.")

        created_count = 0
        processed_count = 0
        skipped_count = 0
        
        # --- Loop Pemrosesan Artikel ---
        for article_element in articles_to_process: 
            processed_count += 1
            self.stdout.write(f"\n--- Memproses Artikel {processed_count}/{len(articles_to_process)} ---")
            
            try:
                link_element = article_element.find("a")
                if not (link_element and link_element.has_attr('href')):
                    self.stdout.write(self.style.WARNING("  > Lewati: tidak ada link <a>."))
                    skipped_count += 1
                    continue

                link_relative = link_element['href']
                link_absolute = f"{BASE_URL}{link_relative}" if not link_relative.startswith('http') else link_relative
                
                title_tag = link_element.find("h2")
                list_img_tag = link_element.find("img")
                if not title_tag: 
                    self.stdout.write(self.style.WARNING(f"  > Lewati: tidak ada <h2>."))
                    skipped_count += 1
                    continue
                
                title = title_tag.text.strip()
                thumbnail_small = list_img_tag['src'] if list_img_tag and list_img_tag.has_attr('src') else None

                # --- FILTER JUDUL ---
                title_lower = title.lower()
                if title_lower.startswith("video:") or title_lower.startswith("foto:") or title_lower.startswith("link"):
                    self.stdout.write(self.style.WARNING(f"  > Lewati: Judul '{title[:30]}...' adalah Video/Foto/Link."))
                    skipped_count += 1
                    continue
                # ------------------

                self.stdout.write(f"  > Judul: {title}")
                
                if Article.objects.filter(title=title).exists():
                    self.stdout.write(self.style.WARNING(f"  > INFO: Artikel sudah ada, dilewati."))
                    skipped_count += 1
                    continue
                
                time.sleep(1) 

                # --- Ambil Halaman Detail ---
                try:
                    detail_page = requests.get(link_absolute, headers=HEADERS, timeout=15)
                    detail_page.raise_for_status()
                except requests.RequestException as e:
                     self.stderr.write(self.style.ERROR(f"  > Gagal ambil detail {link_absolute}: {e}"))
                     skipped_count += 1
                     continue 
                
                detail_soup = BeautifulSoup(detail_page.content, "html.parser")

                # --- Ambil Gambar Utama ---
                image_container = detail_soup.find("div", class_="detail-image")
                thumbnail_large = None
                if image_container:
                    img_tag_detail = image_container.find("img")
                    if img_tag_detail and img_tag_detail.has_attr('src'):
                        thumbnail_large = img_tag_detail['src']
                thumbnail_to_save = thumbnail_large if thumbnail_large else thumbnail_small

                # --- Ambil Konten ---
                content_div = detail_soup.find("div", class_="detail-text")
                if not content_div:
                    content = "Konten tidak dapat diambil."
                    self.stderr.write(self.style.ERROR(f"  > Gagal ambil konten (div.detail-text) di {link_absolute}."))
                else:
                    paragraphs = content_div.find_all("p")
                    content_lines = [ p.text.strip() for p in paragraphs if not p.find('a', class_="embed") and p.text.strip()]
                    content = "\n\n".join(content_lines)
                    content = content.replace("ADVERTISEMENT", "").replace("SCROLL TO CONTINUE WITH CONTENT", "")
                    content = "\n".join([line for line in content.splitlines() if line.strip()]) 
                    # self.stdout.write(f"  > Konten ditemukan ({len(content_lines)} paragraf).") # Opsional

                # --- DETEKSI KATEGORI ---
                # Default category (pastikan 'olahraga lain' ada di choices model)
                detected_category = "olahraga lain" 
                valid_categories = [choice[0] for choice in Article.CATEGORY_CHOICES]

                # 1. Cek Meta Subkanal
                subkanal_meta = detail_soup.find("meta", {"name": "subkanal"})
                if subkanal_meta and subkanal_meta.has_attr('content'):
                    subkanal_content = subkanal_meta['content'].lower()
                    if subkanal_content == "sepakbola" and "sepakbola" in valid_categories:
                        detected_category = "sepakbola"
                    elif subkanal_content == "raket" and "raket" in valid_categories:
                        detected_category = "raket"
                    # Tambahkan subkanal lain jika perlu

                # 2. Jika masih default, cek Breadcrumb (khusus Olahraga Lain)
                if detected_category == "olahraga lain":
                    breadcrumb_subkanal = detail_soup.find("a", class_="gtm_breadcrumb_subkanal")
                    if breadcrumb_subkanal and "Olahraga Lainnya" in breadcrumb_subkanal.text:
                         if "olahraga lain" in valid_categories:
                             detected_category = "olahraga lain" # Konfirmasi

                # 3. Jika masih default, cek Keywords
                if detected_category == "olahraga lain":
                    dtk_keywords_meta = detail_soup.find("meta", {"name": "dtk:keywords"})
                    if dtk_keywords_meta and dtk_keywords_meta.has_attr('content'):
                        if "motogp" in dtk_keywords_meta['content'].lower() and "moto gp" in valid_categories:
                            detected_category = "moto gp"
                    
                    # Jika belum ketemu motogp, cek keywords standar untuk f1
                    if detected_category == "olahraga lain": # Cek lagi agar tidak menimpa motogp
                        keywords_meta = detail_soup.find("meta", {"name": "keywords"})
                        if keywords_meta and keywords_meta.has_attr('content'):
                            if "f1" in keywords_meta['content'].lower() and "f1" in valid_categories:
                                detected_category = "f1"

                self.stdout.write(f"  > Kategori: {detected_category}")
                # -------------------------

                # --- Simpan ke Database ---
                Article.objects.create(
                    title=title, 
                    content=content, 
                    thumbnail=thumbnail_to_save, 
                    category=detected_category, # Gunakan kategori yang terdeteksi
                    author=cnn_author, 
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  > SUKSES: Artikel '{title[:30]}...' disimpan!"))

            except Exception as e: 
                self.stderr.write(self.style.ERROR(f"  > ERROR proses item {link_absolute}: {e}"))
                skipped_count += 1
                continue
        
        # --- Pesan Selesai ---
        self.stdout.write(self.style.SUCCESS(
            f"\nScraping selesai! {created_count} artikel baru. {skipped_count} dilewati. "
            f"{processed_count} total diproses."
        ))