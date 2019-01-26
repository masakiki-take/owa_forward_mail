import traceback

from exchangelib.errors import UnauthorizedError
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from owa_forward_mail.accounts.models import ForwardEmail, User
from owa_forward_mail.accounts.owa_account import OwaAccount
from owa_forward_mail.applications.models import ForwardHistory, ForwardType
from owa_forward_mail.utils.email import SendEmail
from owa_forward_mail.utils.enum import ForwardTarget, ForwardStatus, MailAuthStatus
from owa_forward_mail.utils.slack import LogLevel, send_slack_message


class Command(BaseCommand):
    RETRY_COUNT = 3

    def _is_valid_account(self, user, forward_email):
        try:
            OwaAccount(
                server=user.server,
                email=user.email,
                username=user.plane_username,
                password=user.plane_password
            )
            return True
        except UnauthorizedError:
            send_slack_message(LogLevel.warning, user, '認証失敗 (1)', channel=True)

            ForwardHistory.objects.create(user=user, status=ForwardStatus.get_values('auth_failure'))
            user.need_password_change = True
            user.save()

            title = '【OWAメール転送システム】OWAのログインに失敗しました'
            template = 'email/authentication_error.html'
            email = SendEmail(forward_email.email, title, template)
            email.send()

            return False

    def _delete_old_histories(self, histories):
        delete_ids = [history.id for history in histories[99:]]
        ForwardHistory.objects.filter(id__in=delete_ids).delete()

    def _get_last_time(self, user):
        last_time = None

        histories = ForwardHistory.objects.filter(user=user).order_by('created_at')
        if histories:
            valid_history = histories.filter(user=user, status=ForwardStatus.get_values('valid'))
            if valid_history:
                last_time = valid_history.latest('created_at').created_at

            self._delete_old_histories(histories)

        return last_time

    def _owa_process(self, user, forward_type, forward_email):
        try:
            owa_account = OwaAccount(
                server=user.server,
                email=user.email,
                username=user.plane_username,
                password=user.plane_password,
                forward_email=forward_email.email,
                enableFaultTolerance=True
            )
            last_time = self._get_last_time(user)

            for i in range(self.RETRY_COUNT + 1):
                try:
                    if forward_type.target == ForwardTarget.get_values('count'):
                        count = owa_account.send_unread_mail_count(forward_type.keep_unread, last_time)
                    elif forward_type.target == ForwardTarget.get_values('subject'):
                        count = owa_account.send_unread_mail_subject(forward_type.keep_unread, last_time)
                    elif forward_type.target == ForwardTarget.get_values('mail'):
                        count = owa_account.forward_unread_mail(forward_type.keep_unread, last_time)
                    break
                except Exception:
                    if i < self.RETRY_COUNT:
                        send_slack_message(
                            LogLevel.warning, user, f'リトライ ({i + 1})', traceback.format_exc(), channel=True
                        )
                        continue
                    else:
                        raise
            if count:
                send_slack_message(LogLevel.info, user, f'`新着 {count} 件`')
            else:
                send_slack_message(LogLevel.info, user, '新着なし')

            ForwardHistory.objects.create(
                user=user,
                status=ForwardStatus.get_values('valid'),
                new_mail_count=count
            )
        except UnauthorizedError:
            send_slack_message(LogLevel.warning, user, '認証失敗 (2)', channel=True)

            ForwardHistory.objects.create(user=user, status=ForwardStatus.get_values('auth_failure'))
            user.need_password_change = True
            user.save()

            title = '【OWAメール転送システム】OWAのログインに失敗しました'
            template = 'email/authentication_error.html'
            email = SendEmail(forward_email.email, title, template)
            email.send()
        except Exception:
            send_slack_message(LogLevel.error, user, 'エラー発生', traceback.format_exc(), channel=True)

            forward_type.target = ForwardTarget.get_values('stop')
            forward_type.save()

            ForwardHistory.objects.create(user=user, status=ForwardStatus.get_values('invalid'))

            title = '【OWAメール転送システム】転送エラーが発生しました'
            template = 'email/critical_error.html'
            email = SendEmail(forward_email.email, title, template)
            email.send()

    def handle(self, *args, **options):
        try:
            now = timezone.localtime()
            if now.hour not in settings.OPERATING_HOURS:
                return

            send_slack_message(LogLevel.info, None, 'タスク開始')

            users = User.objects.filter(need_password_change=False, is_superuser=False)
            for user in users:
                forward_email = ForwardEmail.objects.get(user=user)
                forward_type = ForwardType.objects.get(user=user)

                if (
                    forward_email.mail_auth != MailAuthStatus.get_values('done')
                    or forward_type.target == ForwardTarget.get_values('stop')
                ):
                    reason = 'メール認証待ち' if forward_email.mail_auth != MailAuthStatus.get_values('done') else '配信停止中'
                    send_slack_message(LogLevel.warning, user, reason)
                    continue

                keep_unread = '残す' if forward_type.keep_unread else '残さない'
                send_slack_message(LogLevel.info, user, f'{forward_type.get_target_display()} / {keep_unread}')

                if self._is_valid_account(user, forward_email):
                    self._owa_process(user, forward_type, forward_email)

            send_slack_message(LogLevel.info, None, 'タスク終了')
        except Exception:
            send_slack_message(LogLevel.error, None, 'エラー発生', traceback.format_exc(), channel=True)
