"""Create the legacy employee table without assuming Django's default user model."""

from django.conf import settings
from django.db import migrations


def create_employee_table(apps, schema_editor):
    user_app, user_model_name = settings.AUTH_USER_MODEL.split(".", 1)
    user_model = apps.get_model(user_app, user_model_name)
    connection = schema_editor.connection
    quote = connection.ops.quote_name
    user_table = quote(user_model._meta.db_table)
    user_pk_type = user_model._meta.pk.db_type(connection)

    schema_editor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS employee_table (
            employee_id BIGSERIAL PRIMARY KEY,
            candidate_id BIGINT REFERENCES candidate(candidate_id) ON DELETE SET NULL,
            user_id {user_pk_type} REFERENCES {user_table}({quote(user_model._meta.pk.column)}) ON DELETE CASCADE,
            employee_code VARCHAR(50) UNIQUE NOT NULL,
            department_id BIGINT REFERENCES department(department_id) ON DELETE SET NULL,
            designation VARCHAR(150) NOT NULL,
            joining_date DATE NOT NULL,
            employment_status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
            created_by {user_pk_type} REFERENCES {user_table}({quote(user_model._meta.pk.column)}) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_employee_candidate_id ON employee_table(candidate_id);
        CREATE INDEX IF NOT EXISTS idx_employee_user_id ON employee_table(user_id);
        CREATE INDEX IF NOT EXISTS idx_employee_code ON employee_table(employee_code);
        """
    )


def drop_employee_table(apps, schema_editor):
    schema_editor.execute("DROP TABLE IF EXISTS employee_table CASCADE;")


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('candidates', '0004_aptitudetest_assigned_candidates_aptitudetest_status_and_more'),
    ]

    operations = [
        migrations.RunPython(create_employee_table, reverse_code=drop_employee_table),
    ]
