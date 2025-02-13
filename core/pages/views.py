from django.shortcuts import render, redirect, HttpResponseRedirect, reverse


def home(request):
    return HttpResponseRedirect(reverse('profile'))
