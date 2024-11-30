from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Users, Registrations, Results, TestSchedules

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('username',)

admin.site.register(Users, UserAdmin)

@admin.register(TestSchedules)
class TestAdmin(admin.ModelAdmin):
    list_display = ('Name', 'Psychologist', 'Description', 'Date', 'Location', 'Capacity')
    search_fields = ('Name', 'Psychologist')
    list_filter = ('Name', 'Psychologist')

@admin.register(Registrations)
class RegisAdmin(admin.ModelAdmin):
    list_display = ('User', 'TestSchedule__Name', 'ParticipantNumber', 'TestSchedule__Date', 'Status')
    search_fields = ('User__username',)
    list_filter = ('Status', 'TestSchedule__Date', 'User__username')
    
@admin.register(Results)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('Registration', 'Recommendation', 'ResultNumber', 'Date')
    search_fields = ('Registration__User__username', 'Registration__TestSchedule__Psychologist__username', 'Summary', 'ResultNumber')
    list_filter = ('Recommendation', 'Summary', 'Date')