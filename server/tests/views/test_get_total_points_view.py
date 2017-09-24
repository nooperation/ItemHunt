import requests
from django.test import LiveServerTestCase
from django.test import TransactionTestCase, TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from ...models import *
from ...views import JSON_RESULT_ERROR
from ...views import JSON_RESULT_SUCCESS
from ...views import JSON_TAG_RESULT
from ...views import JSON_TAG_MESSAGE


def is_json_success(result_json):
    return JSON_TAG_RESULT in result_json and result_json[JSON_TAG_RESULT] == JSON_RESULT_SUCCESS


def is_json_error(result_json):
    return JSON_TAG_RESULT in result_json and result_json[JSON_TAG_RESULT] == JSON_RESULT_ERROR


class GetTotalPointsView(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name='First Region')
        self.hunt = Hunt.objects.create(
            name='First hunt',
            public_token='aduosJYPT1bU4tS3YvkIeN_D04ppO2Gk0eByAYQkZqMd',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.first_player = Player.objects.create(
            uuid='41f94400-2a3e-408a-9b80-1774724f62af',
            name='First Agent'
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
            hunt=self.hunt
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
            player_name=self.first_player.name,
            player_uuid=self.first_player.uuid,
        )

        response = self.post_with_metadata(reverse('server:activate_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(response.json()['total_points'], self.first_transaction.points)

    def test_unknown_user(self):
        server_data = dict(
            player_name='Unknown user',
            player_uuid='00000000-4444-2222-0000-AAAAAAAAAAAA',
        )

        response = self.post_with_metadata(reverse('server:activate_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(response.json()['total_points'], 0)

    def test_invalid_player_name(self):
        server_data = dict(
            player_name='Unknown user',
            player_uuid='00000000-4444-2222-0000-AAAAAAAAAAAA',
        )

        server_data['player_name'] = None
        response = self.post_with_metadata(reverse('server:activate_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        server_data['player_name'] = 'a'*300
        response = self.post_with_metadata(reverse('server:activate_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

    def test_invalid_player_uuid(self):
        server_data = dict(
            player_name='Unknown user',
            player_uuid='00000000-4444-2222-0000-AAAAAAAAAAAA',
        )

        server_data['player_uuid'] = None
        response = self.post_with_metadata(reverse('server:activate_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        server_data['player_uuid'] = 'a' * 300
        response = self.post_with_metadata(reverse('server:activate_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))
