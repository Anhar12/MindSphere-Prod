from django.db import models
from django.core.exceptions import ValidationError
from . import Users, TestSchedules
from django.db.models import F

class Registrations(models.Model):
    STATUS_CHOICES = (
        ('Waiting for Result', 'Waiting for Result'),
        ('Finished', 'Finished'),
    )

    User = models.ForeignKey(Users, limit_choices_to={'role': Users.PARTICIPANT}, on_delete=models.CASCADE)
    TestSchedule = models.ForeignKey(TestSchedules, on_delete=models.CASCADE)
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Waiting for Result')
    ParticipantNumber = models.IntegerField()

    def save(self, *args, **kwargs):
        if self._state.adding:
            if Registrations.objects.filter(User=self.User, TestSchedule=self.TestSchedule).exists():
                raise ValidationError(f'{self.User.username} participant has already registered for {self.TestSchedule}')

            total_registered = Registrations.objects.filter(TestSchedule=self.TestSchedule).count()
            if total_registered >= self.TestSchedule.Capacity:
                raise ValidationError('Test schedule has reached its maximum capacity.')

            if not self.ParticipantNumber:
                self.ParticipantNumber = total_registered + 1
        
        super().save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        deleted_number = self.ParticipantNumber

        super().delete(*args, **kwargs)

        Registrations.objects.filter(
            ParticipantNumber__gt=deleted_number
        ).update(ParticipantNumber=F('ParticipantNumber') - 1)


    def __str__(self):
        return f'{self.User.username} - {self.TestSchedule.Name} ({self.Status})'
