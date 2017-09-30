from django.core.urlresolvers import reverse
from django.test import TestCase

from server.models import *


class PlayerViewTests(TestCase):
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
        self.player = Player.objects.create(
            uuid='41f94400-2a3e-408a-9b80-1774724f62af',
            name='First Agent',
            hunt=self.hunt
        )
        self.hunt_token = AuthorizedUsers.objects.create(
            hunt=self.hunt,
            user=self.user
        )
        self.item1 = Item.objects.create(
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
        self.item2 = Item.objects.create(
            uuid='aaaaaaaa-2aaa-408a-aaaa-aaaaaaaaaaaa',
            name='Second Item',
            type=Item.TYPE_CREDIT,
            position_x=125.00,
            position_y=150.00,
            position_z=175.00,
            points=13,
            enabled=True,
            region=self.region,
            hunt=self.hunt
        )
        self.transaction1 = Transaction.objects.create(
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
            item=self.item1
        )
        self.transaction2 = Transaction.objects.create(
            points=13,
            player_x=10.0,
            player_y=125.0,
            player_z=150.0,
            item_x=175.0,
            item_y=1100.0,
            item_z=1125.0,
            player=self.player,
            region=self.region,
            hunt=self.hunt,
            item=self.item2
        )

    def test_authorized(self):
        server_data = dict(
            hunt_id=self.hunt.id,
            player_id=self.player.id
        )

        response = self.client.get(reverse('frontend:view_player', kwargs=server_data))
        self.assertEquals(response.status_code, 200)

    def test_not_logged_in(self):
        server_data = dict(
            hunt_id=self.hunt.id,
            player_id=self.player.id
        )

        self.client.logout()
        response = self.client.get(reverse('frontend:view_player', kwargs=server_data))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('frontend:view_player', kwargs=server_data))

    def test_unauthorized(self):
        server_data = dict(
            hunt_id=self.hunt.id,
            player_id=self.player.id
        )

        AuthorizedUsers.objects.all().delete()
        response = self.client.get(reverse('frontend:view_player', kwargs=server_data))
        self.assertEquals(response.status_code, 403)

    def test_invalid_hunt(self):
        server_data = dict(
            hunt_id=42,
            player_id=self.player.id
        )

        response = self.client.get(reverse('frontend:view_player', kwargs=server_data))
        self.assertEquals(response.status_code, 403)

    def test_invalid_item(self):
        server_data = dict(
            hunt_id=self.hunt.id,
            player_id=42
        )

        response = self.client.get(reverse('frontend:view_player', kwargs=server_data))
        self.assertEquals(response.status_code, 403)
