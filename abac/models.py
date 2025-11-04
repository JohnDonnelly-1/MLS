from django.db import models
from django.conf import settings
from crum import get_current_user
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.
#User = settings.AUTH_USER_MODEL

# Create your models here.

### REFERENCES ###
#https://docs.djangoproject.com/en/4.0/topics/db/models/

'''
class DefaultModel(models.Model):
    name = models.CharField(max_length=55)

    def __str__(self):
        return self.name  #needs to be a string

    def get_absolute_url(self):
        return reverse("$URL_NAME_SPACE:$NAME", kwargs={"pk": self.pk})
'''

class Label(models.Model):
    class LabelType(models.TextChoices):
        LEVEL = "LVL", "Level"
        CATEGORY = "CAT", "Category" 

    short_code = models.CharField(max_length=3)
    name = models.CharField(max_length=50)
    label_type = models.CharField(max_length=3, choices=LabelType.choices, default=LabelType.CATEGORY )

    def __str__(self):
        return self.name


class Security(models.Model):
    securities = models.ManyToManyField(Label, null=True, related_name="labels")

    def __str__(self) -> str:
        return ", ".join(str(short_code) for short_code in self.securities.filter(label_type="CAT"))

    class Meta:
        verbose_name_plural = "securities"
    



class FakeUser(models.Model):
    name = models.CharField(max_length=50)
    accesses = models.OneToOneField(Security, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("abac:user", kwargs={"pk": self.pk})
    

class Object(models.Model):
    class ObjectType(models.TextChoices):
        SHIP = "SHIP", "Ship"
        SUB = "SUB", "Submarine" 
        AC = "AC", "Aircraft"
        FILE = "FILE", "File"

    name = models.CharField(max_length=15)
    obj_type =  models.CharField(max_length=4, choices=ObjectType.choices, default=ObjectType.SHIP )
    x_coords = models.PositiveSmallIntegerField(
                        default=50,
                        validators=[
                            MaxValueValidator(100),
                        ] )
    y_coords = models.PositiveSmallIntegerField(default=50, 
                        validators=[
                            MaxValueValidator(100),
                        ] )
    security = models.OneToOneField(Security, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse("abac:object", kwargs={"pk": self.pk})
    
    def __str__(self):
        return self.name
### ###