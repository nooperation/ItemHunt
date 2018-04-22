from collections import ChainMap

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import render, redirect
from django import template

# Create your views here.
from django.urls import reverse
from django.views import generic
from server.models import Hunt, HuntAuthorizationToken, AuthorizedUsers, Item, Transaction, Player, Region
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
            prize_count = Item.objects.filter(type=Item.TYPE_PRIZE, hunt=hunt).count()
            item_count = Item.objects.filter(type=Item.TYPE_CREDIT, hunt=hunt).count()
            player_count = Transaction.objects.filter(hunt=hunt).values('player').distinct().count()
            region_count = Transaction.objects.filter(hunt=hunt).values('region__name').distinct().count()

            request.breadcrumbs.append({
                'name': hunt.name,
            })
            return render(request, 'frontend/view_hunt.html', {
                'hunt': hunt,
                'prize_count': prize_count,
                'item_count': item_count,
                'player_count': player_count,
                'region_count': region_count
            })
        except AuthorizedUsers.DoesNotExist:
            log.warning('Attempt to access unauthorized hunt. User={} hunt_id={}'.format(request.user.username, hunt_id))
        except Exception as ex:
            log.exception('Failed to view hunt')

        return render(request, 'frontend/view_hunt.html', {
            'error': 'Server Error'
        }, status=403)


class HuntRegionsView(LoginRequiredMixin, generic.View):
    def get(self, request, hunt_id):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            region_stats = []

            hunt = AuthorizedUsers.objects.get(user=request.user, hunt__id=hunt_id).hunt
            regions = Region.objects.all()
            for region in regions:
                prize_count = Item.objects.filter(type=Item.TYPE_PRIZE, hunt=hunt, region=region).count()
                item_count = Item.objects.filter(type=Item.TYPE_CREDIT, hunt=hunt, region=region).count()
                region_stats.append({'region': region, 'hunt': hunt, 'prize_count': prize_count, 'item_count': item_count})

            request.breadcrumbs.append({
                'name': hunt.name,
                'path': reverse('frontend:view_hunt', kwargs={'hunt_id': hunt.id})
            })
            request.breadcrumbs.append({
                'name': 'Regions',
            })
            return render(request, 'frontend/view_hunt_regions.html', {
                'hunt': hunt,
                'region_stats': region_stats,
            })
        except AuthorizedUsers.DoesNotExist:
            log.warning('Attempt to access unauthorized hunt. User={} hunt_id={}'.format(request.user.username, hunt_id))
        except Exception as ex:
            log.exception('Failed to view hunt')

        return render(request, 'frontend/view_hunt.html', {
            'error': 'Server Error'
        }, status=403)


class RegionItemsView(LoginRequiredMixin, generic.View):
    def get(self, request, hunt_id, region_id):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            region = Region.objects.get(id=region_id)
            hunt = AuthorizedUsers.objects.get(user=request.user, hunt__id=hunt_id).hunt
            hunt_items = Item.objects.filter(type=Item.TYPE_CREDIT, hunt=hunt, region=region)

            transactions = Transaction.objects.filter(hunt=hunt, region=region).values('item_id').annotate(Count('item_id'))
            transactions = [{item['item_id']: item['item_id__count']} for item in transactions]
            transactions = ChainMap(*transactions)

            request.breadcrumbs.append({
                'name': hunt.name,
                'path': reverse('frontend:view_hunt', kwargs={'hunt_id': hunt.id})
            })
            request.breadcrumbs.append({
                'name': 'Regions',
                'path': reverse('frontend:view_hunt_regions', kwargs={'hunt_id': hunt.id})
            })
            request.breadcrumbs.append({
                'name': region.name + ' Items',
            })
            return render(request, 'frontend/view_hunt_items.html', {
                'hunt': hunt,
                'hunt_items': hunt_items,
                'transactions': transactions,
            })
        except AuthorizedUsers.DoesNotExist:
            log.warning(
                'Attempt to access unauthorized hunt. User={} hunt_id={}'.format(request.user.username, hunt_id))
        except Exception as ex:
            log.exception('Failed to view hunt')

        return render(request, 'frontend/view_hunt.html', {
            'error': 'Server Error'
        }, status=403)


class RegionPrizesView(LoginRequiredMixin, generic.View):
    def get(self, request, hunt_id, region_id):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            region = Region.objects.get(id=region_id)
            hunt = AuthorizedUsers.objects.get(user=request.user, hunt__id=hunt_id).hunt
            store_items = Item.objects.filter(type=Item.TYPE_PRIZE, hunt=hunt, region=region)

            transactions = Transaction.objects.filter(hunt=hunt, region=region).values('item_id').annotate(Count('item_id'))
            transactions = [{item['item_id']: item['item_id__count']} for item in transactions]
            transactions = ChainMap(*transactions)

            request.breadcrumbs.append({
                'name': hunt.name,
                'path': reverse('frontend:view_hunt', kwargs={'hunt_id': hunt.id})
            })
            request.breadcrumbs.append({
                'name': 'Regions',
                'path': reverse('frontend:view_hunt_regions', kwargs={'hunt_id': hunt.id})
            })
            request.breadcrumbs.append({
                'name': region.name + ' Prizes',
            })
            return render(request, 'frontend/view_hunt_prizes.html', {
                'hunt': hunt,
                'store_items': store_items,
                'transactions': transactions,
            })
        except AuthorizedUsers.DoesNotExist:
            log.warning(
                'Attempt to access unauthorized hunt. User={} hunt_id={}'.format(request.user.username, hunt_id))
        except Exception as ex:
            log.exception('Failed to view hunt')

        return render(request, 'frontend/view_hunt_prizes.html', {
            'error': 'Server Error'
        }, status=403)


class HuntItemsView(LoginRequiredMixin, generic.View):
    def get(self, request, hunt_id):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            hunt = AuthorizedUsers.objects.get(user=request.user, hunt__id=hunt_id).hunt
            hunt_items = Item.objects.filter(type=Item.TYPE_CREDIT, hunt=hunt)

            transactions = Transaction.objects.filter(hunt=hunt).values('item_id').annotate(Count('item_id'))
            transactions = [{item['item_id']: item['item_id__count']} for item in transactions]
            transactions = ChainMap(*transactions)

            request.breadcrumbs.append({
                'name': hunt.name,
                'path': reverse('frontend:view_hunt', kwargs={'hunt_id': hunt.id})
            })
            request.breadcrumbs.append({
                'name': 'Items',
            })
            return render(request, 'frontend/view_hunt_items.html', {
                'hunt': hunt,
                'hunt_items': hunt_items,
                'transactions': transactions,
            })
        except AuthorizedUsers.DoesNotExist:
            log.warning(
                'Attempt to access unauthorized hunt. User={} hunt_id={}'.format(request.user.username, hunt_id))
        except Exception as ex:
            log.exception('Failed to view hunt')

        return render(request, 'frontend/view_hunt_items.html', {
            'error': 'Server Error'
        }, status=403)


class HuntPrizesView(LoginRequiredMixin, generic.View):
    def get(self, request, hunt_id):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            hunt = AuthorizedUsers.objects.get(user=request.user, hunt__id=hunt_id).hunt
            store_items = Item.objects.filter(type=Item.TYPE_PRIZE, hunt=hunt)

            transactions = Transaction.objects.filter(hunt=hunt).values('item_id').annotate(Count('item_id'))
            transactions = [{item['item_id']: item['item_id__count']} for item in transactions]
            transactions = ChainMap(*transactions)

            request.breadcrumbs.append({
                'name': hunt.name,
                'path': reverse('frontend:view_hunt', kwargs={'hunt_id': hunt.id})
            })
            request.breadcrumbs.append({
                'name': 'Prizes',
            })
            return render(request, 'frontend/view_hunt_prizes.html', {
                'hunt': hunt,
                'store_items': store_items,
                'transactions': transactions,
            })
        except AuthorizedUsers.DoesNotExist:
            log.warning(
                'Attempt to access unauthorized hunt. User={} hunt_id={}'.format(request.user.username, hunt_id))
        except Exception as ex:
            log.exception('Failed to view hunt')

        return render(request, 'frontend/view_hunt_prizes.html', {
            'error': 'Server Error'
        }, status=403)


class HuntPlayersView(LoginRequiredMixin, generic.View):
    def get(self, request, hunt_id):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            hunt = AuthorizedUsers.objects.get(user=request.user, hunt__id=hunt_id).hunt
            players = Player.objects.filter(hunt=hunt)

            request.breadcrumbs.append({
                'name': hunt.name,
                'path': reverse('frontend:view_hunt', kwargs={'hunt_id': hunt.id})
            })
            request.breadcrumbs.append({
                'name': 'Players',
            })
            return render(request, 'frontend/view_hunt_players.html', {
                'hunt': hunt,
                'players': players
            })
        except AuthorizedUsers.DoesNotExist:
            log.warning(
                'Attempt to access unauthorized hunt. User={} hunt_id={}'.format(request.user.username, hunt_id))
        except Exception as ex:
            log.exception('Failed to view hunt')

        return render(request, 'frontend/view_hunt_players.html', {
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
            item = Item.objects.get(pk=item_id, hunt=hunt)
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
            player = Player.objects.get(pk=player_id)
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


class GenerateTokenView(LoginRequiredMixin, generic.View):
    def get(self, request, hunt_id):
        request.breadcrumbs = [{
            'name': 'Home',
            'path': reverse('frontend:index', kwargs={})
        }]

        try:
            hunt = AuthorizedUsers.objects.get(user=request.user, hunt__id=hunt_id).hunt
            token = hunt.create_hunt_auth_token()

            request.breadcrumbs.append({
                'name': hunt,
                'path': reverse('frontend:view_hunt', kwargs={'hunt_id': hunt_id})
            })
            request.breadcrumbs.append({
                'name': 'Generate Token',
            })
            return render(request, 'frontend/generate_token.html', {
                'hunt': hunt,
                'token': token.token
            })
        except AuthorizedUsers.DoesNotExist:
            log.warning('Attempt to generate token for unauthorized hunt. User={} hunt_id={}'.format(request.user.username, hunt_id))
        except Exception as ex:
            log.exception('Failed to generate token')

        return render(request, 'frontend/view_hunt.html', {
            'error': 'Server Error'
        }, status=403)
