from django.contrib import messages
from django.contrib.auth import login, logout, REDIRECT_FIELD_NAME
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import is_safe_url
from django.views.generic import TemplateView, View

from .auth import EmailAuthenticate
from .forms import AccountForm, EditEmailForm, LoginForm
from .models import ForwardEmail
from ..utils.constant import Constant
from ..utils.enum import MailAuthStatus


class LoginView(View):
    template_name = 'accounts/login.html'

    def get_redirect_url(self, request):
        redirect_to = request.POST.get(
            REDIRECT_FIELD_NAME,
            request.GET.get(REDIRECT_FIELD_NAME, '')
        )
        allowed_hosts = {request.get_host()}
        url_is_safe = is_safe_url(
            url=redirect_to,
            allowed_hosts=allowed_hosts,
            require_https=request.is_secure(),
        )
        return redirect_to if url_is_safe else ''

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        else:
            form = LoginForm()
            next = request.GET.get(REDIRECT_FIELD_NAME, '')
            context = {
                'form': form,
                'next': next,
            }
            return render(request, self.template_name, context)

    def post(self, request):
        signup = self.request.POST.get('is_signup')
        form = LoginForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        if signup:
            user = form.create_user()
        else:
            user = form.get_user()
            if not form.get_user():
                form.setReadonly()
                return render(request, self.template_name, {'form': form, 'is_signup': True})
            else:
                form.update_user(user)

        login(request, user)
        next_url = self.get_redirect_url(request)
        if next_url:
            return redirect(next_url)
        messages.success(request, 'ログインしました')
        return redirect('dashboard')


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        messages.success(request, 'ログアウトしました')
        return redirect('login')


class AccountView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        forward_email = ForwardEmail.objects.get(user=self.request.user)
        form = AccountForm({
            'server': self.request.user.server,
            'email': self.request.user.email,
            'username': self.request.user.plane_username,
            'password': self.request.user.plane_password,
            'forward_email': forward_email.email,
        })

        context.update({
            'current': 'account',
            'form': form,
            'mail_auth': forward_email.mail_auth,
            'constant': Constant,
        })
        return context


class EditEmailView(LoginRequiredMixin, View):
    template_name = 'accounts/edit_email.html'

    def get(self, request):
        form = EditEmailForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = EditEmailForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        confirm_url = (
            f'{request.scheme}://{request.get_host()}'
            f'{reverse("confirm_email", kwargs={"token": "dummy"})[:-6]}'
        )
        email_auth = EmailAuthenticate(request.user, form.cleaned_data['email'])
        if not email_auth.send_email_auth(confirm_url):
            messages.error(request, '認証メールの送信に失敗しました')
            return render(request, self.template_name, {'form': form})

        forward_email = ForwardEmail.objects.get(user=request.user)
        forward_email.email = form.cleaned_data['email']
        forward_email.mail_auth = MailAuthStatus.get_values('sent')
        forward_email.save()

        messages.success(request, '認証メールを送信しました')
        return redirect('dashboard')


class EmailConfirmationView(LoginRequiredMixin, View):
    def get(self, request, token):
        try:
            forward_email = ForwardEmail.objects.get(user=request.user)
            email_auth = EmailAuthenticate(request.user, forward_email.email)
            if email_auth.is_valid_token(token):
                if email_auth.send_email_auth_done():
                    forward_email.mail_auth = MailAuthStatus.get_values('done')
                    forward_email.save()
                    messages.success(request, 'メール認証が完了しました')
                else:
                    messages.error(request, 'メール認証が失敗しました。もう一度やり直してください')
            else:
                messages.error(request, 'メール認証が失敗しました。もう一度やり直してください')
        except EmailAuthenticate.EmailAuthTokenExpired:
            messages.error(request, 'メール認証の有効期限が過ぎています。もう一度やり直してください')
        except EmailAuthenticate.EmailAuthCompleted:
            messages.error(request, '既にメール認証が完了しています')
        except Exception:
            messages.error(request, 'メール認証が失敗しました。もう一度やり直してください')

        return redirect('dashboard')
