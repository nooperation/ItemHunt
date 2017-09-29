from django.db import models
from django.db.models import Sum
from django.core.validators import RegexValidator, MinLengthValidator, MinValueValidator
from django.contrib.auth.models import User
import os
import base64
from datetime import datetime, timedelta, timezone
import logging


def generate_token():
    token = None
    for i in range(0, 1000):
        token = base64.urlsafe_b64encode(os.urandom(33)).decode('utf-8')
        if Hunt.objects.filter(private_token=token).count() != 0:
            token = None
        elif HuntAuthorizationToken.objects.filter(token=token).count() != 0:
            token = None
        else:
            break
    if token is None:
        raise Exception('Unable to generate token')
    return token


class Hunt(models.Model):
    def __str__(self):
        return self.name

    def regenerate_private_token(self):
        self.private_token = generate_token()

    name = models.CharField(max_length=255, unique=True)
    private_token = models.CharField(max_length=64, unique=True, validators=[MinLengthValidator(8)], default=generate_token)
    enabled = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


class HuntAuthorizationToken(models.Model):
    MAX_TOKEN_AGE = 60 * 5

    def __str__(self):
        return self.hunt.name

    def is_expired(self):
        time_since_creation = (datetime.now(timezone.utc) - self.created_on).seconds
        if time_since_creation > self.MAX_TOKEN_AGE:
            return True
        return False

    @staticmethod
    def delete_all_expired():
        try:
            expiration_date = datetime.now(timezone.utc) - timedelta(seconds=HuntAuthorizationToken.MAX_TOKEN_AGE)
            expired_tokens = HuntAuthorizationToken.objects.filter(created_on__lte=expiration_date)
            expired_tokens.delete()
            logging.error('butts')
        except Exception as ex:
            logging.exception('Failed to delete all expired', ex)

    token = models.CharField(max_length=64, unique=True, validators=[MinLengthValidator(8)], default=generate_token)
    hunt = models.ForeignKey(Hunt, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)


class AuthorizedUsers(models.Model):
    def __str__(self):
        return self.user.name

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hunt = models.ForeignKey(Hunt, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)


class Region(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField(max_length=255, unique=True)


class Player(models.Model):
    def __str__(self):
        return self.name

    def get_total_points(self, hunt):
        total_points = Transaction.objects.filter(player=self, hunt=hunt).aggregate(total_points=Sum('points'))['total_points']
        if total_points is None:
            return 0
        return total_points

    uuid = models.CharField(max_length=36, unique=True, validators=[
        RegexValidator(
            regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
            message='Invalid UUID',
            code='invalid_uuid'
        ),
    ])
    name = models.CharField(max_length=64, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)


class Item(models.Model):
    def __str__(self):
        return self.name

    TYPE_CREDIT = 0
    TYPE_PRIZE = 1
    SERVER_TYPE_CHOICES = (
        (TYPE_CREDIT, 'Credit'),
        (TYPE_PRIZE, 'Prize'),
    )

    uuid = models.CharField(max_length=36, unique=True, validators=[
        RegexValidator(
            regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
            message='Invalid object key',
            code='invalid object key'
        ),
    ])
    name = models.CharField(max_length=255)
    type = models.IntegerField(choices=SERVER_TYPE_CHOICES, default=TYPE_CREDIT)
    position_x = models.FloatField()
    position_y = models.FloatField()
    position_z = models.FloatField()
    # The explicit validator is for SQLite, which normally allows negative PositiveIntegerFields values
    points = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    enabled = models.BooleanField()
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    hunt = models.ForeignKey(Hunt, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


class Transaction(models.Model):
    def __str__(self):
        return '{} - {}'.format(self.created_on.strftime("%Y-%m-%d %H:%M:%S"), self.player.name)

    points = models.IntegerField()
    player_x = models.FloatField()
    player_y = models.FloatField()
    player_z = models.FloatField()
    item_x = models.FloatField()
    item_y = models.FloatField()
    item_z = models.FloatField()
    player = models.ForeignKey(Player, on_delete=models.PROTECT)
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    hunt = models.ForeignKey(Hunt, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True)
