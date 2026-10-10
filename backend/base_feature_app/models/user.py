from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADOPTER = 'adopter', 'Adopter'
        SHELTER_ADMIN = 'shelter_admin', 'Shelter Admin'
        VETERINARIAN = 'veterinarian', 'Veterinarian'
        WEB_MANAGER = 'web_manager', 'Web Manager'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100, blank=True)

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADOPTER)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    auth_version = models.PositiveIntegerField(default=0, editable=False)
    date_joined = models.DateTimeField(default=timezone.now)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    terms_version = models.CharField(max_length=20, blank=True, default='')
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Soft-archive: inactive account without deleting related rows.',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
