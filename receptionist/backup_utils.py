import os
import sys
from datetime import datetime
from django.conf import settings
from django.core.management import call_command

BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)


def create_database_backup():
    """
    Generate a timestamped JSON / SQL database backup of the HMS database.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"hms_backup_{timestamp}.json"
    backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

    try:
        with open(backup_filepath, 'w', encoding='utf-8') as f:
            call_command(
                'dumpdata',
                exclude=['contenttypes', 'auth.permission', 'sessions'],
                stdout=f,
                indent=2
            )
        return {
            'status': 'success',
            'filename': backup_filename,
            'filepath': backup_filepath,
            'timestamp': timestamp,
            'size_bytes': os.path.getsize(backup_filepath)
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def restore_database_backup(backup_filepath):
    """
    Restore HMS database from a given JSON backup file.
    """
    if not os.path.exists(backup_filepath):
        return {'status': 'error', 'error': 'Backup file does not exist.'}

    try:
        call_command('loaddata', backup_filepath)
        return {'status': 'success', 'filepath': backup_filepath}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
