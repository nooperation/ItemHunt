from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import generic

JSON_RESULT_SUCCESS = 'success'
JSON_RESULT_ERROR = 'error'
JSON_TAG_RESULT = 'result'
JSON_TAG_MESSAGE = 'payload'


def json_success(message):
    return {JSON_TAG_RESULT: JSON_RESULT_SUCCESS, JSON_TAG_MESSAGE: message}


def json_error(message):
    return {JSON_TAG_RESULT: JSON_RESULT_ERROR, JSON_TAG_MESSAGE: message}


# Create your models here.
class IndexView(generic.View):
    def get(self, request):
        return JsonResponse(json_success({'servers_list': 'stuff goes here'}))
