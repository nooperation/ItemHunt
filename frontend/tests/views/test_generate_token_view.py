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
        self.hunt_token = AuthorizedUsers.objects.create(
            hunt=self.hunt,
            user=self.user
        )

    def test_authorized(self):
        server_data = dict(
            hunt_id=self.hunt.id
        )

        response = self.client.get(reverse('frontend:generate_token', kwargs=server_data))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(HuntAuthorizationToken.objects.count(), 1)
        token = HuntAuthorizationToken.objects.first()
        self.assertIsNotNone(token)
        self.assertContains(response, token.token)

    def test_not_logged_in(self):
        server_data = dict(
            hunt_id=self.hunt.id
        )

        self.client.logout()
        response = self.client.get(reverse('frontend:generate_token', kwargs=server_data))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('frontend:generate_token', kwargs=server_data))
        self.assertEquals(HuntAuthorizationToken.objects.count(), 0)

    def test_unauthorized(self):
        server_data = dict(
            hunt_id=self.hunt.id
        )

        AuthorizedUsers.objects.all().delete()
        response = self.client.get(reverse('frontend:generate_token', kwargs=server_data))
        self.assertEquals(response.status_code, 403)
        self.assertEquals(HuntAuthorizationToken.objects.count(), 0)

    def test_invalid(self):
        server_data = dict(
            hunt_id=42
        )

        AuthorizedUsers.objects.all().delete()
        response = self.client.get(reverse('frontend:generate_token', kwargs=server_data))
        self.assertEquals(response.status_code, 403)
        self.assertEquals(HuntAuthorizationToken.objects.count(), 0)
