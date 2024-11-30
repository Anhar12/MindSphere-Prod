from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from . import Registrations

class Results(models.Model):
    Registration = models.ForeignKey(Registrations, on_delete=models.CASCADE)
    Date = models.DateTimeField(default=now)
    Summary = models.TextField(null=True, blank=True)
    Recommendation = models.TextField(null=True, blank=True)
    ResultNumber = models.CharField(max_length=255, unique=True, null=True, blank=True)
    IsDone = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.ResultNumber and self.IsDone:
            test_name = self.Registration.TestSchedule.id
            reg_participant_number = self.Registration.ParticipantNumber
            day = self.Date.day
            month = self.Date.month
            year = self.Date.year

            roman_month = self.convert_to_roman(month)

            self.ResultNumber = f"MS/{test_name}/{year}/{roman_month}/{day}/{reg_participant_number}"
        
        if not self.IsDone:
            self.ResultNumber = "Not completed"
        
        if not self.Summary and self.IsDone:
            raise ValidationError('Summary is required')
        
        if not self.Summary and not self.IsDone:
            self.Summary = "You're not completed this test"
        
        if self.Date < self.Registration.TestSchedule.Date:
            raise ValidationError('The test is not finished yet! You are not allowed to input the results now.')
        
        self.Registration.Status = 'Finished'
        self.Registration.save()
        
        super().save(*args, **kwargs)

    def convert_to_roman(self, number):
        roman_numerals = {
            1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI',
            7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII'
        }
        return roman_numerals.get(number, '')

    def __str__(self):
        return f'Result for {self.Registration}'
