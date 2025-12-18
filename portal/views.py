from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, 'pages/index.html')


import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView

# Set up logging
logger = logging.getLogger(__name__)
class LoginView(View):
    template_name = 'auth/auth-login.html'

    def get(self, request):
        logger.debug("LoginView GET request received")
        if request.user.is_authenticated:
            logger.info(f"User {request.user} already authenticated, redirecting")
            messages.info(request, "You're already logged in!")
            return redirect('home')
        
        logger.debug("Rendering login form")
        return render(request, self.template_name)

    def post(self, request):
        logger.debug("LoginView POST request received")
        # form = self.form_class(request.POST)
        # print(request.POST)
        data = request.POST
        # print(f'data: {data}')
        
        if data:
            username = data['username']
            password = data['password']
            remember_me = data.get('remember_me', False)
            logger.debug(f"Attempting authentication for phone: {username}")

            # print(phone_number, password, remember_me)
            
            user = authenticate(request, username=username, password=password)

            if user is not None:
                logger.info(f"User {user} authenticated successfully")
                login(request, user)
                
                if not remember_me:
                    logger.debug("Setting session to expire on browser close")
                    request.session.set_expiry(0)
                
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                next_url = request.GET.get('next', reverse_lazy('home'))
                logger.debug(f"Redirecting to: {next_url}")
                return redirect(next_url)
            else:
                logger.warning(f"Authentication failed for phone: {username}")
                messages.error(request, "Invalid phone number or password. Please try again.")
       
        
        logger.debug("Re-rendering login form with errors")
        return render(request, self.template_name)


class LogoutView(View):
    print
    def get(self, request):
        logger.debug("LogoutView GET request received")
        if request.user.is_authenticated:
            logger.info(f"Logging out user: {request.user}")
            logout(request)
            messages.success(request, "You've been successfully logged out!")
            return redirect('login')
        else:
            logger.debug("Anonymous user attempted logout")
            messages.info(request, "You weren't logged in to begin with.")
        logger.debug("Redirecting to login page")
        return redirect('login')


from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User, Group

@require_http_methods(["GET", "POST"])
def change_password(request):
    if request.method == 'POST':
        print(request.POST)
        form = PasswordChangeForm(request.user, request.POST)



        username = request.POST.get('username')
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if not username or not current_password or not new_password1 or not new_password2:
            messages.error(request, 'Please fill in all required fields.', extra_tags='password')
            return redirect('login')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User does not exist.', extra_tags='password')
            return redirect('login')
        
        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.', extra_tags='password')
            return redirect('login')
        
        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.', extra_tags='password')
            return redirect('login')
        
        # if len(new_password1) < 8:
        #     messages.error(request, 'New password must be at least 8 characters long.', extra_tags='password')
        #     return redirect('login')
        
        # Additional password validations can be added here

        user.set_password(new_password1)
        user.save()
        update_session_auth_hash(request, user)  # Important, to keep the user logged in after password change
        messages.success(request, 'Your password was successfully updated!', extra_tags='password')
        return redirect('login')
    
    # If GET request, just redirect to login page
    return redirect('login')

# If you want a separate page for password change (optional)
@login_required
def password_change_done(request):
    messages.success(request, 'Your password has been changed successfully!')
    return redirect('login')