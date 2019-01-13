from exchangelib.errors import UnauthorizedError
from django import forms
from django.conf import settings
from django.db import transaction

from .models import ForwardEmail, User
from .owa_account import OwaAccount
from ..applications.models import ForwardType
from ..utils.cipher import Cipher


class LoginForm(forms.Form):
    SERVER_TYPE = (
        ('mail.remtiro.com', 'mail.remtiro.com'),
    )

    server = forms.ChoiceField(
        choices=SERVER_TYPE,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレス'}))
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザ名'}))
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'パスワード'}, render_value=True))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cipher = Cipher(settings.PERSONAL_CRYPTO_KEY)

    def clean(self):
        server = self.cleaned_data['server']
        email = self.cleaned_data['email']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']

        try:
            owa_account = OwaAccount(server=server, email=email, username=username, password=password)
        except UnauthorizedError:
            raise forms.ValidationError({
                'username': ['ユーザ名またはパスワードが間違っています'],
                'password': ['ユーザ名またはパスワードが間違っています'],
            }, code='invalid')

        if not owa_account.has_inbox():
            raise forms.ValidationError({'email': ['メールアドレスが間違っています']}, code='invalid')

        return self.cleaned_data

    def setReadonly(self):
        self.fields['server'].widget.attrs['readonly'] = 'readonly'
        self.fields['email'].widget.attrs['readonly'] = 'readonly'
        self.fields['username'].widget.attrs['readonly'] = 'readonly'
        self.fields['password'].widget.attrs['readonly'] = 'readonly'

    def get_user(self):
        try:
            email = self.cleaned_data['email'].lower()
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            return None

    @transaction.atomic
    def create_user(self):
        user = User.objects.create_user(
            server=self.cleaned_data['server'],
            email=self.cleaned_data['email'].lower(),
            username=self.cipher.encrypt(self.cleaned_data['username']),
            password=self.cipher.encrypt(self.cleaned_data['password'])
        )
        ForwardEmail.objects.create(user=user)
        ForwardType.objects.create(user=user)
        return user

    def update_user(self, user):
        user.password = self.cipher.encrypt(self.cleaned_data['password'])
        user.need_password_change = False
        user.save()
        return user


class EditEmailForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '転送先メールアドレス'}))


class AccountForm(forms.Form):
    server = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    email = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'readonly': 'readonly'}, render_value=True))
    forward_email = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
