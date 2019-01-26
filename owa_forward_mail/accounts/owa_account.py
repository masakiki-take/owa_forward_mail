import pytz

from django.template import loader
from exchangelib import (
    Account,
    Configuration,
    Credentials,
    DELEGATE,
    EWSDateTime,
    Message,
    ServiceAccount
)
from exchangelib.items import BaseMeetingItem
from exchangelib.errors import ErrorItemNotFound, ErrorNonExistentMailbox


class OwaAccount():
    WEEKS = ["月", "火", "水", "木", "金", "土", "日"]

    def __init__(self, email, server, username, password, forward_email=None, enableFaultTolerance=False):
        if enableFaultTolerance:
            credentials = ServiceAccount(
                username=username,
                password=password
            )
        else:
            credentials = Credentials(
                username=username,
                password=password
            )

        self.account = Account(
            primary_smtp_address=email,
            config=Configuration(
                server=server,
                credentials=credentials,
            ),
            autodiscover=False,
            access_type=DELEGATE,
        )
        self.forward_email = forward_email

    def _get_unread_mail_ids(self, last_time):
        """未読メールIDを取得

        Args:
            last_time(DateTime): 前回実行日時 (UTC)
                未指定の場合は、全ての未読メールを取得
        Returns:
            list(str): 受信トレイおよびサブフォルダの未読メール識別ID (Message.id)
        """
        unread_inbox = self.account.inbox.filter(is_read=False)
        unread_subfolder = self.account.inbox.walk().filter(is_read=False)
        if last_time:
            ews_last_time = EWSDateTime.from_datetime(last_time)
            unread_inbox = unread_inbox.filter(datetime_received__gt=ews_last_time)
            unread_subfolder = unread_subfolder.filter(datetime_received__gt=ews_last_time)

        return [mail.id for mail in unread_inbox] + [mail.id for mail in unread_subfolder]

    def _get_mail_infos(self, mails):
        """メール情報を取得

        Messageオブジェクトを扱いやすい最低限の情報にして返却

        Args:
            mails(list(Message)): Messageオブジェクトリスト
        Returns:
            list(dict): メール情報リスト
        """
        mail_infos = []
        for mail in mails:
            if mail.author.name == mail.author.email_address:
                author = mail.author.email_address
            else:
                author = f'{mail.author.name} <{mail.author.email_address}>'

            received_at = mail.datetime_received.astimezone(pytz.timezone('Asia/Tokyo'))
            received_at_str = received_at.strftime('%Y/%m/%d %H:%M:%S')
            received_at_str = received_at_str.replace(' ', f'({self.WEEKS[received_at.weekday()]}) ')

            mail_infos.append({
                'id': mail.id,
                'received_at': received_at_str,
                'from': author,
                'subject': mail.subject
            })

        return mail_infos

    def _get_unread_mail_infos(self, last_time):
        """未読メール情報を取得

        Args:
            last_time(DateTime): 前回実行日時 (UTC)
                未指定の場合は、全ての未読メールを取得
        Returns:
            list(dict): 受信トレイおよびサブフォルダの未読メール情報
        """
        inbox_mails = self.account.inbox.filter(is_read=False)
        subfolder_mails = self.account.inbox.walk().filter(is_read=False)
        if last_time:
            ews_last_time = EWSDateTime.from_datetime(last_time)
            inbox_mails = inbox_mails.filter(datetime_received__gt=ews_last_time)
            subfolder_mails = subfolder_mails.filter(datetime_received__gt=ews_last_time)

        return self._get_mail_infos(inbox_mails) + self._get_mail_infos(subfolder_mails)

    def _forward_mail(self, mail_id):
        """メールを転送

        Args:
            mail_id(str): メール識別ID (Message.id)
        """

        mail = self.account.inbox.get(id=mail_id)
        if isinstance(mail, Message):
            mail.forward(
                subject=f'【OWAメール転送システム】Fwd: {mail.subject}',
                body='このメールはシステムにより自動転送されたものです。',
                to_recipients=[self.forward_email]
            )
        elif isinstance(mail, BaseMeetingItem):
            received_at = mail.datetime_received.astimezone(pytz.timezone('Asia/Tokyo'))
            received_at_str = received_at.strftime('%Y/%m/%d %H:%M:%S')
            received_at_str = received_at_str.replace(' ', f'({self.WEEKS[received_at.weekday()]}) ')

            self._send_email(
                subject='【OWAメール転送システム】新着メール通知 (ミーティング)',
                template='email/unread_mail.html',
                extra_context={
                    'count': 1,
                    'mail_infos': [{
                        'received_at': received_at_str,
                        'from': mail.author,
                        'subject': mail.subject,
                    }],
                }
            )

    def _set_read_flag(self, mail_id, value):
        """未読フラグを設定

        Args:
            mail_id(str): メール識別ID (Message.id)
            value(bool): True (開封済み) / False (未開封)
        """
        mail = self.account.inbox.get(id=mail_id)
        mail.is_read = value
        mail.save()

    def _send_email(self, subject, template, extra_context=None):
        """メールを送信

        Args:
            subject(str): 件名
            template(str): テンプレートファイル名
            extra_context(dict): 追加コンテクスト
        """
        context = {'to_email': self.forward_email}
        if extra_context:
            context.update(extra_context)
        body = loader.render_to_string(template, context=context)

        try:
            mail = Message(
                account=self.account,
                subject=subject,
                body=body,
                to_recipients=[self.forward_email]
            )
            mail.send()
        except Exception:
            import traceback
            print(traceback.format_exc())

    def has_inbox(self):
        """受信ボックスが存在するか
        """
        try:
            return True if self.account.inbox else False
        except (ErrorItemNotFound, ErrorNonExistentMailbox):
            return False

    def send_unread_mail_count(self, keep_unread, last_time):
        """未読メールの件数を送信

        Args:
            keep_unread(bool): 未読フラグを残すか
            last_time(DateTime): 前回実行日時 (UTC)
        Returns:
            int: 未読メール件数
        """
        mail_ids = self._get_unread_mail_ids(last_time)
        if not mail_ids:
            return 0

        self._send_email(
            subject='【OWAメール転送システム】新着メール通知',
            template='email/unread_mail.html',
            extra_context={'count': len(mail_ids)}
        )

        if not keep_unread:
            for mail_id in mail_ids:
                self._set_read_flag(mail_id, True)

        return len(mail_ids)

    def send_unread_mail_subject(self, keep_unread, last_time):
        """未読メールの差出人と件名を送信

        Args:
            keep_unread(bool): 未読フラグを残すか
            last_time(DateTime): 前回実行日時 (UTC)
        Returns:
            int: 未読メール件数
        """
        mail_infos = self._get_unread_mail_infos(last_time)
        if not mail_infos:
            return 0

        self._send_email(
            subject='【OWAメール転送システム】新着メール通知',
            template='email/unread_mail.html',
            extra_context={
                'count': len(mail_infos),
                'mail_infos': mail_infos,
            }
        )

        if not keep_unread:
            for mail_id in [mail_info['id'] for mail_info in mail_infos]:
                self._set_read_flag(mail_id, True)

        return len(mail_infos)

    def forward_unread_mail(self, keep_unread, last_time):
        """未読メールを転送

        Args:
            keep_unread(bool): 未読フラグを残すか
            last_time(DateTime): 前回実行日時 (UTC)
        Returns:
            int: 未読メール件数
        """
        mail_ids = self._get_unread_mail_ids(last_time)
        if not mail_ids:
            return 0

        for mail_id in mail_ids:
            self._forward_mail(mail_id)
            if keep_unread:
                # OWAから転送すると自動で開封済みになるため、転送後未開封に設定
                self._set_read_flag(mail_id, False)
            else:
                # 会議招待メールは転送できないため、手動で開封済みに設定
                self._set_read_flag(mail_id, True)

        return len(mail_ids)
