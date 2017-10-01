from django.core.urlresolvers import reverse
from django.test import TestCase

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


class GetTotalPointsView(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name='FirstRegion')
        self.hunt = Hunt.objects.create(
            name='First hunt',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.object_key = 'e88b0760-1316-8ca2-f4cc-48d7a807a448'
        self.object_name = 'Test object'
        self.position_x = 5
        self.position_y = 6
        self.position_z = 7

    def post_with_metadata(self, address, params):
        return self.client.post(
            address,
            params,
            HTTP_X_SECONDLIFE_LOCAL_POSITION=f'({self.position_x}, {self.position_y}, {self.position_z})',
            HTTP_X_SECONDLIFE_REGION='{region_name} (123, 456)'.format(region_name=self.region.name),
            HTTP_X_SECONDLIFE_OWNER_NAME='Owner Name',
            HTTP_X_SECONDLIFE_OBJECT_NAME=self.object_name,
            HTTP_X_SECONDLIFE_OBJECT_KEY=self.object_key,
            HTTP_X_SECONDLIFE_OWNER_KEY='b553381f-9c6a-a51d-4037-186c9d0f7413',
            HTTP_X_SECONDLIFE_SHARD='Secondlife'
        )

    def test_normal_credit(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            points=10,
            type=Item.TYPE_CREDIT
        )

        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))

        first_item = Item.objects.first()
        self.assertEquals(first_item.uuid, self.object_key)
        self.assertEquals(first_item.name, self.object_name)
        self.assertEquals(first_item.type, server_data['type'])
        self.assertEquals(first_item.position_x, self.position_x)
        self.assertEquals(first_item.position_y, self.position_y)
        self.assertEquals(first_item.position_z, self.position_z)
        self.assertEquals(first_item.points, server_data['points'])
        self.assertEquals(first_item.enabled, True)
        self.assertEquals(first_item.hunt, self.hunt)
        self.assertEquals(first_item.region, self.region)

    def test_normal_prize(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            points=10,
            type=Item.TYPE_PRIZE,
        )

        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))

        first_item = Item.objects.first()
        self.assertEquals(first_item.uuid, self.object_key)
        self.assertEquals(first_item.name, self.object_name)
        self.assertEquals(first_item.type, server_data['type'])
        self.assertEquals(first_item.position_x, self.position_x)
        self.assertEquals(first_item.position_y, self.position_y)
        self.assertEquals(first_item.position_z, self.position_z)
        self.assertEquals(first_item.points, server_data['points'])
        self.assertEquals(first_item.enabled, True)
        self.assertEquals(first_item.hunt, self.hunt)
        self.assertEquals(first_item.region, self.region)

    def test_new_region(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            points=10,
            type=Item.TYPE_CREDIT
        )

        self.region.name = 'NewRegion'
        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))

        new_region = Region.objects.get(name=self.region.name)
        self.assertEquals(new_region.name, self.region.name)

        first_item = Item.objects.first()
        self.assertEquals(first_item.uuid, self.object_key)
        self.assertEquals(first_item.name, self.object_name)
        self.assertEquals(first_item.hunt, self.hunt)
        self.assertEquals(first_item.region, new_region)

    def test_invalid_region(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            points=10,
            type=Item.TYPE_CREDIT
        )

        self.region.name = 'a'*300
        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

        self.region.name = ''
        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

    def test_invalid_private_token(self):
        server_data = dict(
            private_token='InvalidPrivateToken',
            points=10,
            type=Item.TYPE_CREDIT
        )

        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

    def test_missing_private_token(self):
        server_data = dict()
        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

    def test_properties_changed(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            points=10,
            type=Item.TYPE_CREDIT
        )
        self.post_with_metadata(reverse('server:register_item'), server_data)

        server_data['points'] = 100
        server_data['type'] = Item.TYPE_PRIZE
        self.region.name = 'UpdatedRegion'
        self.object_name = 'Updated object'
        self.position_x = 105
        self.position_y = 106
        self.position_z = 107

        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))

        first_item = Item.objects.first()
        self.assertEquals(first_item.uuid, self.object_key)
        self.assertEquals(first_item.name, self.object_name)
        self.assertEquals(first_item.type, server_data['type'])
        self.assertEquals(first_item.position_x, self.position_x)
        self.assertEquals(first_item.position_y, self.position_y)
        self.assertEquals(first_item.position_z, self.position_z)
        self.assertEquals(first_item.points, server_data['points'])
        self.assertEquals(first_item.enabled, True)
        self.assertEquals(first_item.hunt, self.hunt)
        self.assertEquals(first_item.region.name, self.region.name)

    def test_negative_points_credit(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            points=-10,
            type=Item.TYPE_CREDIT
        )

        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

    def test_negative_points_prize(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            points=-10,
            type=Item.TYPE_PRIZE
        )

        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))

    def test_zero_points_prize(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            points=0,
            type=Item.TYPE_PRIZE
        )

        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))

    def test_zero_points_credit(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            points=0,
            type=Item.TYPE_CREDIT
        )

        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))

    def test_disabled_hunt(self):
        server_data = dict(
            private_token=self.hunt.private_token,
            points=10,
            type=Item.TYPE_PRIZE,
        )

        self.hunt.enabled = False
        self.hunt.save()

        response = self.post_with_metadata(reverse('server:register_item'), server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))
