# news/management/commands/scrape_cnn.py

import requests
from bs4 import BeautifulSoup
import time 
import locale 
from datetime import datetime
from django.core.management.base import BaseCommand
import csv 
import os # Pastikan os diimport

class Command(BaseCommand):
    help = 'Scrapes news articles from CNN Olahraga and saves them to news/articles/cnn_articles.csv'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Memulai scraping CNN Indonesia Olahraga ke CSV...'))
        HEADERS = {
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        BASE_URL = "https://www.cnnindonesia.com"; INDEX_BASE_URL = f"{BASE_URL}/olahraga/indeks/7"
        TOTAL_ARTICLES_TARGET = 500; all_article_elements = []; current_page = 1; max_pages_to_try = 4
        
        try: locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8') 
        except locale.Error: self.stderr.write(self.style.WARNING("Gagal set locale 'id_ID.UTF-8'."))
        
        self.stdout.write(f"Target: {TOTAL_ARTICLES_TARGET} artikel dari max {max_pages_to_try} halaman...")
        # ... (Loop while pagination - TIDAK BERUBAH) ...
        while len(all_article_elements) < TOTAL_ARTICLES_TARGET and current_page <= max_pages_to_try:
            # ... (kode get halaman list, find container, find articles) ...
            if current_page == 1: paginated_url = INDEX_BASE_URL
            else: paginated_url = f"{INDEX_BASE_URL}?page={current_page}"
            # self.stdout.write(f"\nMengambil: {paginated_url}")
            try: list_page = requests.get(paginated_url, headers=HEADERS, timeout=15); list_page.raise_for_status()
            except requests.RequestException as e: self.stderr.write(self.style.ERROR(f' Gagal: {e}. Stop.')); break 
            list_soup = BeautifulSoup(list_page.content, "html.parser")
            list_container = list_soup.find("div", class_="flex flex-col gap-5") 
            if not list_container: self.stderr.write(self.style.WARNING(f" No container di hal {current_page}. Stop.")); break 
            page_article_elements = list_container.find_all("article")
            if not page_article_elements: self.stdout.write(self.style.WARNING(f" No <article> di hal {current_page}. Stop.")); break 
            self.stdout.write(f" > Hal {current_page}: Ditemukan {len(page_article_elements)} artikel.")
            all_article_elements.extend(page_article_elements)
            if len(all_article_elements) >= TOTAL_ARTICLES_TARGET: self.stdout.write(f" > Target tercapai."); break
            current_page += 1
            if len(all_article_elements) < TOTAL_ARTICLES_TARGET: time.sleep(1) # Jeda lebih singkat

        articles_to_process = all_article_elements[:TOTAL_ARTICLES_TARGET]
        self.stdout.write(f"\nTotal artikel yang akan diproses ke CSV: {len(articles_to_process)}.")
        
        processed_count, skipped_count = 0, 0
        scraped_data_list = [] 
        
        # --- Loop Pemrosesan Artikel ---
        for article_element in articles_to_process: 
            processed_count += 1
            
            try:
                # ... (Ambil link, title, thumbnail_small) ...
                link_element = article_element.find("a")
                if not (link_element and link_element.has_attr('href')): skipped_count += 1; continue
                link_relative = link_element['href']
                link_absolute = f"{BASE_URL}{link_relative}" if not link_relative.startswith('http') else link_relative
                title_tag = link_element.find("h2"); list_img_tag = link_element.find("img")
                if not title_tag: skipped_count += 1; continue
                title = title_tag.text.strip()
                thumbnail_small = list_img_tag['src'] if list_img_tag and list_img_tag.has_attr('src') else None
                
                # ... (Filter judul) ...
                title_lower = title.lower()
                if title_lower.startswith(("video:", "foto:", "link", "infografis:")): skipped_count += 1; continue
                
                
                time.sleep(0.5) # Jeda lebih singkat
                
                try:
                    detail_page = requests.get(link_absolute, headers=HEADERS, timeout=15)
                    detail_page.raise_for_status()
                    detail_soup = BeautifulSoup(detail_page.content, "html.parser")
                except requests.RequestException as e: skipped_count += 1; self.stderr.write(self.style.ERROR(f"  > Gagal detail: {e}")); continue 

                # ... (Ambil Gambar - SAMA) ...
                image_container = detail_soup.find("div", class_="detail-image")
                thumbnail_large = None
                if image_container: img_tag_detail = image_container.find("img"); thumbnail_large = img_tag_detail['src'] if img_tag_detail and img_tag_detail.has_attr('src') else None
                thumbnail_to_save = thumbnail_large if thumbnail_large else thumbnail_small

                # ... (Ambil Tanggal String - SAMA) ...
                publish_date_str = "" 
                date_div = detail_soup.find("div", class_="text-cnn_grey text-sm mb-4")
                if date_div: publish_date_str = date_div.text.strip()
                
                # ... (Ambil Konten - SAMA) ...
                content_div = detail_soup.find("div", class_="detail-text")
                if not content_div: content = "" # String kosong jika gagal
                else: 
                    paragraphs = content_div.find_all("p")
                    content_lines = [ p.text.strip() for p in paragraphs if not p.find('a', class_="embed") and p.text.strip()]
                    content = "\n\n".join(content_lines)
                    content = content.replace("ADVERTISEMENT", "").replace("SCROLL TO CONTINUE WITH CONTENT", "")
                    content = "\n".join([line for line in content.splitlines() if line.strip()]) 
                
                # ... (Deteksi Kategori - SAMA) ...
                detected_category = "olahraga lain"; valid_categories_temp = ['sepakbola', 'f1', 'moto gp', 'raket', 'olahraga lain']
                breadcrumb = detail_soup.find("a", class_="gtm_breadcrumb_subkanal"); is_olahraga_lain = False
                if breadcrumb and "Olahraga Lainnya" in breadcrumb.text: detected_category = "olahraga lain"; is_olahraga_lain = True
                if not is_olahraga_lain:
                    subkanal_meta = detail_soup.find("meta", {"name": "subkanal"})
                    if subkanal_meta and subkanal_meta.has_attr('content'): sc = subkanal_meta['content'].lower(); 
                    if sc == "sepakbola": detected_category = "sepakbola"
                    elif sc == "raket": detected_category = "raket"
                if detected_category == "olahraga lain":
                    dtk_kw = detail_soup.find("meta", {"name": "dtk:keywords"}); kw = detail_soup.find("meta", {"name": "keywords"})
                    if dtk_kw and dtk_kw.has_attr('content') and "motogp" in dtk_kw['content'].lower(): detected_category = "moto gp"
                    if detected_category == "olahraga lain" and kw and kw.has_attr('content') and "f1" in kw['content'].lower(): detected_category = "f1"
                
                # --- Tambahkan data ke list ---
                scraped_data_list.append({
                    'title': title, 'content': content,
                    'thumbnail': thumbnail_to_save if thumbnail_to_save else "", 
                    'category': detected_category, 'publish_date_str': publish_date_str,
                    'author_username': 'CNN Indonesia' 
                })
                self.stdout.write(f"  + {title[:40]}...") # Konfirmasi data ditambahkan

            except Exception as e: 
                self.stderr.write(self.style.ERROR(f"  > ERROR proses item {link_absolute}: {e}"))
                skipped_count += 1; continue
        
        if scraped_data_list:
            try:
                # Dapatkan path root app 'news'
                # (__file__ -> scrape_cnn.py -> commands -> management -> news)
                app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                # Tentukan path folder 'articles' di dalam app 'news'
                articles_dir = os.path.join(app_dir, 'articles')
                # Buat folder jika belum ada
                os.makedirs(articles_dir, exist_ok=True) 
                # Tentukan path file CSV di dalam folder 'articles'
                csv_file_path = os.path.join(articles_dir, 'cnn_articles.csv')

                fieldnames = ['title', 'content', 'thumbnail', 'category', 'publish_date_str', 'author_username']
                
                self.stdout.write(f"\nMenulis {len(scraped_data_list)} artikel ke {csv_file_path}...")
                with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader() 
                    writer.writerows(scraped_data_list) 
                    
                self.stdout.write(self.style.SUCCESS(f"Berhasil menyimpan data ke {csv_file_path}"))
            except IOError as e: self.stderr.write(self.style.ERROR(f"Gagal menulis CSV: {e}"))
            except Exception as e: self.stderr.write(self.style.ERROR(f"Error tak terduga saat tulis CSV: {e}"))
        else: self.stdout.write(self.style.WARNING("Tidak ada data untuk disimpan ke CSV."))
        # ----------------------------------------

        self.stdout.write(self.style.SUCCESS(f"\nSelesai! {len(scraped_data_list)} data siap ditulis, {skipped_count} dilewati, {processed_count} diproses."))