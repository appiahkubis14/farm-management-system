# utils/user_utils.py
from django.contrib.auth.models import Group
from backend.models import UserPosition, UserGroupPosition

def assign_user_to_position(user, position_name, is_active=True):
    """Assign a user to a position and sync groups"""
    try:
        position = UserPosition.objects.get(name=position_name)
        
        # Deactivate any existing active positions for this user
        UserGroupPosition.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # Create or update the user position
        user_position, created = UserGroupPosition.objects.get_or_create(
            user=user,
            position=position,
            defaults={'is_active': is_active}
        )
        
        if not created:
            user_position.is_active = is_active
            user_position.save()
        
        return user_position
        
    except UserPosition.DoesNotExist:
        raise ValueError(f"Position '{position_name}' does not exist")

def get_user_position(user):
    """Get the active position for a user"""
    try:
        return UserGroupPosition.objects.get(user=user, is_active=True)
    except UserGroupPosition.DoesNotExist:
        return None

def get_users_by_position(position_name):
    """Get all users with a specific position"""
    try:
        position = UserPosition.objects.get(name=position_name)
        return [ugp.user for ugp in UserGroupPosition.objects.filter(position=position, is_active=True)]
    except UserPosition.DoesNotExist:
        return []