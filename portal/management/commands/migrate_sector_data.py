from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from portal.models import SectorModel
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate data from Sector Boundary table to portal_sectormodel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without saving to database',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if records exist',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Table name with space - needs to be quoted
        table_name = '"Sector Boundary"'
        
        self.stdout.write(self.style.SUCCESS(f'Starting sector data migration from table: {table_name}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('*** DRY RUN MODE - No changes will be saved ***'))
        
        # Perform migration
        stats = self.migrate_data(table_name, dry_run, force)
        
        # Print summary
        self.print_summary(stats, dry_run)
    
    @transaction.atomic
    def migrate_data(self, table_name, dry_run=False, force=False):
        """Perform the actual data migration using raw SQL"""
        
        stats = {
            'total': 0,
            'migrated': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }
        
        # Use a savepoint for dry run
        sid = None
        if dry_run:
            sid = transaction.savepoint()
        
        try:
            with connection.cursor() as cursor:
                # First, get total count - note the quoted table name
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                stats['total'] = cursor.fetchone()[0]
                
                # Get all records from source table with actual column names from screenshot
                cursor.execute(f"""
                    SELECT 
                        id,
                        "sector" as sector_name,  -- This is the sector name field
                        "size_Ha",
                        "mean_pH",
                        "mean_OC",
                        "Texture_co",
                        geom
                    FROM {table_name}
                """)
                
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                for row in rows:
                    try:
                        # Convert row to dictionary
                        record = dict(zip(columns, row))
                        
                        # Check if record exists (by sector name)
                        if not force:
                            exists = SectorModel.objects.filter(
                                sector=record.get('sector_name')
                            ).exists()
                            
                            if exists:
                                self.stdout.write(f"Record '{record.get('sector_name')}' already exists, skipping")
                                stats['skipped'] += 1
                                continue
                        
                        # Create new SectorModel record with proper field mapping
                        dest = SectorModel(
                            sector=record.get('sector_name'),  # Maps to 'sector' field
                            size_Ha=record.get('size_Ha'),
                            mean_pH=record.get('mean_pH'),
                            mean_OC=record.get('mean_OC'),
                            Texture_co=str(record.get('Texture_co')) if record.get('Texture_co') else None,  # Convert int to string
                            geom=record.get('geom')
                            # created_by and modified_by will be NULL initially
                        )
                        
                        # Save if not dry run
                        if not dry_run:
                            dest.save()
                            self.stdout.write(f"✓ Migrated sector: {dest.sector}")
                        else:
                            self.stdout.write(f"[DRY RUN] Would migrate sector: {record.get('sector_name')}")
                        
                        stats['migrated'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error migrating record {record.get('sector_name', 'Unknown')}: {str(e)}"
                        self.stdout.write(self.style.ERROR(f"✗ {error_msg}"))
                        stats['errors'] += 1
                        stats['error_details'].append(error_msg)
            
            # Rollback if dry run
            if dry_run and sid:
                transaction.savepoint_rollback(sid)
                self.stdout.write(self.style.WARNING("Dry run completed - no changes saved"))
            
        except Exception as e:
            if dry_run and sid:
                transaction.savepoint_rollback(sid)
            raise CommandError(f"Migration failed: {str(e)}")
        
        return stats
    
    def print_summary(self, stats, dry_run):
        """Print migration summary"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("MIGRATION SUMMARY"))
        self.stdout.write("="*50)
        self.stdout.write(f"Total records processed: {stats['total']}")
        self.stdout.write(f"Successfully migrated: {stats['migrated']}")
        self.stdout.write(f"Skipped (already exist): {stats['skipped']}")
        self.stdout.write(f"Errors: {stats['errors']}")
        
        if stats['error_details']:
            self.stdout.write("\n" + self.style.ERROR("ERROR DETAILS:"))
            for error in stats['error_details'][:10]:
                self.stdout.write(self.style.ERROR(f"  • {error}"))
        
        self.stdout.write("="*50)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("This was a DRY RUN - no changes were saved"))
            self.stdout.write(self.style.WARNING("Run without --dry-run to actually migrate data"))