from django.utils import timezone
from django_slack import slack_message


class LogLevel():
    info = 'INFO'
    warning = 'WARNING'
    error = 'ERROR'


def send_slack_message(level, user, title, extra_message=None, channel=False):
    slack_message('slack/message.slack', {
        'now': timezone.localtime().strftime("%H:%M:%S"),
        'level': level,
        'user': user,
        'title': title,
        'extra_message': extra_message,
        'channel': channel,
    })
