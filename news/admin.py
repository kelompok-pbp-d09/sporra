# news/admin.py

from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Kustomisasi tampilan untuk model Article di halaman admin.
    """
    
    # Menampilkan kolom-kolom ini di daftar artikel
    # Kita ganti 'published_date' -> 'created_at'
    # Kita ganti 'image' -> 'news_views' (views lebih berguna di list)
    list_display = ('title', 'author', 'category', 'created_at', 'news_views', 'is_news_hot')
    
    # Menambahkan filter di sidebar kanan
    # Kita ganti 'published_date' -> 'created_at'
    list_filter = ('category', 'author', 'created_at')
    
    # Menambahkan kotak pencarian
    search_fields = ('title', 'content')
    
    # HAPUS 'prepopulated_fields' KARENA KITA TIDAK PUNYA FIELD 'slug'
    
    # Tambahan: Membuat field ini "read-only" di halaman edit admin
    # karena field ini diisi otomatis oleh sistem
    readonly_fields = ('created_at', 'news_views', 'id')

    # Mengelompokkan field di halaman edit
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'category', 'thumbnail', 'content')
        }),
        ('Info Otomatis', {
            'fields': ('id', 'created_at', 'news_views'),
            'classes': ('collapse',)  # Sembunyikan grup ini by default
        }),
    )