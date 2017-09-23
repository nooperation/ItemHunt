from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import *

admin.site.register(Hunt)
admin.site.register(Region)
admin.site.register(Player)
admin.site.register(Item)
admin.site.register(Transaction)
