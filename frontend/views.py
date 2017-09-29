from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import generic
from server.models import Hunt
from server.views import json_success


class IndexView(LoginRequiredMixin, generic.View):
    def get(self, request):
        hunt_list = Hunt.objects.all()
        return render(request, 'frontend/index.html', {'hunt_list': hunt_list})

