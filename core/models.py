###############################################################################################################
#PERMISSIONS

from django.contrib.auth.models import Group, Permission
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.contrib.auth.models import Group
from enum import Enum
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType


from django.db import models

class SidebarMenu(models.Model):
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=255)
    url = models.URLField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    groups = models.ManyToManyField(Group, related_name='sidebar_menus', blank=True)
    menu_type = models.CharField(max_length=50, default="main")  # Set a default value here

    def __str__(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order"]

    @staticmethod
    def get_menu_for_user(user):
        """Get sidebar items based on user's group permissions."""
        user_groups = user.groups.all()
        allowed_menus = SidebarMenu.objects.filter(Q(groups__in=user_groups) | Q(groups__isnull=True))
        return allowed_menus


class Role(models.Model):
    """Role model representing a group with specific permissions."""
    name = models.CharField(max_length=50, unique=True)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='role')

    def __str__(self):
        return self.name


    def set_permissions(self, model_class, perm_list):
        """Assign permissions to the group for a specific model."""
        content_type = ContentType.objects.get_for_model(model_class)
        for codename in perm_list:
            permission, created = Permission.objects.get_or_create(
                content_type=content_type, codename=codename)
            self.group.permissions.add(permission)

    def add_permission(self, permission_codename):
        """Add a single permission to the group."""
        permission = Permission.objects.get(codename=permission_codename)
        self.group.permissions.add(permission)

    def remove_permission(self, permission_codename):
        """Remove a single permission from the group."""
        permission = Permission.objects.get(codename=permission_codename)
        self.group.permissions.remove(permission)



# from django.db import models
# from django.contrib.auth import get_user_model
# from django.utils import timezone
# import geoip2.database
# import user_agents

# User = get_user_model()

# class LoginHistoryData(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
#     timestamp = models.DateTimeField(default=timezone.now)
#     ip_address = models.GenericIPAddressField()
#     device_type = models.CharField(max_length=50, blank=True)
#     browser = models.CharField(max_length=100, blank=True)
#     os = models.CharField(max_length=100, blank=True)
#     location = models.CharField(max_length=255, blank=True)
#     latitude = models.FloatField(null=True, blank=True)
#     longitude = models.FloatField(null=True, blank=True)
#     status = models.CharField(max_length=10, choices=[('success', 'Success'), ('failed', 'Failed')])
#     reason = models.CharField(max_length=255, blank=True)

#     def __str__(self):
#         return f"{self.user} - {self.status} - {self.timestamp}"

#     @classmethod
#     def create_from_request(cls, request, user=None, status='success', reason=''):
#         """Factory method to create a login record from a request object"""
#         ua_string = request.META.get('HTTP_USER_AGENT', '')
#         user_agent = user_agents.parse(ua_string)
        
#         # Determine device type
#         if user_agent.is_mobile:
#             device_type = 'Mobile'
#         elif user_agent.is_tablet:
#             device_type = 'Tablet'
#         else:
#             device_type = 'Desktop'
        
#         # Get location data
#         location = ''
#         latitude = None
#         longitude = None
#         ip_address = cls._get_client_ip(request)
        
#         try:
#             with geoip2.database.Reader('GeoLite2-City.mmdb') as reader:
#                 response = reader.city(ip_address)
#                 location = f"{response.city.name}, {response.country.name}" if response.city.name else response.country.name
#                 latitude = response.location.latitude
#                 longitude = response.location.longitude
#         except:
#             pass
        
#         return cls.objects.create(
#             user=user,
#             ip_address=ip_address,
#             device_type=device_type,
#             browser=user_agent.browser.family,
#             os=user_agent.os.family,
#             location=location,
#             latitude=latitude,
#             longitude=longitude,
#             status=status,
#             reason=reason
#         )

#     @staticmethod
#     def _get_client_ip(request):
#         """Extract client IP from request"""
#         x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#         if x_forwarded_for:
#             ip = x_forwarded_for.split(',')[0]
#         else:
#             ip = request.META.get('REMOTE_ADDR')
#         return ip