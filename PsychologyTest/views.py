from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from .decorators import admin_required, login_required, user_required, ParticipantPsychologist_required, psychologist_required
from django.http import JsonResponse
from django.core.paginator import Paginator 
from .forms import SignUpForm, ScheduleForm, ResultForm, ProfileForm, PasswordForm
from .models import Registrations, Users, Results, TestSchedules
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Count
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def Home(request):
    context = {
        'section' : 'home'
    }
    return render(request, 'Home/index.html', context)

def ScheduleList(request):
    today = now().date()
    tomorrow = today + timedelta(days=1)
    
    schedules = TestSchedules.objects.annotate(
        registered_count=Count('registrations'),
        truncated_date=TruncDate('Date')
    ).all().order_by('-Date')
    
    query = request.GET.get('q')
    if query:
        schedules = TestSchedules.objects.annotate(
            registered_count=Count('registrations'),
            truncated_date=TruncDate('Date')
        ).filter(
            Q(Name__icontains=query) | 
            Q(Date__icontains=query) | 
            Q(Psychologist__first_name__icontains=query) | 
            Q(Psychologist__last_name__icontains=query) | 
            Q(Description__icontains=query) | 
            Q(Location__icontains=query)
        ).order_by('-Date')
    
    paginator = Paginator(schedules, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'section': 'schedule-list',
        'test_schedules': page_obj,
        'tomorrow': tomorrow,
        'query': query
    }
    return render(request, 'Home/schedule.html', context)

def About(request):
    context = {
        'section' : 'about'
    }
    return render(request, 'Home/about.html', context)

def Contact(request):
    context = {
        'section' : 'contact'
    }
    return render(request, 'Home/contact.html', context)

def SignIn(request):
    context = {
        'section' : 'sign-in'
    }
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'message': 'Sign in successfuly!',
                'role' : user.role,
                'isAdmin' : user.is_staff
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username or password.',
            })

    return render(request, 'Home/sign-in.html', context)

def SignUp(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data['password']
            user = form.save(commit=False)
            user.set_password(password)
            user.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Sign up successful!'
            })

        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list

            return JsonResponse({
                'status': 'error',
                'message': 'Sign up failed.',
                'errors': errors
            })

    return render(request, 'Home/sign-up.html', {'section': 'sign-in'})

def SignOut(request):
    logout(request)
    return redirect('sign-in')

def delete_old_file(file_path):
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

@login_required()
def TestSchedule(request):
    psychologists = Users.objects.filter(role=Users.PSYCHOLOGIST)
    today = now().date()
    tomorrow = today + timedelta(days=1)
    
    schedules = TestSchedules.objects.annotate(
        registered_count=Count('registrations'),
        truncated_date=TruncDate('Date')
    ).all().order_by('-Date')
    
    query = request.GET.get('q')
    if query:
        schedules = TestSchedules.objects.annotate(
            registered_count=Count('registrations'),
            truncated_date=TruncDate('Date')
        ).filter(
            Q(Name__icontains=query) | 
            Q(Date__icontains=query) | 
            Q(Psychologist__first_name__icontains=query) | 
            Q(Psychologist__last_name__icontains=query) | 
            Q(Description__icontains=query) | 
            Q(Location__icontains=query)
        ).order_by('-Date')
    
    paginator = Paginator(schedules, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.user.role == -1:
        return render(request, 'MindSphere/schedule.html', context={
            'section' : 'test-schedule', 
            'psychologists' : psychologists,
            'test_schedules' : page_obj,
            'tomorrow': tomorrow,
            'query': query
        })
    
    return render(request, 'MindSphere/schedule.html', context={
        'section' : 'test-schedule',
        'test_schedules' : page_obj,
        'tomorrow': tomorrow,
        'query': query
    })

@admin_required()
def AddSchedule(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST, request.FILES)
        if form.is_valid():
            schedule = form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Schedule added successfully!'
            })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list
                
            return JsonResponse({
                'status': 'error',
                'message': 'Failed adding schedule! please check your input',
                'errors': errors,
            })
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method!',
    })

@admin_required()
def UpdateSchedule(request, pk):
    if request.method == 'POST':
        schedule = TestSchedules.objects.filter(id=pk).first()
        
        if not schedule:
            return JsonResponse({
                'status': 'error',
                'message': 'Test schedule not found!'
            })
        
        form = ScheduleForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            
            total_registered = Registrations.objects.filter(TestSchedule=schedule).count()
            if total_registered > data['Capacity']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You cannot update with that capacity! the capacity must be more or equal to the numbers of registrants.'
                })
                
            schedule.Name = data['Name']
            psychologist_id = data['Psychologist']
            psychologist = Users.objects.filter(id=psychologist_id.id, role=Users.PSYCHOLOGIST).first()
            if not psychologist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Selected psychologist is invalid!'
                })
            schedule.Psychologist = psychologist
            
            schedule.Description = data['Description']
            schedule.Date = data['Date']
            schedule.Capacity = data['Capacity']
            schedule.Location = data['Location']
            
            if 'Image' in request.FILES:
                if schedule.Image:
                    delete_old_file(schedule.Image.path)
                schedule.Image = request.FILES['Image']
            try:
                schedule.save()
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid Data: {str(e)}'
                })
            
            return JsonResponse({
                'status': 'success',
                'message': 'Schedule updated successfully!'
            })
            
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list
                
            return JsonResponse({
                'status': 'error',
                'message': 'Failed updating schedule! please check your input',
                'errors': errors,
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@admin_required()
def DeleteSchedule(request, pk):
    if request.method == 'DELETE':
        try:
            schedule = TestSchedules.objects.get(id=pk)
            if schedule.Image:
                delete_old_file(schedule.Image.path)
            schedule.delete()
            return JsonResponse({'status': 'success', 'message': 'Schedule deleted successfully!'})
        except TestSchedules.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Schedule not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@user_required()
def RegisterSchedule(request, pk):
    if request.method == 'POST':
        schedule = TestSchedules.objects.annotate(
            registered_count=Count('registrations'),
            truncated_date=TruncDate('Date')
        ).filter(id=pk).first()
        
        if not schedule:
            return JsonResponse({
                'status': 'error',
                'message': 'Test schedule not found!'
            })

        if Registrations.objects.filter(User=request.user, TestSchedule=schedule).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'You have already registered for this schedule!'
            })
        
        if schedule.registered_count >= schedule.Capacity:
            return JsonResponse({
                'status': 'error',
                'message': 'Test schedule has reached its maximum capacity.'
            })
            
        if schedule.truncated_date <= now().date():
            return JsonResponse({
                'status': 'error',
                'message': 'Test schedule has already passed.'
            })
        
        try:
            registration = Registrations(User=request.user, TestSchedule=schedule)
            registration.save()
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
        
        return JsonResponse({'status': 'success', 'message': 'Registration successful!'})

@ParticipantPsychologist_required()
def PsychologicalTest(request):
    registrations = Registrations.objects.all()
    
    if request.user.role == Users.PARTICIPANT:
        registrations = Registrations.objects.filter(User=request.user, Status='Waiting for Result').order_by('TestSchedule__Date')
    elif request.user.role == Users.PSYCHOLOGIST:
        registrations = Registrations.objects.filter(TestSchedule__Psychologist=request.user, Status='Waiting for Result').order_by('TestSchedule__Date', 'ParticipantNumber')

    serialized_data = [
        {
            'id': reg.id,
            'name': f"{reg.User.first_name} {reg.User.last_name}",
            'schedule_name': reg.TestSchedule.Name,
            'psychologist': f"{reg.TestSchedule.Psychologist.first_name} {reg.TestSchedule.Psychologist.last_name}",
            'number': reg.ParticipantNumber,
            'location': reg.TestSchedule.Location,
            'date': reg.TestSchedule.Date.isoformat(),
            'status': reg.Status
        }
        for reg in registrations
    ]

    return render(request, 'MindSphere/test.html', context={
        'section': 'psychological-test',
        'registrations_json': serialized_data
    })

@user_required()
def DeleteRegistration(request, pk):
    if request.method == 'DELETE':
        try:
            registration = Registrations.objects.get(id=pk)
            registration.delete()
            return JsonResponse({
                'status': 'success', 
                'message': 'Registration deleted successfully!'
            })
        except Registrations.DoesNotExist:
            return JsonResponse({
                'status': 'error', 
                'message': 'Registrations not found.'
            })
        
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request method.'
    })

@psychologist_required() 
def AddResult(request, pk):
    if request.method == 'POST':
        form = ResultForm(request.POST)
        print(request.POST.get('Summary'))
        if form.is_valid():
            registration = Registrations.objects.get(id=pk)
            if not registration:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Registration not found.'
                })
            
            try:
                result = form.save(commit=False)
                result.IsDone = True if request.POST.get('IsDone') == 'True' else False
                result.Registration = registration
                
                form.save()
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
                
            return JsonResponse({
                'status': 'success',
                'message': 'Result added successfully!'
            })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list
                
            return JsonResponse({
                'status': 'error',
                'message': 'Failed finish the result! please try again',
                'errors': errors,
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    })
 
@admin_required()
def PsycologistManagement(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data['password']
            user = form.save(commit=False)
            user.set_password(password)
            user.role = Users.PSYCHOLOGIST
            user.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Successfully created psychologist account!'
            })

        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list

            return JsonResponse({
                'status': 'error',
                'message': 'Failed creating account.',
                'errors': errors
            })
    return render(request, 'MindSphere/psychologist.html', context={'section' : 'psychologist'})

@login_required()
def History(request):
    result = Results.objects.all().order_by('-Date', '-ResultNumber')
    
    if request.user.role == Users.PARTICIPANT:
        result = Results.objects.filter(Registration__User=request.user).order_by('-Date', '-ResultNumber')
    elif request.user.role == Users.PSYCHOLOGIST:
        result = Results.objects.filter(Registration__TestSchedule__Psychologist=request.user).order_by('-Date', '-ResultNumber')
    
    serialized_data = [
        {
            'id': res.id,
            'name': f"{res.Registration.User.first_name} {res.Registration.User.last_name}",
            'schedule_name': res.Registration.TestSchedule.Name,
            'psychologist': f"{res.Registration.TestSchedule.Psychologist.first_name} {res.Registration.TestSchedule.Psychologist.last_name}",
            'number': res.ResultNumber,
            'summary': res.Summary,
            'recommendation': res.Recommendation,
            'date': res.Date.isoformat(),
            'status': 'Completed' if res.IsDone else 'Not Completed'
        }
        for res in result
    ]
    
    return render(request, 'MindSphere/history.html', context={
        'section' : 'history',
        'result_json': serialized_data
    })

@login_required()
def AccountSettings(request):
    account = Users.objects.get(id=request.user.id)
    
    return render(request, 'MindSphere/settings.html', context={
        'section' : 'account-settings',
        'account': account
    })

@login_required()
def ChangeProfile(request):
    if request.method == 'POST':
        account = Users.objects.get(id=request.user.id)
        form = ProfileForm(request.POST, instance=account)
        if form.is_valid():
            data = form.cleaned_data
            
            account.username = data['username']
            account.first_name = data['first_name']
            account.last_name = data['last_name']
            account.email = data['email']
            
            account.save()

            return JsonResponse({'status': 'success', 'message': 'Profile updated successfully!'})
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list

            return JsonResponse({
                'status': 'error',
                'message': 'Failed updating profile.',
                'errors': errors
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    })
    
@login_required()
def ChangePassword(request):
    if request.method == 'POST':
        user = request.user
        form = PasswordForm(request.POST, user=user)

        if form.is_valid():
            new_password = form.cleaned_data.get('password')
            user.set_password(new_password)
            user.save()
            
            update_session_auth_hash(request, user)

            return JsonResponse({'status': 'success', 'message': 'Password updated successfully!'})
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list
                
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to update password.',
                'errors': errors
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    })

def ForgotPassword(request):
    if request.method == "POST":
        email = request.POST.get("email")
        
        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Email not registered in our system.',
            })

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        reset_url = f"http://{get_current_site(request).domain}/reset-password/{uid}/{token}/"
        
        subject = "Reset your password"
        message = f"Click the link to reset your password: {reset_url}"
        
        try:
            send_mail(subject, message, 'anharkhoirun@gmail.com', [email])
            return JsonResponse({
                'status': 'success',
                'message': 'Password reset link has been sent to your email.',
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send email. ' + str(e),
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.',
    })
    
def ResetPassword(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        messages.error(request, 'Invalid link or expired token.')
        return redirect('sign-in')

    if not default_token_generator.check_token(user, token):
        messages.error(request, 'Invalid token or expired.')
        return redirect('sign-in')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return JsonResponse({
                'status': 'error',
                'message': 'Password and confirm password do not match.',
            })

        if password:
            user.set_password(password)
            user.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Successfully reset password.',
            })

    return render(request, 'Home/reset-password.html', {'uidb64': uidb64, 'token': token})

def GenerateCertificate(request, result_id):
    try:
        result = Results.objects.get(id=result_id)
    except Results.DoesNotExist:
        return HttpResponse("Result not found", status=404)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={result.ResultNumber}.pdf'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    logo_path = 'PsychologyTest/static/images/LogoPrimary.png'
    logo = os.path.join(settings.BASE_DIR, logo_path).replace('\\', '/')

    p.setTitle(f"{result.ResultNumber}")
    
    p.drawImage(logo, x=50, y=height - 100, width=100, height=100, preserveAspectRatio=True, mask='auto')

    p.setFont("Helvetica-Bold", 36)
    p.setFillColorRGB(0, 0, 0)
    p.setStrokeColorRGB(3 / 255, 97 / 255, 104 / 255)
    
    p.drawCentredString(width/2 - 15, height - 55, 'MIND SPHERE')
    
    p.setFont("Helvetica-Bold", 14)
    
    p.drawCentredString(width/2 + 50, height - 80, 'Jl. Kuaro, Mt. Kelua, Kec. Samarinda Ulu, Samarinda City')
    
    p.setLineWidth(2)
    p.line(0, height - 100, 700, height - 100)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(width/2 - len(result.ResultNumber)*4, height - 125, result.ResultNumber)

    p.setFont("Helvetica", 14)
    p.drawString(50, height - 165, 'The undersigned below :')
    p.drawString(65, height - 190, 'Psychologist')
    p.drawString(200, height - 190, f': {result.Registration.TestSchedule.Psychologist.first_name} {result.Registration.TestSchedule.Psychologist.last_name}')
    p.drawString(65, height - 210, 'Position')
    p.drawString(200, height - 210, ': Psychologist')
    p.drawString(65, height - 230, 'Company')
    p.drawString(200, height - 230, ': Mind Sphere')
    p.drawString(65, height - 250, 'Date')
    p.drawString(200, height - 250, f': {result.Date.strftime("%d %B, %Y")}')
    
    p.drawString(50, height - 285, 'Certifies that :')
    p.drawString(65, height - 310, 'Participant')
    p.drawString(200, height - 310, f': {result.Registration.User.first_name} {result.Registration.User.last_name}')
    p.drawString(65, height - 330, 'Test Type')
    p.drawString(200, height - 330, f': {result.Registration.TestSchedule.Name}')
    p.drawString(65, height - 350, 'Test Date')
    p.drawString(200, height - 350, f': {result.Registration.TestSchedule.Date.strftime("%d %B, %Y")}')
    p.drawString(65, height - 370, 'Test Location')
    p.drawString(200, height - 370, f': {result.Registration.TestSchedule.Location}')

    p.drawString(50, height - 405, "Based on the results of the psychological test conducted on the date above.")
    p.drawString(50, height - 425, "The following results were obtained:")
    
    p.drawString(65, height - 460, 'Summary of result')
    textSummary = result.Summary.replace('\n', ' ')
    nowHeight = height - 440
    if len(textSummary) > 45*4:
        textSummary = textSummary[0:45*4 - 2]
        textSummary += '...'
        
    if len(textSummary) > 45:
        count = int(len(textSummary)/45)
        for i in range (count):
            nowHeight -= 20
            if i == 0:
                p.drawString(200, nowHeight, f': {textSummary[i*45:i*45+45]}')
            elif i == count - 1:
                p.drawString(207, nowHeight, f'{textSummary[i*45:]}')
            else:
                p.drawString(207, nowHeight, f'{textSummary[i*45:i*45+45]}')
    else:
        nowHeight -= 20
        p.drawString(200, nowHeight, f': {result.Summary}')
    
    p.drawString(65, nowHeight - 20, 'Recommendation')
    textRecommendation = result.Recommendation.replace('\n', ' ')
    if len(textRecommendation) > 45*5:
        textRecommendation = textRecommendation[0:45*5 - 2]
        textRecommendation += '...'
    
    if len(textRecommendation) > 45:
        count = int(len(textRecommendation)/45)
        for i in range (count):
            nowHeight -= 20
            if i == 0:
                p.drawString(200, nowHeight, f': {textRecommendation[i*45:i*45+45]}')
            elif i == count - 1:
                p.drawString(207, nowHeight, f'{textRecommendation[i*45:]}')
            else:
                p.drawString(207, nowHeight, f'{textRecommendation[i*45:i*45+45]}')
    else:
        p.drawString(200, nowHeight - 20, f': {result.Recommendation}')
    
    p.drawString(400, 130, 'Best Regards,')
    
    logo_path = 'PsychologyTest/static/images/ttd.png'
    logo = os.path.join(settings.BASE_DIR, logo_path).replace('\\', '/')
    
    p.drawImage(logo, x=390, y=50, width=105, height=70, preserveAspectRatio=True, mask='auto')
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(360, 30, 'Director of Mind Shpere')
    
    p.showPage()
    p.save()
    return response