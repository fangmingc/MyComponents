from django.contrib import admin
from . import models
# Register your models here.

admin.site.register(models.User)
admin.site.register(models.Role)
admin.site.register(models.Permission)
admin.site.register(models.PermissionGroup)
admin.site.register(models.Menu)
