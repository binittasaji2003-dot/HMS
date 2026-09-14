import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
import django
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'employee_table' 
        ORDER BY ordinal_position;
    """)
    cols = cursor.fetchall()
    print("Columns in employee_table:")
    for c in cols:
        print(f"  {c[0]}: {c[1]} (nullable: {c[2]})")
