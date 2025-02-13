from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from employees.models import Employee


@receiver(post_save, sender=User)
def create_employee_for_superuser(sender, instance, created, **kwargs):
    # Check if the user is a superuser and has no associated Employee
    if created and instance.is_superuser and not hasattr(instance, 'employee'):
        # Generate a company ID or use a default logic
        generated_company_id = f"ADMIN-{instance.id:04d}"  # Example company ID

        # Create a default Employee instance linked to the superuser
        Employee.objects.create(
            user=instance,
            company_id=generated_company_id,
            contact="N/A",  # Default value for fields
            middle_name="",  # Default value for fields
            gender="MALE",  # Default gender (or make this configurable)
        )
