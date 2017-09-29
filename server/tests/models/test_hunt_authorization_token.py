from django.test import TransactionTestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from server.models import *
from datetime import datetime, timezone, timedelta


class HuntTests(TransactionTestCase):
    def setUp(self):
        self.hunt = Hunt.objects.create(
            name='First hunt',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.hunt_token = HuntAuthorizationToken.objects.create(
            hunt=self.hunt,
        )
        self.expired_date = datetime.now(timezone.utc) - timedelta(seconds=HuntAuthorizationToken.MAX_TOKEN_AGE + 60)

    def test_normal_creation(self):
        self.hunt_token.full_clean()
        self.assertFalse(self.hunt_token.is_expired())
        self.assertTrue(len(self.hunt_token.token) > 8)
        self.assertSequenceEqual(HuntAuthorizationToken.objects.all(), [self.hunt_token])

    def test_expired(self):
        self.hunt_token.created_on = self.expired_date
        self.hunt_token.save()
        self.assertTrue(self.hunt_token.is_expired())
        self.assertSequenceEqual(HuntAuthorizationToken.objects.all(), [self.hunt_token])

    def test_purge_no_expired(self):
        HuntAuthorizationToken.delete_all_expired()
        self.assertSequenceEqual(HuntAuthorizationToken.objects.all(), [self.hunt_token])

    def test_purge_some_expired(self):
        hunt_token_expired = HuntAuthorizationToken.objects.create(
            hunt=self.hunt,
            token='b' * 64,
        )
        hunt_token_expired.created_on = self.expired_date;
        hunt_token_expired.save()
        HuntAuthorizationToken.delete_all_expired()
        self.assertSequenceEqual(HuntAuthorizationToken.objects.all(), [self.hunt_token])

    def test_purge_all_expired(self):
        self.hunt_token.created_on = self.expired_date
        self.hunt_token.save()
        HuntAuthorizationToken.delete_all_expired()
        self.assertSequenceEqual(HuntAuthorizationToken.objects.all(), [])
