import traceback

from exchangelib.errors import UnauthorizedError
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TaskStatus
from ..accounts.models import ForwardEmail, User
from ..accounts.owa_account import OwaAccount
from ..applications.models import ForwardHistory, ForwardType
from ..utils.email import SendEmail
from ..utils.enum import ForwardTarget, ForwardStatus, MailAuthStatus


class RunTaskView(APIView):
    permission_classes = (AllowAny,)

    def _is_busy(self):
        task_status, created = TaskStatus.objects.get_or_create()
        return task_status.is_running

    def _start(self):
        task_status = TaskStatus.objects.all().latest('updated_at')
        task_status.is_running = True
        task_status.save()

    def _end(self):
        task_status = TaskStatus.objects.all().latest('updated_at')
        task_status.is_running = False
        task_status.save()

    def get(self, request, auth_key):
        if auth_key != settings.TASK_EXE_AUTH_KEY:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if self._is_busy():
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            self._start()

        users = User.objects.filter(need_password_change=False, is_superuser=False)
        for user in users:
            forward_email = ForwardEmail.objects.get(user=user)
            forward_type = ForwardType.objects.get(user=user)
            if (
                forward_email.mail_auth != MailAuthStatus.get_values('done')
                or forward_type.target == ForwardTarget.get_values('stop')
            ):
                continue

            histories = ForwardHistory.objects.filter(user=user)
            if histories:
                delete_ids = [history.id for history in histories[99:]]
                ForwardHistory.objects.filter(id__in=delete_ids).delete()
                last_time = (
                    ForwardHistory.objects
                                  .filter(user=user, status=ForwardStatus.get_values('valid'))
                                  .latest('created_at').created_at
                )
            else:
                last_time = None

            try:
                owa_account = OwaAccount(
                    server=user.server,
                    email=user.email,
                    username=user.plane_username,
                    password=user.plane_password,
                    forward_email=forward_email.email
                )
            except UnauthorizedError:
                ForwardHistory.objects.create(user=user, status=ForwardStatus.get_values('auth_failure'))
                user.need_password_change = True
                user.save()

                title = '【OWAメール転送システム】OWAのログインに失敗しました'
                template = 'email/authentication_error.html'
                email = SendEmail(forward_email.email, title, template)
                email.send()
                continue

            try:
                if forward_type.target == ForwardTarget.get_values('count'):
                    count = owa_account.send_unread_mail_count(forward_type.keep_unread, last_time)
                elif forward_type.target == ForwardTarget.get_values('subject'):
                    count = owa_account.send_unread_mail_subject(forward_type.keep_unread, last_time)
                elif forward_type.target == ForwardTarget.get_values('mail'):
                    count = owa_account.forward_unread_mail(forward_type.keep_unread, last_time)
                else:
                    continue

                ForwardHistory.objects.create(
                    user=user,
                    status=ForwardStatus.get_values('valid'),
                    new_mail_count=count
                )
            except Exception:
                ForwardHistory.objects.create(
                    user=user,
                    status=ForwardStatus.get_values('invalid'),
                    message=traceback.format_exc(),
                )
                continue

        self._end()
        return Response(status=status.HTTP_200_OK)
