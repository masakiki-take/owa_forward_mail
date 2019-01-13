import ast
import json

from django.conf import settings
from pytz import datetime

from ..accounts.models import ForwardEmail, User
from ..utils.cipher import Cipher
from ..utils.email import SendEmail
from ..utils.enum import MailAuthStatus


class EmailAuthenticate:
    class EmailAuthCompleted(Exception):
        pass

    class EmailAuthTokenExpired(Exception):
        pass

    def __init__(self, user, email):
        self.user = user
        self.email = email
        self.cipher = Cipher(settings.EMAIL_AUTH_CRYPTO_KEY)

    def _generate_token(self):
        info = {
            'timestamp': datetime.datetime.now().timestamp(),
            'email': self.user.email,
            'forward_email': self.email,
        }
        return self.cipher.encrypt(json.dumps(info))

    def is_valid_token(self, token):
        try:
            token_info = ast.literal_eval(self.cipher.decrypt(token))
        except Exception:
            return False

        if token_info.keys() != {'timestamp', 'email', 'forward_email'}:
            return False

        diff = (datetime.datetime.now() - datetime.datetime.fromtimestamp(token_info['timestamp'])).seconds
        if diff >= 24 * 60 * 60:
            raise self.EmailAuthTokenExpired

        try:
            user = User.objects.get(email=token_info['email'])
        except User.DoesNotExist:
            return False

        forward_email = ForwardEmail.objects.get(user=user)
        if not forward_email:
            return False

        if forward_email.mail_auth == MailAuthStatus.get_values('done'):
            raise self.EmailAuthCompleted

        return (
            user.email == token_info['email']
            and forward_email.email == token_info['forward_email']
        )

    def send_email_auth_done(self):
        title = '【OWAメール転送システム】転送先メールアドレスの認証が完了しました'
        template = 'email/email_auth_done.html'
        email = SendEmail(self.email, title, template)
        return email.send()

    def send_email_auth(self, confirm_url):
        token = self._generate_token()
        if not confirm_url.endswith('/'):
            confirm_url += '/'
        auth_url = f"{confirm_url}{token}/"
        extra_context = {'auth_url': auth_url}

        title = '【OWAメール転送システム】転送先メールアドレスのご確認'
        template = 'email/email_authenticate.html'

        email = SendEmail(self.email, title, template, extra_context)
        return email.send()
