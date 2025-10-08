# Spora

Anggota Kelompok:
1. Afero Aqil Roihan (2406352304)  
2. Andi Hakim Himawan  (2406495792)
3. Dylan Pirade Ponglabba (2406496126)
4. Farrel Faridzi Liwungang (2406436240)
5. Naila Shafa Azizah (2406356510)

Deskripsi Aplikasi
- Ide umum: Forum dan Komunitas Olahraga 

- Deskripsi: Forum komunitas olahraga ini menjadi wadah diskusi dan berbagi informasi seputar berbagai cabang olahraga. Pengguna dapat membuat postingan pertanyaan maupun pengalaman, memberikan komentar, serta memberi like atau upvote pada posting yang dianggap bermanfaat. Setiap cabang olahraga, seperti sepak bola, basket, badminton, dan sebagainya, memiliki kategori tersendiri sehingga percakapan lebih terorganisir dan mudah diikuti. Selain forum diskusi, tersedia fitur opsional untuk membuat dan bergabung dalam event olahraga, misalnya mengadakan tanding futsal atau jogging bersama.

Modul
1. Modul Autentikasi & Profil Pengguna

 - Registrasi, login, logout, dan manajemen sesi user.
 - Model UserProfile dengan atribut tambahan (username, bio, foto profil, reputasi poin dari upvotes).
 - Filter informasi sensitif (misalnya email/nomor HP hanya terlihat oleh user yang login).
 - Tampilan profil: daftar posting, komentar, dan event yang diikuti.

2. Modul Kategori & Forum Diskusi

 - Model Category (contoh: Sepak Bola, Basket, Badminton).
 - Model Post untuk thread diskusi dan Comment untuk balasan.
 - Fitur upvote/downvote pada post & komentar.
 - Tampilan: daftar post per kategori, halaman detail post dengan threaded comments.

3. Modul Event Olahraga

 - Model Event (judul, deskripsi, kategori olahraga, lokasi, waktu, peserta maksimal, daftar peserta).
 - CRUD event (create, update, delete event).
 - User bisa klik Join Event atau Leave Event.
 - Halaman Events Page (list + kalender sederhana).

4. Modul Dataset Produk Olahragaa

 - Initial dataset: minimal 100 produk olahraga (misalnya sepatu bola, raket badminton, bola basket, jersey, dll).
 - Model Product dengan kategori utama produk.
 - Fitur filter (misalnya berdasarkan harga, kategori olahraga).
 - Tampilan daftar produk dengan responsive design (Bootstrap/Tailwind).

5. Modul Integrasi & Fitur Tambahan

 - Base template (base.html, header.html, footer.html) untuk konsistensi desain dark theme.
 - Implementasi AJAX (misalnya untuk upvote/downvote tanpa reload halaman).
 - URL mapping untuk seluruh modul dan integrasi jadi satu aplikasi.
 - Unit testing untuk memastikan tiap modul bekerja (target ≥80% coverage).
 - Deployment ke PWS.

 Role Pengguna:
 1. User biasa : Dapat post komentar dan balasannya, dapat mengadakan suatu event, dan mengedit/menghapus post dari dirinya sendiri.
 2. Admin : Dapat melakukan semua yang user biasa lakukan dengan tambahan dapat menghapus post event/komentar dari user lain.
