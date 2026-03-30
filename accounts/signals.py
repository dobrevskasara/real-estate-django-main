from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from accounts.models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        role = "ADMIN" if instance.is_superuser else "USER"
        Profile.objects.create(user=instance, role=role)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
