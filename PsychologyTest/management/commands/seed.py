from django.core.management.base import BaseCommand
from faker import Faker
from PsychologyTest.models import Users, Registrations, Results, TestSchedules
import random
from django.utils import timezone
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Seed database with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--participants', type=int, default=150, help='Number of participants to create'
        )
        parser.add_argument(
            '--pyschologist', type=int, default=3, help='Number of pyschologist to create'
        )
        parser.add_argument(
            '--test_schedules', type=int, default=5, help='Number of test_schedules to create'
        )
        parser.add_argument(
            '--registrations', type=int, default=1, help='Number of registrations to create'
        )
        parser.add_argument(
            '--results', type=int, default=1, help='Number of results to create'
        )
        parser.add_argument(
            '--clear', action='store_true', help='Clear all data except admin superuser'
        )

    def handle(self, *args, **options):
        fake = Faker('id_ID')
        
        if options['clear']:
            self.clear_data()
            self.stdout.write(self.style.SUCCESS('Cleared all data.'))
            return

        num_participants = options['participants']
        num_pyschologist = options['pyschologist']
        num_schedules = options['test_schedules']
        num_registrations = options['registrations']
        num_results = options['results']

        participants = []
        pyschologist = []
        
        for _ in range(num_participants):
            username = fake.unique.name()
            first_name = fake.first_name()
            last_name = fake.last_name()
            password = fake.password()
            
            user = Users.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role=Users.PARTICIPANT
            )
            
            participants.append(user)
        
        for _ in range(num_pyschologist):
            username = fake.unique.name()
            first_name = fake.first_name()
            last_name = fake.last_name()
            password = fake.password()
            
            user = Users.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role=Users.PSYCHOLOGIST
            )
            
            pyschologist.append(user)

        test_schedules = []
        tomorrow = (datetime.today() + timedelta(days=1)).date()

        for _ in range(num_schedules):
            Psychologist = random.choice(pyschologist)
            Name = fake.bs().title() + " Test"
            Description = fake.text(max_nb_chars=200)
            Location = fake.address()
            Capacity = fake.random_int(min=40, max=50)
            schedule_date = fake.date_between(start_date=tomorrow, end_date='+1y')
            naive_date = datetime.combine(schedule_date, datetime.min.time())
            Date = timezone.make_aware(naive_date)

            test_entry = TestSchedules.objects.create(
                Psychologist=Psychologist,
                Date=Date,
                Name=Name,
                Description=Description,
                Location=Location,
                Capacity=Capacity
            )
            test_schedules.append(test_entry)

        registrations = []
        for _ in range(num_registrations):
            User = random.choice(participants)

            available_schedules = [
                schedule for schedule in test_schedules
                if Registrations.objects.filter(User=User, TestSchedule=schedule).count() == 0 and 
                Registrations.objects.filter(TestSchedule=schedule).count() < schedule.Capacity
            ]
            
            if not available_schedules:
                print("No available TestSchedules with capacity left.")
                break

            TestSchedule = random.choice(available_schedules)
            print(f"Checking registration for {User.username} in {TestSchedule.Name}")
            if Registrations.objects.filter(User=User, TestSchedule=TestSchedule).exists():
                print(f"User {User.username} already registered for {TestSchedule.Name}")
            else:
                print(f"Registering {User.username} for {TestSchedule.Name}")
            total_registered = Registrations.objects.filter(TestSchedule=TestSchedule).count()
            regis_entry = Registrations.objects.create(
                User=User,
                TestSchedule=TestSchedule,
                ParticipantNumber=total_registered + 1
            )
            
            registrations.append(regis_entry)
    
        for _ in range(num_results):
            available_regis = [entry for entry in registrations if entry.Status != 'Finished']
            if not available_regis:
                break
            
            regis_entry = random.choice(available_regis)
            Summary = fake.text(max_nb_chars=200)
            Recommendation = fake.text()

            Results.objects.create(
                Registration=regis_entry,
                Summary=Summary,
                Recommendation=Recommendation
            )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully seeded {num_participants} participant, {num_pyschologist} psychologist, {num_schedules} test schedules, {num_registrations} registration, and {num_results} results.'
        ))

    def clear_data(self):
        Users.objects.filter(is_superuser=False).delete()