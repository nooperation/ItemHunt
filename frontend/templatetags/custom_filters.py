from django import template
from datetime import date, timedelta

from django.utils import html

register = template.Library()


def make_location_link_safe(region_name, x, y, z):
    region_name_safe = html.escape(region_name)
    x_safe = int(x)
    y_safe = int(y)
    z_safe = int(z)
    return '<a href="secondlife://{}/{}/{}/{}">{}</a>'.format(
        region_name_safe,
        x_safe,
        y_safe,
        z_safe,
        region_name_safe
    )


@register.filter(name='player_points')
def player_points(player, hunt):
    return player.get_total_points(hunt)


@register.filter(name='item_location')
def item_location(item):
    return make_location_link_safe(
        item.region.name,
        item.position_x,
        item.position_y,
        item.position_z,
    )


@register.filter(name='transaction_location')
def transaction_location(transaction):
    return make_location_link_safe(
        transaction.region.name,
        transaction.player_x,
        transaction.player_y,
        transaction.player_z,
    )


@register.filter(name='transaction_item_location')
def transaction_location(transaction):
    return make_location_link_safe(
        transaction.region.name,
        transaction.item_x,
        transaction.item_y,
        transaction.item_z,
    )
