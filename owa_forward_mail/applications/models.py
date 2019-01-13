from django.db import models

from ..accounts.models import User
from ..mixins import CreateAndUpdateDateTimeMixin
from ..utils.enum import ForwardStatus, ForwardTarget


class ForwardType(CreateAndUpdateDateTimeMixin):
    """転送種別"""
    FORWARD_TARGET = tuple([x.value for x in ForwardTarget])

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    target = models.CharField(max_length=1, choices=FORWARD_TARGET, default=ForwardTarget.get_values('stop'))
    keep_unread = models.BooleanField(default=True)

    class Meta:
        db_table = 'forward_type'


class ForwardHistory(CreateAndUpdateDateTimeMixin):
    """転送履歴"""
    FORWARD_STATUS = tuple([x.value for x in ForwardStatus])

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=FORWARD_STATUS, default=ForwardStatus.get_values('init'))
    new_mail_count = models.IntegerField(default=0)
    message = models.TextField(default='')

    @property
    def status_display(self):
        if self.status == ForwardStatus.get_values('init'):
            return '未転送'
        elif self.status == ForwardStatus.get_values('valid'):
            if self.new_mail_count:
                return f'新着 {self.new_mail_count} 件'
            else:
                return '新着なし'
        elif self.status == ForwardStatus.get_values('auth_failure'):
            return '認証失敗'
        elif self.status == ForwardStatus.get_values('invalid'):
            return '転送失敗'

    class Meta:
        db_table = 'forward_history'
        ordering = ['-created_at']


class TaskStatus(CreateAndUpdateDateTimeMixin):
    """タスクステータス"""
    is_running = models.BooleanField(default=False)

    class Meta:
        db_table = 'task_status'
