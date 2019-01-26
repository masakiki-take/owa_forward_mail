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

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=FORWARD_STATUS, default=ForwardStatus.get_values('init'))
    new_mail_count = models.IntegerField(default=0)

    @property
    def status_display(self):
        if self.status == ForwardStatus.get_values('valid'):
            if self.new_mail_count:
                return f'新着 {self.new_mail_count} 件'
            else:
                return '新着なし'
        else:
            return self.get_status_display()

    class Meta:
        db_table = 'forward_history'
        ordering = ['-created_at']
