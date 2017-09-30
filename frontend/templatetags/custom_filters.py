from django import template
from datetime import date, timedelta

register = template.Library()


@register.filter(name='player_points')
def player_points(player, hunt):
    return player.get_total_points(hunt)
