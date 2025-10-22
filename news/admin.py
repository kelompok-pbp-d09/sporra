from django.contrib import admin
from .models import Article # Impor model kamu

# Dekorator @admin.register secara otomatis mendaftarkan Article
# dan mengaitkannya dengan class kustomisasi ArticleAdmin
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Kustomisasi tampilan untuk model Article di halaman admin.
    ModelAdmin menyediakan semua fitur CRUD.
    """
    
    # Menentukan kolom apa saja yang tampil di halaman daftar artikel (/admin/news/article/)
    list_display = ('title', 'author', 'category', 'created_at', 'news_views', 'is_news_hot')
    
    # Menambahkan filter di sidebar kanan
    list_filter = ('category', 'author', 'created_at')
    
    # Menambahkan kotak pencarian
    search_fields = ('title', 'content')
    
    # Membuat field ini tidak bisa diedit di halaman admin
    readonly_fields = ('created_at', 'news_views', 'id')

    # Mengelompokkan field di halaman tambah/edit artikel
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'category', 'thumbnail', 'content')
        }),
        ('Info Otomatis (Read-Only)', {
            'fields': ('id', 'created_at', 'news_views'),
            'classes': ('collapse',) # Sembunyikan grup ini by default
        }),
    )