from django.core.urlresolvers import reverse
from django.test import TestCase

from server.models import *


class RegisterTokenViewTests(TestCase):
    def setUp(self):
        self.username = 'test_user'
        self.password = 'test_password'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)

        self.hunt = Hunt.objects.create(
            name='First hunt',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.first_player = Player.objects.create(
            uuid='41f94400-2a3e-408a-9b80-1774724f62af',
            name='First Agent',
            hunt=self.hunt
        )
        self.hunt_token = HuntAuthorizationToken.objects.create(
            hunt=self.hunt,
        )

    def test_successful_register(self):
        server_data = dict(
            token=self.hunt_token.token
        )

        self.assertFalse(self.hunt.is_user_authorized(self.user))
        response = self.client.get(reverse('frontend:register_token', kwargs=server_data))
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.hunt.is_user_authorized(self.user))
        self.assertEquals(HuntAuthorizationToken.objects.all().count(), 0)

    def test_register_not_logged_in(self):
        server_data = dict(
            token=self.hunt_token.token
        )

        self.client.logout()
        response = self.client.get(reverse('frontend:register_token', kwargs=server_data))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('frontend:register_token', kwargs=server_data))
        # Our has not been used it, it must still exist
        self.assertSequenceEqual(HuntAuthorizationToken.objects.all(), [self.hunt_token])

    def test_register_invalid_token(self):
        server_data = dict(
            token='a'*32
        )

        response = self.client.get(reverse('frontend:register_token', kwargs=server_data))
        self.assertEquals(response.status_code, 400)
