from django.utils import timezone 
from django.db import models
from datetime import datetime
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.contrib.auth.base_user import BaseUserManager

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be provided')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class LoanStatus(models.Model):
    status_name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.status_name

class Author(models.Model):
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.full_name

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Reader(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField()
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    registration_date = models.DateField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'birth_date']

    objects = CustomUserManager()

    def __str__(self):
        return self.full_name


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True)
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    year_published = models.IntegerField(null=True, blank=True)
    total_copies = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    available_copies = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.title
    

class BookLoan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE)
    loan_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.ForeignKey(LoanStatus, on_delete=models.PROTECT, default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(return_date__isnull=True) | models.Q(return_date__gte=models.F('loan_date')),
                name='return_date_after_loan'
            )
        ]

    def __str__(self):
        return f"{self.book} loaned to {self.reader}"
    
    def return_book(self):
        """Метод для возврата книги"""
        self.return_date = timezone.now().date()
        self.status = LoanStatus.objects.get(status_name='returned')
        self.save()

        self.book.available_copies += 1
        self.book.save()

        BookHistory.objects.create(
            book=self.book,
            event_type='return',
            details=f"Книга возвращена читателем {self.reader.full_name}"
        )
    
    @property
    def is_overdue(self):
        """Проверяет, просрочена ли книга"""
        due_date = self.due_date
        if isinstance(due_date, datetime):
            due_date = due_date.date()
        if self.return_date is None and due_date < timezone.now().date():
            return True
        return False


    
    def save(self, *args, **kwargs):
        """Автоматически обновляет статус при сохранении"""
        if self.is_overdue and self.status.status_name != 'overdue':
            self.status = LoanStatus.objects.get(status_name='overdue')
        super().save(*args, **kwargs)

class Fine(models.Model):
    loan = models.ForeignKey(BookLoan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    issued_date = models.DateField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Fine #{self.id} - {self.amount}"

class BookHistory(models.Model):
    EVENT_CHOICES = [
        ('loan', 'Выдача'),
        ('return', 'Возврат'),
        ('lost', 'Потеря'),
        ('overdue', 'Просрочка')
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    event_date = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.book} - {self.get_event_type_display()}"

