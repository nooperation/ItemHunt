from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django import template

# Create your views here.
from django.urls import reverse
from django.views import generic
from server.models import Hunt, HuntAuthorizationToken, AuthorizedUsers, Item, Transaction, Player
import logging

log = logging.getLogger(__name__)


class IndexView(LoginRequiredMixin, generic.View):
    def get(self, request):
        authenticated_services = AuthorizedUsers.objects.filter(user=request.user)
        hunt_list = []
        for item in authenticated_services:
            hunt_list.append(item.hunt)

        request.breadcrumbs = [{
            'name': 'Home'
        }]
        return render(request, 'frontend/index.html', {
            'hunt_list': hunt_list
        })


class RegisterTokenView(LoginRequiredMixin, generic.View):
    def get(self, request, token):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            try:
                hunt_authorization_token = HuntAuthorizationToken.objects.get(token=token)
            except HuntAuthorizationToken.DoesNotExist:
                return render(request, 'frontend/register_token.html', {
                    'error': 'Invalid token'
                }, status=400)

            if hunt_authorization_token.is_expired():
                return render(request, 'frontend/register_token.html', {
                    'error': 'Expired token'
                }, status=400)

            hunt = hunt_authorization_token.hunt
            is_already_authorized = hunt.is_user_authorized(request.user)
            if is_already_authorized:
                hunt_authorization_token.delete()
                return render(request, 'frontend/register_token.html', {
                    'error': 'User is already registered to this hunt'
                }, status=400)

            hunt.authorize_user(request.user)
            hunt_authorization_token.delete()

            return render(request, 'frontend/register_token.html', {
                'success': 'Server Registered',
                'hunt_name': hunt.name
            })
        except Exception as ex:
            log.exception('Failed to register token')
            return render(request, 'frontend/register_token.html', {
                'error': 'Invalid token'
            }, status=400)


class HuntView(LoginRequiredMixin, generic.View):
    def get(self, request, hunt_id):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            hunt = AuthorizedUsers.objects.get(user=request.user, hunt__id=hunt_id).hunt
            store_items = Item.objects.filter(type=Item.TYPE_PRIZE, hunt__id=hunt_id)
            players = Player.objects.filter(hunt__id=hunt_id)

            request.breadcrumbs.append({
                'name': hunt.name,
            })
            return render(request, 'frontend/view_hunt.html', {
                'hunt': hunt,
                'store_items': store_items,
                'players': players
            })
        except AuthorizedUsers.DoesNotExist:
            log.warning('Attempt to access unauthorized hunt. User={} hunt_id={}'.format(request.user.username, hunt_id))
        except Exception as ex:
            log.exception('Failed to view hunt')

        request.breadcrumbs = []
        return render(request, 'frontend/view_hunt.html', {
            'error': 'Server Error'
        }, status=403)

# TODO: Test to make sure we're only getting transactions for this item's hunt
class ItemView(LoginRequiredMixin, generic.View):
    def get(self, request, hunt_id, item_id):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            hunt = AuthorizedUsers.objects.get(user=request.user, hunt__id=hunt_id).hunt
            item = Item.objects.get(pk=item_id, hunt__id=hunt_id)
            transactions = Transaction.objects.filter(item=item, hunt=hunt).select_related('player')

            request.breadcrumbs.append({
                'name': hunt,
                'path': reverse('frontend:view_hunt', kwargs={'hunt_id': hunt_id})
            })
            request.breadcrumbs.append({
                'name': item,
            })
            return render(request, 'frontend/view_item.html', {
                'item': item,
                'transactions': transactions
            })
        except AuthorizedUsers.DoesNotExist:
            log.warning('Attempt to access unauthorized hunt. User={} hunt_id={} item_id={}'.format(request.user.username, hunt_id, item_id))
        except Item.DoesNotExist:
            log.warning('Attempt to access unauthorized item. User={} hunt_id={} item_id={}'.format(request.user.username, hunt_id, item_id))
        except Exception as ex:
            log.exception('Failed to view item')

        request.breadcrumbs = []
        return render(request, 'frontend/view_item.html', {
            'error': 'Server Error'
        }, status=403)


# TODO: Test to make sure we're only getting transactions for this player's hunt
class PlayerView(LoginRequiredMixin, generic.View):
    def get(self, request, hunt_id, player_id):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            hunt = AuthorizedUsers.objects.get(user=request.user, hunt__id=hunt_id).hunt
            player = Player.objects.get(pk=player_id, hunt__id=hunt_id)
            transactions = Transaction.objects.filter(player=player, hunt=hunt).select_related('region')
            total_points = player.get_total_points(hunt)
            items_purchased = [transaction for transaction in transactions if transaction.item.type == Item.TYPE_PRIZE and transaction.player == player]
            items_found = [transaction for transaction in transactions if transaction.item.type == Item.TYPE_CREDIT and transaction.player == player]

            request.breadcrumbs.append({
                'name': hunt,
                'path': reverse('frontend:view_hunt', kwargs={'hunt_id': hunt_id})
            })
            request.breadcrumbs.append({
                'name': player,
            })
            return render(request, 'frontend/view_player.html', {
                'player': player,
                'total_points': total_points,
                'items_found': len(items_found),
                'items_purchased': len(items_purchased),
                'transactions': transactions
            })

        except AuthorizedUsers.DoesNotExist:
            log.warning('Attempt to access unauthorized hunt. User={} hunt_id={} player_id={}'.format(request.user.username, hunt_id, player_id))
        except Player.DoesNotExist:
            log.warning('Attempt to access unauthorized player. User={} hunt_id={} player_id={}'.format(request.user.username, hunt_id, player_id))
        except Exception as ex:
            log.exception('Failed to view item')

        request.breadcrumbs = []
        return render(request, 'frontend/view_player.html', {
            'error': 'Server Error'
        }, status=403)
