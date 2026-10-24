from django.db import migrations


def register_estate_accounting(apps, schema_editor):
    Module = apps.get_model("users", "Module")
    Permission = apps.get_model("users", "Permission")
    Role = apps.get_model("users", "Role")

    module, _ = Module.objects.get_or_create(
        code="estate_accounting",
        defaults={
            "name": "Estate Accounting",
            "description": "Create, manage, and print estate asset, receipt, expense, and distribution accounts",
            "icon": "📒",
        },
    )
    permissions = {
        permission_type: Permission.objects.get_or_create(
            module=module,
            permission_type=permission_type,
        )[0]
        for permission_type in ("view", "create", "edit", "delete", "print", "export")
    }

    role_permissions = {
        "Administrator": permissions.keys(),
        "Staff": ("view", "create", "edit", "print", "export"),
        "Viewer": ("view", "print"),
    }
    for role_name, permission_types in role_permissions.items():
        role = Role.objects.filter(name=role_name).first()
        if role:
            role.permissions.add(*(permissions[key] for key in permission_types))


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0036_alter_printevent_form_type"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            register_estate_accounting,
            migrations.RunPython.noop,
        ),
    ]
