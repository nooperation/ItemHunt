import requests
from django.test import LiveServerTestCase
from django.test import TransactionTestCase, TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import copy

from ...models import *
from ...views import JSON_RESULT_ERROR
from ...views import JSON_RESULT_SUCCESS
from ...views import JSON_TAG_RESULT


def is_json_success(result_json):
    return JSON_TAG_RESULT in result_json and result_json[JSON_TAG_RESULT] == JSON_RESULT_SUCCESS


def is_json_error(result_json):
    return JSON_TAG_RESULT in result_json and result_json[JSON_TAG_RESULT] == JSON_RESULT_ERROR


def post_with_metadata(client, address, server, params):
    return client.post(address,
                       params,
                       HTTP_X_SECONDLIFE_LOCAL_POSITION='({x}, {y}, {z})'.format(x=server.position_x,
                                                                                 y=server.position_y,
                                                                                 z=server.position_z),
                       HTTP_X_SECONDLIFE_REGION='{region_name} (123, 456)'.format(region_name=server.region.name),
                       HTTP_X_SECONDLIFE_OWNER_NAME='Owner Name',
                       HTTP_X_SECONDLIFE_OBJECT_NAME=server.object_name,
                       HTTP_X_SECONDLIFE_OBJECT_KEY=server.object_key,
                       HTTP_X_SECONDLIFE_OWNER_KEY=server.owner.uuid,
                       HTTP_X_SECONDLIFE_SHARD=server.shard)


class ActivateItemView(TestCase):
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
        self.item_creditA = Item.objects.create(
            uuid='11111111-1111-1111-1111-111111111111',
            name='First Credit (15pts)',
            type=Item.TYPE_CREDIT,
            position_x=45.00,
            position_y=80.00,
            position_z=125.00,
            points=15,
            enabled=True,
            region=self.region,
            hunt=self.hunt
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
        self.server_data = dict(
            private_token=self.hunt.private_token,
            player_name=self.first_player.name,
            player_uuid=self.first_player.uuid,
            player_x=42.16,
            player_y=97.23,
            player_z=112.73,
            points=self.item_creditA.points
        )

    def post_with_metadata(self, address, item, params):
        return self.client.post(
            address,
            params,
            HTTP_X_SECONDLIFE_LOCAL_POSITION='({x}, {y}, {z})'.format(x=item.position_x, y=item.position_y,
                                                                      z=item.position_z),
            HTTP_X_SECONDLIFE_REGION='{region_name} (123, 456)'.format(region_name=self.region.name),
            HTTP_X_SECONDLIFE_OWNER_NAME='Owner Name',
            HTTP_X_SECONDLIFE_OBJECT_NAME=item.name,
            HTTP_X_SECONDLIFE_OBJECT_KEY=item.uuid,
            HTTP_X_SECONDLIFE_OWNER_KEY='AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',
            HTTP_X_SECONDLIFE_SHARD='Secondlife'
        )

    def test_activate_credit(self):
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(Transaction.objects.count(), 1)

        transaction = Transaction.objects.first()
        self.assertEquals(transaction.points, self.server_data['points'])
        self.assertEquals(transaction.player_x, self.server_data['player_x'])
        self.assertEquals(transaction.player_y, self.server_data['player_y'])
        self.assertEquals(transaction.player_z, self.server_data['player_z'])
        self.assertEquals(transaction.item_x, self.item_creditA.position_x)
        self.assertEquals(transaction.item_y, self.item_creditA.position_y)
        self.assertEquals(transaction.item_z, self.item_creditA.position_z)
        self.assertEquals(transaction.player, self.first_player)
        self.assertEquals(transaction.region, self.region)
        self.assertEquals(transaction.hunt, self.hunt)

        self.assertEquals(self.first_player.get_total_points(self.hunt), self.server_data['points'])

    def test_multiple_activate_credit(self):
        self.server_data['points'] = 15
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(self.first_player.get_total_points(self.hunt), 15)

        second_credit = Item.objects.create(
            uuid='BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',
            name='Second Credit (35pts)',
            type=Item.TYPE_CREDIT,
            position_x=45.00,
            position_y=80.00,
            position_z=125.00,
            points=15,
            enabled=True,
            region=self.region,
            hunt=self.hunt
        )

        self.server_data['points'] = 35
        response = self.post_with_metadata(reverse('server:activate_item'), second_credit, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(self.first_player.get_total_points(self.hunt), 15 + 35)

    def test_double_activate_credit(self):
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(Transaction.objects.count(), 1)

        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))
        self.assertEquals(Transaction.objects.count(), 1)

        self.assertEquals(self.first_player.get_total_points(self.hunt), self.server_data['points'])

    def test_activate_new_region(self):
        self.server_data['points'] = 100
        self.region.name = 'New_Region'
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(self.first_player.get_total_points(self.hunt), 100)

        self.assertEquals(Region.objects.get(name=self.region.name).name, self.region.name)

    def test_activate_invalid_region(self):
        self.server_data['points'] = 100

        self.region.name = 'a'*300
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.region.name = ''
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.assertEquals(self.first_player.get_total_points(self.hunt), 0)

    def test_activate_new_item(self):
        self.server_data['points'] = 100
        self.item_creditA.uuid = 'FFFFEEEE-FAFA-AFAF-BABA-CAAAAAAAAAAA'
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.assertEquals(self.first_player.get_total_points(self.hunt), 0)

    def test_activate_invalid_item(self):
        self.server_data['points'] = 100

        self.item_creditA.uuid = None
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.item_creditA.uuid = 'a'*100
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.assertEquals(self.first_player.get_total_points(self.hunt), 0)

    def test_activate_new_player(self):
        self.server_data['player_name'] = 'New Player'
        self.server_data['player_uuid'] = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))

        new_player = Player.objects.get(uuid=self.server_data['player_uuid'])
        self.assertEquals(new_player.name, self.server_data['player_name'])
        self.assertEquals(new_player.uuid, self.server_data['player_uuid'])
        self.assertEquals(new_player.get_total_points(self.hunt), self.server_data['points'])

    def test_activate_prize(self):
        self.server_data['points'] = 100
        self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)

        self.server_data['points'] = 25
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_prizeA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(self.first_player.get_total_points(self.hunt), 75)

    def test_activate_prize_too_expensive(self):
        self.server_data['points'] = 15
        self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)

        self.server_data['points'] = 25
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_prizeA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.assertEquals(self.first_player.get_total_points(self.hunt), 15)

    def test_activate_invalid_hunt_token(self):
        self.server_data['points'] = 15
        self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)

        self.hunt.private_token = 'a' * 32
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.hunt.private_token = None
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.assertEquals(self.first_player.get_total_points(self.hunt), 15)

    def test_activate_invalid_hunt_name(self):
        self.server_data['points'] = 15
        self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)

        self.hunt.name = 'new hunt name'
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.hunt.name = None
        response = self.post_with_metadata(reverse('server:activate_item'), self.item_creditA, self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.assertEquals(self.first_player.get_total_points(self.hunt), 15)
