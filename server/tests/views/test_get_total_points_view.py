import requests
from django.test import LiveServerTestCase
from django.test import TransactionTestCase, TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from ...models import *
from ...views import *


def is_json_success(result_json):
    return JSON_TAG_RESULT in result_json and result_json[JSON_TAG_RESULT] == JSON_RESULT_SUCCESS


def is_json_error(result_json):
    return JSON_TAG_RESULT in result_json and result_json[JSON_TAG_RESULT] == JSON_RESULT_ERROR


class GetTotalPointsView(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name='FirstRegion')
        self.hunt = Hunt.objects.create(
            name='First hunt',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.first_player = Player.objects.create(
            uuid='41f94400-2a3e-408a-9b80-1774724f62af',
            name='First Agent'
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
        self.first_transaction = Transaction.objects.create(
            points=15,
            player_x=0.0,
            player_y=25.0,
            player_z=50.0,
            item_x=75.0,
            item_y=100.0,
            item_z=125.0,
            player=self.first_player,
            region=self.region,
            hunt=self.hunt,
            item=self.item_prizeA
        )

    def post_with_metadata(self, address, params):
        return self.client.post(
            address,
            params,
            HTTP_X_SECONDLIFE_LOCAL_POSITION='(5, 6, 7)',
            HTTP_X_SECONDLIFE_REGION='{region_name} (123, 456)'.format(region_name=self.region.name),
            HTTP_X_SECONDLIFE_OWNER_NAME='Owner Name',
            HTTP_X_SECONDLIFE_OBJECT_NAME='does not matter',
            HTTP_X_SECONDLIFE_OBJECT_KEY='AAAAAAAA-AAAA-AAAA-AAAA-BBBBBBBBBBBB',
            HTTP_X_SECONDLIFE_OWNER_KEY='AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',
            HTTP_X_SECONDLIFE_SHARD='Secondlife'
        )

    def test_known_user(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            player_uuid=self.first_player.uuid,
        )

        response = self.post_with_metadata(reverse('server:get_total_points'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(response.json()['payload']['total_points'], self.first_transaction.points)
        self.assertEquals(response.json()[JSON_TAG_TARGET_UUID], server_data['player_uuid'])

    def test_unknown_user(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            player_uuid='00000000-4444-2222-0000-AAAAAAAAAAAA',
        )

        response = self.post_with_metadata(reverse('server:get_total_points'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(response.json()['payload']['total_points'], 0)
        self.assertEquals(response.json()[JSON_TAG_TARGET_UUID], server_data['player_uuid'])

    def test_invalid_player_uuid(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            player_uuid='00000000-4444-2222-0000-AAAAAAAAAAAA',
        )

        server_data['player_uuid'] = None
        response = self.post_with_metadata(reverse('server:get_total_points'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        server_data['player_uuid'] = 'a' * 300
        response = self.post_with_metadata(reverse('server:get_total_points'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))
