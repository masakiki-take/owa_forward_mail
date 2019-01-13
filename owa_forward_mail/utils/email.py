from django.core.mail import EmailMultiAlternatives
from django.template import loader


class SendEmail:
    def __init__(self, to_email, title, template, extra_context=None):
        context = {'to_email': to_email}
        if extra_context:
            context.update(extra_context)
        body = loader.render_to_string(template, context=context)
        from_email = 'OWAメール転送システム <noreply@owa_forward_mail.com>'
        self.email = EmailMultiAlternatives(subject=title, body=body, from_email=from_email, to=[to_email])

    def send(self):
        return self.email.send()
