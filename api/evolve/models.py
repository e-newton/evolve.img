import os
from django.db import models
from PIL import Image
from evolve_objects import EvolveObject
from django.utils.translation import gettext_lazy as _

# Create your models here.


class EvolveRequest(models.Model):

    class ObjectSelection(models.TextChoices):
        RECTANGLE = EvolveObject.RECTANGLE, _('Rectangle')
        CIRCLE = EvolveObject.CIRCLE, _('Circle')
        EMOJI = EvolveObject.EMOJI, _('Emoji')

    id = models.CharField(primary_key=True, max_length=32)
    image = models.ImageField()
    object = models.CharField(max_length=120, choices=ObjectSelection.choices, default=ObjectSelection.RECTANGLE)
    finished_generating = models.DateTimeField(null=True, blank=True)
    evolved_image = models.ImageField(null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None) -> None:
        super().save(force_insert, force_update, using, update_fields)
        if not self.image.name:
            raise Exception('Image name not found')
        print('image size', Image.open(self.image.path).size)

    def delete(self, using=None, keep_parents=False):
        if self.image and self.image.path and os.path.exists(self.image.path):
            os.remove(self.image.path)
        if self.evolved_image and self.evolved_image.path and os.path.exists(self.evolved_image.path):
            os.remove(self.evolved_image.path)
        return super().delete(using, keep_parents)


