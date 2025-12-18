
from django.contrib.auth.models import Permission
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.db.models.signals import post_delete

from backend.models import UserGroupPosition, UserPosition

# from employees.models import Employee
# models.py (continued)
@receiver(post_save, sender=UserPosition)
def create_position_group(sender, instance, created, **kwargs):
    """Create a Django group when a new position is created"""
    if created:
        instance.get_or_create_group()

@receiver(post_save, sender=UserGroupPosition)
def sync_user_position_to_group(sender, instance, created, **kwargs):
    """Sync user group membership when UserGroupPosition is saved"""
    instance.sync_user_groups()

@receiver(post_delete, sender=UserGroupPosition)
def remove_user_from_group(sender, instance, **kwargs):
    """Remove user from group when UserGroupPosition is deleted"""
    group_name = instance.position.get_group_name()
    try:
        group = Group.objects.get(name=group_name)
        instance.user.groups.remove(group)
    except Group.DoesNotExist:
        pass

# Also sync when Group is created to ensure positions exist
@receiver(post_save, sender=Group)
def sync_group_to_position(sender, instance, created, **kwargs):
    """Create a position when a new group with position name is created"""
    if created:
        # Check if group name matches any position display name
        position_map = {
            'District Officer': 'district_officer',
            'Port Officer': 'port_officer', 
            'Port Manager': 'port_manager',
            'Regional Manager': 'regional_manager',
            'Client': 'client',
            'Admin': 'admin'
        }
        
        if instance.name in position_map:
            position_name = position_map[instance.name]
            UserPosition.objects.get_or_create(
                name=position_name,
                defaults={'description': f'{instance.name} position'}
            )