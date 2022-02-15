# Generated by Django 3.2.11 on 2022-01-16 00:05
from django.db import migrations


# pylint: disable=unused-argument
def add_roles(apps, schema_editor):
    """
    Add the default roles for users

    :param apps:
    :type apps: ~django.apps.registry.Apps

    :param schema_editor: The database abstraction layer that creates actual SQL code
    :type schema_editor: ~django.db.backends.base.schema.BaseDatabaseSchemaEditor
    """
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    management_group = Group.objects.get(name="MANAGEMENT")
    delete_imprint_permission = Permission.objects.get(codename="delete_imprintpage")
    management_group.permissions.add(delete_imprint_permission)


# pylint: disable=unused-argument
def remove_roles(apps, schema_editor):
    """
    Remove the default roles for users

    :param apps: The
    :type apps: ~django.apps.registry.Apps

    :param schema_editor: The database abstraction layer that creates actual SQL code
    :type schema_editor: ~django.db.backends.base.schema.BaseDatabaseSchemaEditor
    """
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    management_group = Group.objects.get(name="MANAGEMENT")
    delete_imprint_permission = Permission.objects.get(codename="delete_imprintpage")
    management_group.permissions.remove(delete_imprint_permission)


class Migration(migrations.Migration):
    """
    Migration file to grant the imprint deletion permission to the management role
    """

    dependencies = [
        ("cms", "0004_alter_model_ordering"),
    ]

    operations = [
        migrations.RunPython(add_roles, remove_roles),
    ]
