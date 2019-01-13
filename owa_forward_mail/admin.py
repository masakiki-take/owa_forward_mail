from django.contrib import admin
from .accounts import models as accounts_models
from .applications import models as applications_models

admin.site.register(accounts_models.User)
admin.site.register(accounts_models.ForwardEmail)
admin.site.register(applications_models.ForwardType)
admin.site.register(applications_models.ForwardHistory)
admin.site.register(applications_models.TaskStatus)