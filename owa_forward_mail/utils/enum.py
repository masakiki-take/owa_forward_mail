from enum import Enum

from .constant import Constant


class MailAuthStatus(Enum):
    init = (Constant.MAIL_AUTH_STATUS_INIT, '初期状態')
    sent = (Constant.MAIL_AUTH_STATUS_SENT, '送信済み')
    done = (Constant.MAIL_AUTH_STATUS_DONE, '認証済み')

    @classmethod
    def get_values(cls, member):
        return cls[member].value[0]


class ForwardTarget(Enum):
    stop = (Constant.FORWARD_TARGET_STOP, '配信停止')
    count = (Constant.FORWARD_TARGET_COUNT, '件数')
    subject = (Constant.FORWARD_TARGET_SUBJECT, '差出人と件名')
    mail = (Constant.FORWARD_TARGET_MAIL, '全文')

    @classmethod
    def get_values(cls, member):
        return cls[member].value[0]


class ForwardStatus(Enum):
    init = (Constant.FORWARD_STATUS_INIT, '未転送')
    valid = (Constant.FORWARD_STATUS_VALID, '正常終了')
    auth_failure = (Constant.FORWARD_STATUS_AUTH_FAILURE, '認証失敗')
    invalid = (Constant.FORWARD_STATUS_INVALID, '転送失敗')

    @classmethod
    def get_values(cls, member):
        return cls[member].value[0]
