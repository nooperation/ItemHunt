from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import generic
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from server.models import *
import logging
import re
from datetime import datetime, date, time, timedelta

log = logging.getLogger(__name__)

JSON_RESULT_SUCCESS = 'success'
JSON_RESULT_ERROR = 'error'
JSON_TAG_RESULT = 'result'
JSON_TAG_PAYLOAD = 'payload'
JSON_TAG_TARGET_UUID = 'target_uuid'

NULL_KEY = '00000000-0000-0000-0000-000000000000'
PATTERN_KEY = '^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'


def get_lsl_headers(request):
    position = request.META['HTTP_X_SECONDLIFE_LOCAL_POSITION'][1:-1].split(', ')
    region_matches = re.match(r"(.*) \(([0-9]+), ([0-9]+)\)", request.META['HTTP_X_SECONDLIFE_REGION'])
    region_name = region_matches.group(1).strip()

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


def json_success(message):
    return {JSON_TAG_RESULT: JSON_RESULT_SUCCESS, JSON_TAG_PAYLOAD: message}


def json_error(message):
    return {JSON_TAG_RESULT: JSON_RESULT_ERROR, JSON_TAG_PAYLOAD: message}


def json_success_to(target_uuid, message):
    return {JSON_TAG_RESULT: JSON_RESULT_SUCCESS, JSON_TAG_PAYLOAD: message, JSON_TAG_TARGET_UUID: target_uuid}


def json_error_to(target_uuid, message):
    return {JSON_TAG_RESULT: JSON_RESULT_ERROR, JSON_TAG_PAYLOAD: message, JSON_TAG_TARGET_UUID: target_uuid}


def is_valid_uuid(uuid):
    return re.match(PATTERN_KEY, uuid, re.I) is not None


# Create your models here.
class IndexView(generic.View):
    def get(self, request):
        return JsonResponse(json_success({'servers_list': 'stuff goes here'}))


@method_decorator(csrf_exempt, name='dispatch')
class ActivateItemView(generic.View):
    def post(self, request):
        player_name = ''

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
                self.log_detailed("FAILED - Invalid hunt", request)
                return JsonResponse(json_error_to(player_uuid, 'Invalid hunt specified'))

            if not hunt.enabled:
                self.log_detailed("FAILED - Hunt is disabled", request)
                return JsonResponse(json_error_to(player_uuid, 'Hunt is disabled'))

            try:
                item = Item.objects.get(uuid=sl_header['object_key'], hunt=hunt)
            except Item.DoesNotExist:
                self.log_detailed("FAILED - Invalid object", request)
                return JsonResponse(json_error_to(player_uuid, 'Invalid item'))

            if not item.enabled:
                self.log_detailed("FAILED - Item is disabled", request)
                return JsonResponse(json_error_to(player_uuid, 'Item is disabled'))

            try:
                region = Region.objects.get(name=sl_header['region'])
            except Region.DoesNotExist:
                region = Region(name=sl_header['region'])
                try:
                    region.full_clean()
                    region.save()
                except ValidationError:
                    self.log_detailed("FAILED - invalid region", request)
                    return JsonResponse(json_error_to(player_uuid, 'Invalid region'))

            try:
                player = Player.objects.get(name=player_name, uuid=player_uuid)
            except Player.DoesNotExist:
                player = Player(name=player_name, uuid=player_uuid)
                try:
                    player.full_clean()
                    player.save()
                except ValidationError:
                    self.log_detailed("FAILED - invalid player", request)
                    return JsonResponse(json_error_to(player_uuid, 'Invalid player'))

            if item.type == Item.TYPE_CREDIT:
                threshold = datetime.today() - timedelta(minutes=5)
                activation_count = Transaction.objects.filter(item=item, player=player, created_on__gt=threshold).count()
                if activation_count != 0:
                    return JsonResponse(json_error_to(player_uuid, {"code": "already_used"}))
            elif item.type == Item.TYPE_PRIZE:
                total_points = player.get_total_points(hunt)
                if points > total_points:
                    return JsonResponse(json_error_to(player_uuid, {"code": "not_enough_points", "points": points, "total_points": total_points}))

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
                self.log_detailed("Success", request)
            except ValidationError:
                self.log_detailed("FAILED - invalid transaction", request)
                return JsonResponse(json_error_to(player_uuid, 'Invalid transaction'))

            total_points = player.get_total_points(hunt)
            return JsonResponse(json_success_to(player_uuid, {'points': points, 'total_points': total_points}))
        except Exception:
            log.exception("Failed to activate player '{}' with uuid '{}'".format(player_name, player_uuid))
            self.log_detailed("FAILED - Server error", request)
            return JsonResponse(json_error_to(player_uuid, 'Server error'))

    @staticmethod
    def log_detailed(message, request):
        sl_header = get_lsl_headers(request)
        player_name = request.POST.get('player_name')
        player_uuid = request.POST.get('player_uuid')
        points = request.POST.get('points')

        object_position = request.META['HTTP_X_SECONDLIFE_LOCAL_POSITION']
        object_region = request.META['HTTP_X_SECONDLIFE_REGION']

        log.info("Activation: {} points='{}' player='{}' player_uuid='{}' region='{}' object_position='{}' object_key='{}' object_name='{}' owner_key='{}'".format(
           message,
           points,
           player_name,
           player_uuid,
           object_region,
           object_position,
           sl_header['object_key'],
           sl_header['object_name'],
           sl_header['owner_key'],
        ))


@method_decorator(csrf_exempt, name='dispatch')
class RegisterItemView(generic.View):
    def post(self, request):
        try:
            sl_header = get_lsl_headers(request)
            private_token = request.POST.get('private_token')
            points = int(request.POST.get('points'))
            item_type = int(request.POST.get('type'))

            try:
                hunt = Hunt.objects.get(private_token=private_token)
            except Hunt.DoesNotExist:
                self.log_detailed("FAILED - Invalid hunt", request)
                return JsonResponse(json_error('Invalid hunt specified'))

            if not hunt.enabled:
                self.log_detailed("FAILED - Hunt is disabled", request)
                return JsonResponse(json_error('Hunt is disabled'))

            try:
                region = Region.objects.get(name=sl_header['region'])
            except Region.DoesNotExist:
                region = Region(name=sl_header['region'])
                try:
                    region.full_clean()
                    region.save()
                except ValidationError:
                    self.log_detailed("FAILED - invalid region", request)
                    return JsonResponse(json_error('Invalid region'))

            existing_item = Item.objects.filter(uuid=sl_header['object_key'], hunt=hunt).first()
            if existing_item is not None:
                existing_item.name = sl_header['object_name']
                existing_item.type = item_type
                existing_item.position_x = sl_header['position_x']
                existing_item.position_y = sl_header['position_y']
                existing_item.position_z = sl_header['position_z']
                existing_item.points = points
                existing_item.region = region
                existing_item.hunt = hunt
                existing_item.full_clean()
                existing_item.save()
                self.log_detailed("Updated", request)
                return JsonResponse(json_success('OK'))

            new_item = Item(
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
            new_item.full_clean()
            new_item.save()
            self.log_detailed("Created", request)
            return JsonResponse(json_success('OK'))
        except TypeError:
            return JsonResponse(json_error('Server error'))
        except ValidationError:
            self.log_detailed("FAILED - Item failed validation", request)
            if points < 0:
                return JsonResponse(json_error('Points cannot be negative'))
            return JsonResponse(json_error('Server error'))
        except Exception:
            log.exception("Failed to register item")
            self.log_detailed("FAILED - Failed to register item", request)
            return JsonResponse(json_error('Server error'))

    @staticmethod
    def log_detailed(message, request):
        sl_header = get_lsl_headers(request)
        item_type = request.POST.get('item_type')
        points = request.POST.get('points')

        object_position = request.META['HTTP_X_SECONDLIFE_LOCAL_POSITION']
        object_region = request.META['HTTP_X_SECONDLIFE_REGION']

        log.info("Registration: {} points='{}' item_type='{}' region='{}' object_position='{}' object_key='{}' object_name='{}' owner_key='{}'".format(
           message,
           points,
           item_type,
           object_region,
           object_position,
           sl_header['object_key'],
           sl_header['object_name'],
           sl_header['owner_key'],
        ))

@method_decorator(csrf_exempt, name='dispatch')
class GetTotalPointsView(generic.View):
    def post(self, request):
        player_uuid = ''

        try:
            private_token = request.POST.get('private_token')
            player_uuid = request.POST.get('player_uuid')

            if not is_valid_uuid(player_uuid):
                log.warning("Invalid UUID passed to GetTotalPointsView: '{}'".format(player_uuid))
                return JsonResponse(json_error('Server error'))

            try:
                hunt = Hunt.objects.get(private_token=private_token)
            except Hunt.DoesNotExist:
                return JsonResponse(json_error_to(player_uuid, 'Invalid hunt specified'))

            try:
                player = Player.objects.get(uuid=player_uuid)
            except Player.DoesNotExist:
                return JsonResponse(json_success_to(player_uuid, {'total_points': 0}))

            total_points = player.get_total_points(hunt)
            return JsonResponse(json_success_to(player_uuid, {'total_points': total_points}))
        except Exception:
            log.exception("Failed to get total points for uuid '{}'".format(player_uuid))
            return JsonResponse(json_error_to(NULL_KEY, 'Server error'))


@method_decorator(csrf_exempt, name='dispatch')
class PurgeExpiredTokensView(generic.View):
    def get(self, request):
        try:
            HuntAuthorizationToken.delete_all_expired()
            return JsonResponse(json_success('OK'))
        except Exception:
            log.exception("Failed to purge expired tokens")
            return JsonResponse(json_error('Server error'))
