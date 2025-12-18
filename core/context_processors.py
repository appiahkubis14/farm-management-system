# context_processors.py
from django.contrib.auth.decorators import login_required
# from backend.models import UserGroupPosition
from utils import sidebar

def user_has_any_group(user_group_names, allowed_groups):
    """Check if user belongs to any of the allowed groups (case-insensitive)"""
    if not allowed_groups:
        return False  # Changed to False - now we require explicit group membership
    
    # Convert both sets to lowercase for case-insensitive comparison
    user_groups_lower = {group_name.lower() for group_name in user_group_names}
    allowed_groups_lower = {group_name.lower() for group_name in allowed_groups}
    
    return bool(user_groups_lower & allowed_groups_lower)

def filter_sidebar_level(items, user_group_names, user):
    filtered_items = {}
    
    print(f"DEBUG: User groups: {user_group_names}")
    print(f"DEBUG: Is admin: {'Admin' in user_group_names}")
    
    # Admin users see everything
    is_admin = 'Admin' in user_group_names
    if is_admin:
        print("DEBUG: Admin user - granting access to all items")
        return items
    
    for item_name, item_data in items.items():
        allowed_groups = item_data.get("groups", [])
        
        # Check if user has required groups
        has_group = user_has_any_group(user_group_names, allowed_groups)
        
        print(f"DEBUG: Item '{item_name}' - has_group: {has_group}")
        print(f"DEBUG:   Allowed groups: {allowed_groups}")
        
        # Only proceed if user has the required group access
        if not has_group:
            print(f"DEBUG:   SKIPPING '{item_name}' - access denied")
            continue
        
        print(f"DEBUG:   INCLUDING '{item_name}' - access granted")
        
        # Recursively filter nested sub-items if any
        sub_items = item_data.get("sub_items", {})
        filtered_sub_items = filter_sidebar_level(sub_items, user_group_names, user) if sub_items else {}

        # Create the item dictionary
        item_dict = {
            "icon": item_data.get("icon"),
        }
        
        if "url" in item_data:
            item_dict["url"] = item_data["url"]
        
        # Only include sub_items if they are not empty
        if filtered_sub_items:
            item_dict["sub_items"] = filtered_sub_items
        
        # Only add the item to filtered_items if it has content (url or valid sub_items)
        if "url" in item_dict or filtered_sub_items:
            filtered_items[item_name] = item_dict
    
    print(f"DEBUG: Filtered items: {list(filtered_items.keys())}")
    return filtered_items

def sidebar_context(request):
    if not request.user.is_authenticated:
        return {}

    user_groups = request.user.groups.all()
    user_group_names = set(user_groups.values_list('name', flat=True))

    filtered_sidebar_items = filter_sidebar_level(
        sidebar.Sidebar.sidebar_items,
        user_group_names,
        request.user
    )

    return {
        "sidebar_items": filtered_sidebar_items,
        "path": request.path,
        "current_user": request.user
    }