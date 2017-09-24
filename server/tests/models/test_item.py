from django.test import TransactionTestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from server.models import *


class ItemTests(TransactionTestCase):
    def setUp(self):
        self.region = Region.objects.create(name='First Region')
        self.hunt = Hunt.objects.create(
            name='First hunt',
            public_token='aduosJYPT1bU4tS3YvkIeN_D04ppO2Gk0eByAYQkZqMd',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.item = Item.objects.create(
            uuid='41f94400-2a3e-408a-9b80-1774724f62af',
            name='First Item',
            type=Item.TYPE_CREDIT,
            position_x=25.00,
            position_y=50.00,
            position_z=75.00,
            points=15,
            enabled=True,
            region=self.region,
            hunt=self.hunt
        )
        self.second_item = Item(
            uuid='3a208475-b8a7-3dea-fbf0-67c4bfa461af',
            name='Second Item',
            type=Item.TYPE_CREDIT,
            position_x=25.00,
            position_y=50.00,
            position_z=75.00,
            points=15,
            enabled=True,
            region=self.region,
            hunt=self.hunt
        )

    def test_normal_creation(self):
        self.item.full_clean()

    def test_duplicate_creation(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.uuid = '41f94400-2a3e-408a-9b80-1774724f62af',
            self.second_item.full_clean()

    def test_missing_uuid(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.uuid = None
            self.second_item.full_clean()

    def test_invalid_uuid_creation(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.uuid = 'ABCDEFGH-IJKL-MNOP-QRST-UVWXYZ012345'
            self.second_item.full_clean()

    def test_missing_name(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.name = None
            self.second_item.full_clean()

    def test_empty_name(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.name = ''
            self.second_item.full_clean()

    def test_long_name(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.name = 'x' * 256
            self.second_item.full_clean()

    def test_missing_type(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.type = None
            self.second_item.full_clean()

    def test_invalid_type(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.type = 42
            self.second_item.full_clean()

    def test_missing_position_x(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.position_x = None
            self.second_item.full_clean()

    def test_missing_position_y(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.position_y = None
            self.second_item.full_clean()

    def test_missing_position_z(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.position_z = None
            self.second_item.full_clean()

    def test_missing_points(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.points = None
            self.second_item.full_clean()

    def test_missing_enabled(self):
        self.second_item.enabled = None
        self.second_item.full_clean()

    def test_missing_region(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.region = None
            self.second_item.full_clean()

    def test_missing_hunt(self):
        with(self.assertRaises(ValidationError)):
            self.second_item.hunt = None
            self.second_item.full_clean()

