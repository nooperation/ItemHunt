from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import generic
from django.core.exceptions import ValidationError
from server.models import *
import logging

JSON_RESULT_SUCCESS = 'success'
JSON_RESULT_ERROR = 'error'
JSON_TAG_RESULT = 'result'
JSON_TAG_MESSAGE = 'payload'

def get_lsl_headers(request):
    position = request.META['HTTP_X_SECONDLIFE_LOCAL_POSITION'][1:-1].split(', ')
    region = request.META['HTTP_X_SECONDLIFE_REGION'].split(' ')
    region_name = region[0]

    return {
        'owner_name': request.META['HTTP_X_SECONDLIFE_OWNER_NAME'],
        'object_name': request.META['HTTP_X_SECONDLIFE_OBJECT_NAME'],
        'object_key': request.META['HTTP_X_SECONDLIFE_OBJECT_KEY'],
        'owner_key': request.META['HTTP_X_SECONDLIFE_OWNER_KEY'],
        'shard': request.META['HTTP_X_SECONDLIFE_SHARD'],
        'region': region_name,
        'position_x': position[0],
        'position_y': position[1],
        'position_z': position[2],
    }

def report_invalid_activation(message, request):
    sl_header = get_lsl_headers(request)
    player_name = request.POST.get('player_name')
    player_uuid = request.POST.get('player_uuid')
    points = request.POST.get('points')

    object_position = request.META['HTTP_X_SECONDLIFE_LOCAL_POSITION']
    object_region = request.META['HTTP_X_SECONDLIFE_REGION']

    logging.info(f"{message} "
                 f"points='{points}' "
                 f"player='{player_name}' "
                 f"player_uuid='{player_uuid}' "
                 f"region='{object_region}' "
                 f"object_position='{object_position}' "
                 f"object_key='{sl_header['object_key']}' "
                 f"object_name='{sl_header['object_name']}' "
                 f"owner_key='{sl_header['owner_key']}' "
                 f"address='{request.META['REMOTE_ADDR']}'")

def json_success(message):
    return {JSON_TAG_RESULT: JSON_RESULT_SUCCESS, JSON_TAG_MESSAGE: message}


def json_error(message):
    return {JSON_TAG_RESULT: JSON_RESULT_ERROR, JSON_TAG_MESSAGE: message}


# Create your models here.
class IndexView(generic.View):
    def get(self, request):
        return JsonResponse(json_success({'servers_list': 'stuff goes here'}))


class ActivateItemView(generic.View):
    def post(self, request):
        player_name = ''
        player_uuid = ''

        try:
            sl_header = get_lsl_headers(request)
            private_token = request.POST.get('private_token')
            player_name = request.POST.get('player_name')
            player_uuid = request.POST.get('player_uuid')
            player_x = float(request.POST.get('player_x'))
            player_y = float(request.POST.get('player_y'))
            player_z = float(request.POST.get('player_z'))
            points = int(request.POST.get('points'))

            try:
                hunt = Hunt.objects.get(private_token=private_token)
            except Hunt.DoesNotExist:
                report_invalid_activation("Invalid hunt", request)
                return JsonResponse(json_error('Invalid hunt specified'))

            try:
                item = Item.objects.get(uuid=sl_header['object_key'], hunt=hunt)
            except Item.DoesNotExist:
                report_invalid_activation("Invalid object", request)
                return JsonResponse(json_error('Invalid item'))

            try:
                region = Region.objects.get(name=sl_header['region'])
            except Region.DoesNotExist:
                region = Region(name=sl_header['region'])
                try:
                    region.full_clean()
                    region.save()
                except ValidationError:
                    report_invalid_activation("invalid region", request)
                    return JsonResponse(json_error('Invalid region'))

            try:
                player = Player.objects.get(name=player_name, uuid=player_uuid)
            except Player.DoesNotExist:
                player = Player(name=player_name, uuid=player_uuid)
                try:
                    player.full_clean()
                    player.save()
                except ValidationError:
                    report_invalid_activation("invalid player", request)
                    return JsonResponse(json_error('Invalid player'))

            if item.type == Item.TYPE_CREDIT:
                activation_count = Transaction.objects.filter(item=item, player=player).count()
                if activation_count != 0:
                    return JsonResponse(json_error('You have already used this item'))
            elif item.type == Item.TYPE_PRIZE:
                total_points = player.get_total_points(hunt)
                if points > total_points:
                    return JsonResponse(json_error("You need {} more points to buy this"))

            new_transaction = Transaction(
                points=points if item.type == Item.TYPE_CREDIT else -points,
                player_x=player_x,
                player_y=player_y,
                player_z=player_z,
                item_x=sl_header['position_x'],
                item_y=sl_header['position_y'],
                item_z=sl_header['position_z'],
                player=player,
                region=region,
                hunt=hunt,
                item=item
            )
            try:
                new_transaction.full_clean()
                new_transaction.save()
            except ValidationError:
                report_invalid_activation("invalid transaction", request)
                return JsonResponse(json_error('Invalid transaction'))

            total_points = player.get_total_points(hunt)
            return JsonResponse(json_success({'points': points, 'total_points': total_points}))
        except Exception:
            logging.exception("Failed to activate player '{}' with uuid '{}'".format(player_name, player_uuid))
            report_invalid_activation("Server error", request)
            return JsonResponse(json_error('Server error'))


class RegisterItemView(generic.View):
    def post(self, request):
        try:
            sl_header = get_lsl_headers(request)
            private_token = request.POST.get('private_token')
            points = request.POST.get('points')
            item_type = request.POST.get('type')

            try:
                hunt = Hunt.objects.get(private_token=private_token)
            except Hunt.DoesNotExist:
                report_invalid_activation("Invalid hunt", request)
                return JsonResponse(json_error('Invalid hunt specified'))

            try:
                region = Region.objects.get(name=sl_header['region'])
            except Region.DoesNotExist:
                region = Region(name=sl_header['region'])
                try:
                    region.full_clean()
                    region.save()
                except ValidationError:
                    report_invalid_activation("invalid region", request)
                    return JsonResponse(json_error('Invalid region'))

            item_count = Item.objects.filter(uuid=sl_header['object_key'], hunt=hunt).count()
            if item_count > 0:
                return JsonResponse(json_success('OK'))

            new_item = Item.objects.create(
                uuid=sl_header['object_key'],
                name=sl_header['object_name'],
                type=item_type,
                position_x=sl_header['position_x'],
                position_y=sl_header['position_y'],
                position_z=sl_header['position_z'],
                points=points,
                enabled=True,
                region=region,
                hunt=hunt
            )
            return JsonResponse(json_success('OK'))
        except Exception:
            logging.exception("Failed to register item")
            return JsonResponse(json_error('Server error'))


class GetTotalPointsView(generic.View):
    def post(self, request):
        player_name = ''
        player_uuid = ''

        try:
            private_token = request.POST.get('private_token')
            player_name = request.POST.get('player_name')
            player_uuid = request.POST.get('player_uuid')

            try:
                hunt = Hunt.objects.get(private_token=private_token)
            except Hunt.DoesNotExist:
                return JsonResponse(json_error('Invalid hunt specified'))

            try:
                player = Player.objects.get(name=player_name, uuid=player_uuid)
            except Player.DoesNotExist:
                return JsonResponse(json_success({'total_points': 0}))

            total_points = player.get_total_points(hunt)
            return JsonResponse(json_success({'total_points': total_points}))
        except Exception:
            logging.exception("Failed to get total points for player '{}' with uuid '{}'".format(player_name, player_uuid))
            return JsonResponse(json_error('Server error'))
