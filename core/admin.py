from django.contrib import admin
from .models import (
    LoanStatus, 
    Author, 
    Genre, 
    Reader, 
    Book, 
    BookLoan, 
    Fine, 
    BookHistory
)

# Регистрация всех моделей
@admin.register(LoanStatus)
class LoanStatusAdmin(admin.ModelAdmin):
    list_display = ('status_name',)
    search_fields = ('status_name',)

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date', 'country')
    search_fields = ('full_name', 'country')
    list_filter = ('country',)

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'registration_date')
    search_fields = ('full_name', 'email')
    list_filter = ('registration_date',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'available_copies')
    search_fields = ('title', 'isbn')
    list_filter = ('genre', 'author')
    raw_id_fields = ('author', 'genre')

@admin.register(BookLoan)
class BookLoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'reader', 'loan_date', 'due_date', 'status')
    search_fields = ('book__title', 'reader__full_name')
    list_filter = ('status', 'loan_date')
    raw_id_fields = ('book', 'reader')

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount', 'issued_date', 'paid')
    search_fields = ('loan__book__title', 'loan__reader__full_name')
    list_filter = ('paid', 'issued_date')
    raw_id_fields = ('loan',)

@admin.register(BookHistory)
class BookHistoryAdmin(admin.ModelAdmin):
    list_display = ('book', 'event_type', 'event_date')
    search_fields = ('book__title',)
    list_filter = ('event_type', 'event_date')
    raw_id_fields = ('book',)