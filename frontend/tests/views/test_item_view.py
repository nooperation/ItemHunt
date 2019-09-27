from django.core.urlresolvers import reverse
from django.test import TestCase

from server.models import *


class ItemViewTests(TestCase):
    def setUp(self):
        self.username = 'test_user'
        self.password = 'test_password'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)

        self.region = Region.objects.create(
            name='First Region'
        )
        self.hunt = Hunt.objects.create(
            name='First hunt',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.first_player = Player.objects.create(
            uuid='41f94400-2a3e-408a-9b80-1774724f62af',
            name='First Agent'
        )
        self.hunt_token = AuthorizedUsers.objects.create(
            hunt=self.hunt,
            user=self.user
        )
        self.item = Item.objects.create(
            uuid='41f94400-2a3e-408a-9b80-1774724f62af',
            name='First Item',
            type=Item.TYPE_PRIZE,
            position_x=25.00,
            position_y=50.00,
            position_z=75.00,
            points=15,
            enabled=True,
            region=self.region,
            hunt=self.hunt
        )

    def test_authorized(self):
        server_data = dict(
            hunt_id=self.hunt.id,
            item_id=self.item.id
        )

        response = self.client.get(reverse('frontend:view_item', kwargs=server_data))
        self.assertEquals(response.status_code, 200)

    def test_not_logged_in(self):
        server_data = dict(
            hunt_id=self.hunt.id,
            item_id=self.item.id
        )

        self.client.logout()
        response = self.client.get(reverse('frontend:view_item', kwargs=server_data))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('frontend:view_item', kwargs=server_data))

    def test_unauthorized(self):
        server_data = dict(
            hunt_id=self.hunt.id,
            item_id=self.item.id
        )

        AuthorizedUsers.objects.all().delete()
        response = self.client.get(reverse('frontend:view_item', kwargs=server_data))
        self.assertEquals(response.status_code, 403)

    def test_invalid_hunt(self):
        server_data = dict(
            hunt_id=42,
            item_id=self.item.id
        )

        response = self.client.get(reverse('frontend:view_item', kwargs=server_data))
        self.assertEquals(response.status_code, 403)

    def test_invalid_item(self):
        server_data = dict(
            hunt_id=self.hunt.id,
            item_id=42
        )

        response = self.client.get(reverse('frontend:view_item', kwargs=server_data))
        self.assertEquals(response.status_code, 403)
