from django.db import models
from django.db.models import Sum
from django.core.validators import RegexValidator, MinLengthValidator
from django.contrib.auth.models import User
import os
import base64

class Hunt(models.Model):
    def __str__(self):
        return self.name

    @staticmethod
    def generate_private_token():
        token = None
        for i in range(0, 10):
            token = base64.urlsafe_b64encode(os.urandom(33)).decode('utf-8')
            if Hunt.objects.filter(private_token=token).count() != 0:
                token = None
            else:
                break
        return token

    @staticmethod
    def generate_public_token():
        token = None
        for i in range(0, 10):
            token = base64.urlsafe_b64encode(os.urandom(33)).decode('utf-8')
            if Hunt.objects.filter(public_token=token).count() != 0:
                token = None
            else:
                break
        return token

    def regenerate_private_token(self):
        self.private_token = self.generate_private_token()

    def regenerate_public_token(self):
        self.public_token = self.generate_public_token()

    name = models.CharField(max_length=255, unique=True)
    public_token = models.CharField(max_length=64, unique=True, validators=[MinLengthValidator(8)])
    private_token = models.CharField(max_length=64, unique=True, validators=[MinLengthValidator(8)])
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


class Region(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField(max_length=255, unique=True)


class Player(models.Model):
    def __str__(self):
        return self.name

    def get_total_points(self, hunt):
        return Transaction.objects.filter(player=self, hunt=hunt).aggregate(total_points=Sum('points'))['total_points']

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
    points = models.IntegerField()
    enabled = models.BooleanField()
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING)
    hunt = models.ForeignKey(Hunt, on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


class Transaction(models.Model):
    def __str__(self):
        return self.created_on

    points = models.IntegerField()
    player_x = models.FloatField()
    player_y = models.FloatField()
    player_z = models.FloatField()
    item_x = models.FloatField()
    item_y = models.FloatField()
    item_z = models.FloatField()
    player = models.ForeignKey(Player, on_delete=models.DO_NOTHING)
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING)
    hunt = models.ForeignKey(Hunt, on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True)
