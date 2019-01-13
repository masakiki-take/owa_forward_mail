from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import TemplateView, View

from ..accounts.auth import EmailAuthenticate
from ..accounts.models import ForwardEmail
from ..applications.models import ForwardHistory, ForwardType
from ..utils.constant import Constant
from ..utils.enum import ForwardTarget, MailAuthStatus


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            forward_type = ForwardType.objects.get(user=self.request.user)
        except ForwardType.DoesNotExist:
            forward_type = None

        forward_email = ForwardEmail.objects.get(user=self.request.user)
        forward_histories = ForwardHistory.objects.filter(user=self.request.user)[:100]

        context.update({
            'current': 'dashboard',
            'user': self.request.user,
            'forward_email': forward_email,
            'forward_type': forward_type,
            'forward_histories': forward_histories,
            'constant': Constant,
        })
        return context


class ResendEmailView(LoginRequiredMixin, View):
    def post(self, request):
        forward_email = ForwardEmail.objects.get(user=request.user)

        confirm_url = (
            f'{request.scheme}://{request.get_host()}'
            f'{reverse("confirm_email", kwargs={"token": "dummy"})[:-6]}'
        )
        email_auth = EmailAuthenticate(request.user, forward_email.email)
        if not email_auth.send_email_auth(confirm_url):
            messages.error(request, '認証メールの送信に失敗しました')
            return redirect('dashboard')

        messages.success(request, '認証メールを再送信しました')
        return redirect('dashboard')


class EditForwardTypeView(LoginRequiredMixin, View):
    template_name = 'dashboard/edit_forward_type.html'

    def get(self, request):
        forward_email = ForwardEmail.objects.get(user=request.user)
        if forward_email.mail_auth != MailAuthStatus.get_values('done'):
            return redirect('dashboard')

        try:
            forward_type = ForwardType.objects.get(user=request.user)
        except ForwardType.DoesNotExist:
            forward_type = None

        context = {
            'forward_type': forward_type,
            'constant': Constant,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        forward_type = ForwardType.objects.get(user=request.user)

        if 'stop' in request.POST:
            forward_type.target = ForwardTarget.get_values('stop')
            forward_type.save()

            messages.success(request, '配信を停止しました')
            return redirect('dashboard')
        else:
            target = request.POST.get('target')
            keep_unread = request.POST.get('keep_unread')
            if not target:
                context = {
                    'forward_type': forward_type,
                    'constant': Constant,
                    'errormessage': '転送対象を選択して下さい',
                }
                return render(request, self.template_name, context)

            forward_type.target = target
            forward_type.keep_unread = True if keep_unread else False
            forward_type.save()

            messages.success(request, '保存しました')
            return redirect('dashboard')
