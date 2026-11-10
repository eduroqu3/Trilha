from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "nome", "role", "escola", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Perfil TRILHA", {"fields": ("nome", "role", "escola")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Perfil TRILHA", {"fields": ("email", "nome", "role", "escola")}),)
    search_fields = ("email", "nome")
