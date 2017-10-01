from django.core.urlresolvers import reverse
from django.test import TestCase

from server.models import *


class TextPurgeExpiredTokensView(TestCase):
    def setUp(self):
        self.hunt = Hunt.objects.create(
            name='First hunt',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.hunt_token = HuntAuthorizationToken.objects.create(
            hunt=self.hunt,
        )
        self.expired_date = datetime.now(timezone.utc) - timedelta(seconds=HuntAuthorizationToken.MAX_TOKEN_AGE + 60)

    def test_expired(self):
        new_auth_token = self.hunt.create_hunt_auth_token()
        self.hunt_token.created_on = self.expired_date
        self.hunt_token.save()

        self.assertTrue(self.hunt_token.is_expired())
        self.assertSequenceEqual(HuntAuthorizationToken.objects.all(), [self.hunt_token, new_auth_token])
        reponse = self.client.get(reverse('server:purge_expired_tokens'))
        self.assertEquals(reponse.status_code, 200)
        self.assertSequenceEqual(HuntAuthorizationToken.objects.all(), [new_auth_token])
