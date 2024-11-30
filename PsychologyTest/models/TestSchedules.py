from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now, timedelta
from . import Users

class TestSchedules(models.Model):
    Psychologist = models.ForeignKey(Users, limit_choices_to={'role': Users.PSYCHOLOGIST}, on_delete=models.CASCADE)
    Name = models.CharField(max_length=250)
    Description = models.TextField()
    Date = models.DateTimeField()
    Location = models.CharField(max_length=250)
    Capacity = models.IntegerField()
    Image = models.ImageField(upload_to='test_schedules/', blank=True, null=True)

    def clean(self):
        if self.Date < now() + timedelta(days=1):
            raise ValidationError({'Date': 'At least tomorrow.'})

        if self.Capacity <= 0:
            raise ValidationError({'Capacity': 'At least 1.'})
        
        if self.Capacity > 150:
            raise ValidationError({'Capacity': 'cannot exceed 150 participants.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.Name} - {self.Date.strftime("%Y-%m-%d")}'
