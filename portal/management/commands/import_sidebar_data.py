# management/commands/migrate_sidebar_hierarchy.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from portal.models import MenuItem

class Command(BaseCommand):
    help = 'Migrate existing sidebar data to new MenuItem hierarchy'
    
    def handle(self, *args, **options):
        # Clear existing data
        MenuItem.objects.all().delete()
        
        # Import from your sidebar.py
        from utils.sidebar import Sidebar
        
        order_counter = 0
        menu_items_map = {}  # Store created items for reference
        
        # First pass: Create all menu items
        for menu_name, menu_data in Sidebar.sidebar_items.items():
            order_counter += 10
            
            menu_item = MenuItem.objects.create(
                name=menu_name.lower().replace(' ', '_').replace('&', 'and'),
                display_name=menu_name,
                icon=menu_data.get('icon', ''),
                url=menu_data.get('url', ''),
                order=order_counter,
                is_active=True,
                parent=None  # Top level
            )
            
            # Add allowed groups
            for group_name in menu_data.get('groups', []):
                group, _ = Group.objects.get_or_create(name=group_name)
                menu_item.allowed_groups.add(group)
            
            menu_items_map[menu_name] = {'item': menu_item, 'data': menu_data}
        
        # Second pass: Create sub-items recursively
        def create_children(parent, sub_items_data, order_base=0):
            child_order = order_base
            for sub_name, sub_data in sub_items_data.items():
                child_order += 10
                
                child_item = MenuItem.objects.create(
                    name=sub_name.lower().replace(' ', '_').replace('&', 'and'),
                    display_name=sub_name,
                    icon=sub_data.get('icon', ''),
                    url=sub_data.get('url', ''),
                    order=child_order,
                    is_active=True,
                    parent=parent
                )
                
                # Add allowed groups
                for group_name in sub_data.get('groups', []):
                    group, _ = Group.objects.get_or_create(name=group_name)
                    child_item.allowed_groups.add(group)
                
                # Recursively create nested items
                if 'sub_items' in sub_data:
                    create_children(child_item, sub_data['sub_items'], child_order)
        
        # Create children for each top-level item
        for menu_name, menu_info in menu_items_map.items():
            menu_item = menu_info['item']
            menu_data = menu_info['data']
            
            if 'sub_items' in menu_data:
                create_children(menu_item, menu_data['sub_items'])
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully migrated {MenuItem.objects.count()} menu items'
        ))