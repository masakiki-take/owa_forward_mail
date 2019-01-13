from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from ..mixins import CreateAndUpdateDateTimeMixin
from ..utils.cipher import Cipher
from ..utils.enum import MailAuthStatus


class UserAccountManager(BaseUserManager):
    def create_user(self, server, email, username, password):
        user = self.model(
            server=server,
            email=email,
            username=username,
            password=password
        )
        user.save()
        return user

    def create_superuser(self, email, password):
        user = self.create_user(
            server='',
            email=email,
            username='',
            password=password
        )
        user.is_superuser = True
        user.is_staff = True
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser, CreateAndUpdateDateTimeMixin, PermissionsMixin):
    """ユーザー"""
    USERNAME_FIELD = 'email'

    server = models.CharField(max_length=128)
    email = models.CharField(max_length=256, unique=True, db_index=True)
    username = models.CharField(max_length=256, unique=True)
    password = models.CharField(max_length=256)
    is_active = models.BooleanField(default=True)
    need_password_change = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserAccountManager()

    @property
    def plane_username(self):
        return Cipher(settings.PERSONAL_CRYPTO_KEY).decrypt(self.username)

    @property
    def plane_password(self):
        return Cipher(settings.PERSONAL_CRYPTO_KEY).decrypt(self.password)


class ForwardEmail(CreateAndUpdateDateTimeMixin):
    """転送先メールアドレス"""
    MAIL_Auth_STATUS = tuple([x.value for x in MailAuthStatus])

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.CharField(max_length=256)
    mail_auth = models.CharField(max_length=1, choices=MAIL_Auth_STATUS, default=MailAuthStatus.get_values('init'))

    class Meta:
        db_table = 'accounts_forward_email'
