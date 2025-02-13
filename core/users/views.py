from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import UserUpdateForm, PasswordChangingForm
from employees.models import Employee


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Your profile has been updated successfully.')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)

    # get some user details
    try:
        # employee = get_object_or_404(Employee, user=request.user)
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = None

    context = {
        'form': form,
        'employee': employee,
        # 'groups': groups
    }

    return render(request, 'users/profile.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangingForm(data=request.POST, user=request.user)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            request.session['default_password_checked'] = request.user.check_password(
                'welcome01')
            messages.success(
                request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangingForm(user=request.user)

    context = {
        'form': form,
    }
    return render(request, 'users/change_password.html', context)
