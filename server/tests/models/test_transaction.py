from django.test import TransactionTestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from server.models import *


class TransactionTests(TransactionTestCase):
    def setUp(self):
        self.region = Region.objects.create(
            name='First Region'
        )
        self.hunt = Hunt.objects.create(
            name='First hunt',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.player = Player.objects.create(
            name='First Player',
            uuid='41f94400-2a3e-408a-9b80-1774724f62af'
        )
        self.item_prizeA = Item.objects.create(
            uuid='33333333-3333-3333-3333-333333333333',
            name='First Prize (cost: 10pts)',
            type=Item.TYPE_PRIZE,
            position_x=5.00,
            position_y=110.00,
            position_z=35.00,
            points=10,
            enabled=True,
            region=self.region,
            hunt=self.hunt
        )
        self.transaction = Transaction.objects.create(
            points=15,
            player_x=0.0,
            player_y=25.0,
            player_z=50.0,
            item_x=75.0,
            item_y=100.0,
            item_z=125.0,
            player=self.player,
            region=self.region,
            hunt=self.hunt,
            item=self.item_prizeA
        )

    def test_normal_creation(self):
        self.transaction.full_clean()
