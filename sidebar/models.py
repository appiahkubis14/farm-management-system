# # models.py
# from django.db import models
# from django.contrib.auth.models import Group
# from django.core.validators import MinValueValidator, MaxValueValidator

# class MenuItem(models.Model):
#     """Base model for sidebar menu items"""
#     name = models.CharField(max_length=100)
#     display_name = models.CharField(max_length=100)
#     icon = models.CharField(max_length=50, help_text="FontAwesome icon class (e.g., 'fas fa-chart-pie')")
#     url = models.CharField(max_length=200, blank=True, null=True, help_text="URL pattern (e.g., '/dashboard/')")
#     order = models.PositiveIntegerField(default=0, help_text="Display order")
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     # Permission groups that can see this item
#     allowed_groups = models.ManyToManyField(
#         Group, 
#         related_name='menu_items',
#         blank=True,
#         help_text="User groups that can access this menu item"
#     )
    
#     class Meta:
#         ordering = ['order', 'name']
#         verbose_name = "Menu Item"
#         verbose_name_plural = "Menu Items"
    
#     def __str__(self):
#         return self.display_name
    
#     @property
#     def has_submenu(self):
#         """Check if this item has sub-items"""
#         return self.sub_items.exists()


# class SubMenuItem(models.Model):
#     """Model for sub-menu items (second level)"""
#     parent = models.ForeignKey(
#         MenuItem, 
#         on_delete=models.CASCADE,
#         related_name='sub_items'
#     )
#     name = models.CharField(max_length=100)
#     display_name = models.CharField(max_length=100)
#     icon = models.CharField(max_length=50, help_text="FontAwesome icon class")
#     url = models.CharField(max_length=200, blank=True, null=True, help_text="URL pattern")
#     order = models.PositiveIntegerField(default=0, help_text="Display order")
#     is_active = models.BooleanField(default=True)
    
#     # Permission groups for this specific sub-item
#     allowed_groups = models.ManyToManyField(
#         Group, 
#         related_name='sub_menu_items',
#         blank=True,
#         help_text="User groups that can access this sub-menu item"
#     )
    
#     class Meta:
#         ordering = ['parent__order', 'order', 'name']
#         verbose_name = "Sub Menu Item"
#         verbose_name_plural = "Sub Menu Items"
    
#     def __str__(self):
#         return f"{self.parent.display_name} > {self.display_name}"
    
#     @property
#     def has_nested_items(self):
#         """Check if this sub-item has nested items (third level)"""
#         return self.nested_items.exists()


# class NestedMenuItem(models.Model):
#     """Model for nested menu items (third level)"""
#     parent = models.ForeignKey(
#         SubMenuItem, 
#         on_delete=models.CASCADE,
#         related_name='nested_items'
#     )
#     name = models.CharField(max_length=100)
#     display_name = models.CharField(max_length=100)
#     icon = models.CharField(max_length=50, help_text="FontAwesome icon class")
#     url = models.CharField(max_length=200, help_text="URL pattern")
#     order = models.PositiveIntegerField(default=0, help_text="Display order")
#     is_active = models.BooleanField(default=True)
    
#     # Permission groups for this specific nested item
#     allowed_groups = models.ManyToManyField(
#         Group, 
#         related_name='nested_menu_items',
#         blank=True,
#         help_text="User groups that can access this nested menu item"
#     )
    
#     class Meta:
#         ordering = ['parent__parent__order', 'parent__order', 'order', 'name']
#         verbose_name = "Nested Menu Item"
#         verbose_name_plural = "Nested Menu Items"
    
#     def __str__(self):
#         return f"{self.parent.parent.display_name} > {self.parent.display_name} > {self.display_name}"


# class SidebarConfiguration(models.Model):
#     """Configuration settings for the sidebar"""
#     name = models.CharField(max_length=100, default="Default Configuration")
#     is_active = models.BooleanField(default=True)
#     show_icons = models.BooleanField(default=True)
#     expand_all = models.BooleanField(default=False, help_text="Expand all menu items by default")
#     show_user_info = models.BooleanField(default=True, help_text="Show user info in sidebar")
#     show_search = models.BooleanField(default=False, help_text="Show search in sidebar")
#     theme = models.CharField(
#         max_length=20,
#         choices=[
#             ('light', 'Light'),
#             ('dark', 'Dark'),
#             ('auto', 'Auto (System)')
#         ],
#         default='light'
#     )
    
#     class Meta:
#         verbose_name = "Sidebar Configuration"
#         verbose_name_plural = "Sidebar Configurations"
    
#     def __str__(self):
#         return self.name
    
#     def save(self, *args, **kwargs):
#         # Ensure only one active configuration exists
#         if self.is_active:
#             SidebarConfiguration.objects.filter(is_active=True).update(is_active=False)
#         super().save(*args, **kwargs)