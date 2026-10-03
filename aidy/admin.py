from django.contrib import admin
from .models import AidyConversation, AidySupportTicket, AidyMessage

# Register your models here.
admin.site.register(AidyConversation)
admin.site.register(AidySupportTicket)
admin.site.register(AidyMessage)
