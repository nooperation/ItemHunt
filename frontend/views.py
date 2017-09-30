from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views import generic
from server.models import Hunt, HuntAuthorizationToken, AuthorizedUsers
from server.views import json_success
import logging


class IndexView(LoginRequiredMixin, generic.View):
    def get(self, request):
        authenticated_services = AuthorizedUsers.objects.filter(user=request.user)
        hunt_list = []
        for item in authenticated_services:
            hunt_list.append(item.hunt)
        return render(request, 'frontend/index.html', {'hunt_list': hunt_list})


class RegisterTokenView(LoginRequiredMixin, generic.View):
    def get(self, request, token):
        try:
            try:
                hunt_authorization_token = HuntAuthorizationToken.objects.get(token=token)
            except HuntAuthorizationToken.DoesNotExist:
                return render(request, 'frontend/register_token.html', {'error': 'Invalid token'})

            if hunt_authorization_token.is_expired():
                return render(request, 'frontend/register_token.html', {'error': 'Expired token'})

            hunt = hunt_authorization_token.hunt
            is_already_authorized = hunt.is_user_authorized(request.user)
            if is_already_authorized:
                hunt_authorization_token.delete()
                return render(request, 'frontend/register_token.html', {'error': 'User is already registered to this hunt'})

            hunt.authorize_user(request.user)
            hunt_authorization_token.delete()

        except Exception as ex:
            logging.exception('Failed to register token')
            return render(request, 'frontend/register_token.html', {'error': 'Invalid token'})
        # TODO: Add feedback
        return render(request, 'frontend/register_token.html', {'success': 'Server Registered', 'hunt_name': hunt.name})