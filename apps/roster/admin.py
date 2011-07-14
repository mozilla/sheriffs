from django.contrib import admin
from django.conf import settings
from roster.models import Slot
from utils import get_user_name

class SlotAdmin(admin.ModelAdmin):  # pragma: no cover
    list_display = ('user_display', 'date_display')
    list_filter = ('user',)
    exclude = ('add_date',)

    def user_display(self, obj):
        return get_user_name(obj.user)
    user_display.short_description = "User"

    def date_display(self, obj):
        return obj.date.strftime(settings.DEFAULT_DATE_FORMAT)
    date_display.short_description = "Date"

admin.site.register(Slot, SlotAdmin)
