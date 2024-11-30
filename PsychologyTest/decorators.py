from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.is_superuser and request.user.is_staff:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You must signed in as admin to access this page.')
                return redirect('sign-in')
        return _wrapped_view
    return decorator

def user_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and request.user.role == 2:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You must signed in as participant to access this page.')
                return redirect('sign-in')
        return _wrapped_view
    return decorator

def psychologist_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and request.user.role == 1:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You must signed in as psychologist to access this page.')
                return redirect('sign-in')
        return _wrapped_view
    return decorator

def ParticipantPsychologist_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and (request.user.role == 1 or request.user.role == 2):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You must signed in as participant to access this page.')
                return redirect('sign-in')
        return _wrapped_view
    return decorator

def login_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You must signed in to access this page.')
                return redirect('sign-in')
        return _wrapped_view
    return decorator