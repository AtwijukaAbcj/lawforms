from django.db import migrations, models


def add_missing_divorceorder_softdelete_fields(apps, schema_editor):
    connection = schema_editor.connection
    table_name = connection.ops.quote_name('forms_divorceorder')

    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            cursor.execute('PRAGMA table_info(forms_divorceorder)')
            existing_columns = [row[1] for row in cursor.fetchall()]
        else:
            cursor.execute(
                'SELECT column_name FROM information_schema.columns WHERE table_name = %s',
                ['forms_divorceorder'],
            )
            existing_columns = [row[0] for row in cursor.fetchall()]

    if 'is_deleted' not in existing_columns:
        schema_editor.execute(
            f'ALTER TABLE {table_name} ADD COLUMN {connection.ops.quote_name("is_deleted")} boolean NOT NULL DEFAULT 0'
        )

    if 'deleted_at' not in existing_columns:
        schema_editor.execute(
            f'ALTER TABLE {table_name} ADD COLUMN {connection.ops.quote_name("deleted_at")} datetime NULL'
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0025_add_divorce_order'),
    ]

    operations = [
        migrations.RunPython(add_missing_divorceorder_softdelete_fields, reverse_code=noop_reverse),
    ]
