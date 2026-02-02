# # admin.py
# from django.contrib import admin
# from django import forms
# from .models import MenuItem, SubMenuItem, NestedMenuItem, SidebarConfiguration

# class SubMenuItemInline(admin.TabularInline):
#     model = SubMenuItem
#     extra = 1
#     filter_horizontal = ('allowed_groups',)
#     fields = ('display_name', 'icon', 'url', 'order', 'is_active', 'allowed_groups')

# class NestedMenuItemInline(admin.TabularInline):
#     model = NestedMenuItem
#     extra = 1
#     filter_horizontal = ('allowed_groups',)
#     fields = ('display_name', 'icon', 'url', 'order', 'is_active', 'allowed_groups')

# @admin.register(MenuItem)
# class MenuItemAdmin(admin.ModelAdmin):
#     list_display = ('display_name', 'icon', 'order', 'is_active', 'has_submenu', 'created_at')
#     list_filter = ('is_active', 'allowed_groups')
#     search_fields = ('display_name', 'name', 'url')
#     filter_horizontal = ('allowed_groups',)
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('name', 'display_name', 'icon', 'url', 'order', 'is_active')
#         }),
#         ('Permissions', {
#             'fields': ('allowed_groups',)
#         }),
#     )
#     inlines = [SubMenuItemInline]
#     actions = ['activate_items', 'deactivate_items']
    
#     def activate_items(self, request, queryset):
#         queryset.update(is_active=True)
#     activate_items.short_description = "Activate selected items"
    
#     def deactivate_items(self, request, queryset):
#         queryset.update(is_active=False)
#     deactivate_items.short_description = "Deactivate selected items"

# @admin.register(SubMenuItem)
# class SubMenuItemAdmin(admin.ModelAdmin):
#     list_display = ('display_name', 'parent', 'icon', 'order', 'is_active', 'has_nested_items')
#     list_filter = ('is_active', 'parent', 'allowed_groups')
#     search_fields = ('display_name', 'name', 'url')
#     filter_horizontal = ('allowed_groups',)
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('parent', 'name', 'display_name', 'icon', 'url', 'order', 'is_active')
#         }),
#         ('Permissions', {
#             'fields': ('allowed_groups',)
#         }),
#     )
#     inlines = [NestedMenuItemInline]
#     actions = ['activate_items', 'deactivate_items']

# @admin.register(NestedMenuItem)
# class NestedMenuItemAdmin(admin.ModelAdmin):
#     list_display = ('display_name', 'parent', 'icon', 'order', 'is_active')
#     list_filter = ('is_active', 'parent', 'allowed_groups')
#     search_fields = ('display_name', 'name', 'url')
#     filter_horizontal = ('allowed_groups',)
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('parent', 'name', 'display_name', 'icon', 'url', 'order', 'is_active')
#         }),
#         ('Permissions', {
#             'fields': ('allowed_groups',)
#         }),
#     )
#     actions = ['activate_items', 'deactivate_items']

# @admin.register(SidebarConfiguration)
# class SidebarConfigurationAdmin(admin.ModelAdmin):
#     list_display = ('name', 'is_active', 'theme', 'show_icons', 'expand_all')
#     list_editable = ('is_active',)
#     fieldsets = (
#         ('General Settings', {
#             'fields': ('name', 'is_active', 'theme')
#         }),
#         ('Display Options', {
#             'fields': ('show_icons', 'expand_all', 'show_user_info', 'show_search')
#         }),
#     )
    
#     def has_delete_permission(self, request, obj=None):
#         # Prevent deletion if it's the only active configuration
#         if obj and obj.is_active:
#             return False
#         return super().has_delete_permission(request, obj)