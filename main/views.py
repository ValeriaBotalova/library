from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from core.models import *
from .forms import *


@login_required
def profile(request):
    active_loans = BookLoan.objects.filter(
        reader=request.user,
        return_date__isnull=True
    ).select_related('book', 'book__author').order_by('due_date')[:5]
    
    favorite_genres = set(loan.book.genre for loan in active_loans if loan.book.genre)
    

    recommended_books = Book.objects.filter(
        genre__in=favorite_genres,
        available_copies__gt=0
    ).exclude(
        id__in=[loan.book.id for loan in active_loans]
    ).order_by('?')[:2]  
    
    return render(request, 'profile.html', {
        'active_loans': active_loans,
        'recommended_books': recommended_books,
    })

@login_required
def guide(request):
    return render(request, 'guide.html')

@login_required
def my_loans(request):
    loans = BookLoan.objects.filter(reader=request.user).order_by('-loan_date')
    for loan in loans.filter(return_date__isnull=True):
        if loan.due_date < timezone.now().date():
            loan.status = LoanStatus.objects.get(status_name='overdue')
            loan.save()
    
    return render(request, 'loans.html', {'loans': loans})

@login_required
def my_fines(request):
    fines = Fine.objects.filter(loan__reader=request.user)
    return render(request, 'fines.html', {'fines': fines})

@login_required
def books(request):
    all_books = Book.objects.all()
    my_loans = BookLoan.objects.filter(reader=request.user, status__status_name='active')
    return render(request, 'books.html', {
        'books': all_books,
        'my_loans': my_loans
    })

def logout_view(request):
    logout(request)
    return render(request,'login.html')

def register_view(request):
    if request.method == 'POST':
        form = ReaderRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = ReaderRegistrationForm()
    return render(request, 'registration.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')
        return redirect('profile')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Перенаправление в зависимости от статуса пользователя
            if user.is_superuser:
                return redirect('/admin/')
            return redirect('profile')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def reserve_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        # Получаем или создаем статус "active"
        status, created = LoanStatus.objects.get_or_create(
            status_name='active',
            defaults={'status_name': 'active'}
        )
        
        # Проверяем доступность книги
        if book.available_copies <= 0:
            messages.error(request, "Эта книга сейчас недоступна")
            return redirect('books')
        
        # Создаем запись о бронировании
        BookLoan.objects.create(
            book=book,
            reader=request.user,
            due_date=timezone.now() + timezone.timedelta(days=14),
            status=status
        )
        
        # Обновляем количество доступных книг
        book.available_copies -= 1
        book.save()
        
        messages.success(request, "Книга успешно забронирована")
        return redirect('books')
    
    return redirect('books')

@login_required
def cancel_reservation(request, loan_id):
    loan = get_object_or_404(BookLoan, pk=loan_id, reader=request.user)
    book = loan.book

    book.available_copies += 1
    book.save()
    
    loan.delete()
    messages.success(request, "Бронирование отменено")
    return redirect('profile')

@login_required
def return_book(request, loan_id):
    loan = get_object_or_404(BookLoan, pk=loan_id, reader=request.user)
    
    if loan.return_date is not None:
        messages.warning(request, "Эта книга уже была возвращена")
        return redirect('my_loans')
    
    loan.return_book()
    messages.success(request, f"Книга '{loan.book.title}' успешно возвращена")
    return redirect('my_loans')