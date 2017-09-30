from django.test import TransactionTestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from server.models import *


class HuntTests(TransactionTestCase):
    def setUp(self):
        self.hunt = Hunt.objects.create(
            name='First hunt',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.second_hunt = Hunt(
            name='Second hunt',
            private_token='gYNLorTNFI0LtlMZ2DrZqjEMBOTd7jp9eEGPNLg8YVKm'
        )

    def test_normal_creation(self):
        self.hunt.full_clean()
        self.assertTrue(self.hunt.enabled)
        self.assertSequenceEqual(Hunt.objects.all(), [self.hunt])

    def test_duplicate_name(self):
        with(self.assertRaises(ValidationError)):
            self.second_hunt.full_clean()

    def test_duplicate_private_token(self):
        with(self.assertRaises(ValidationError)):
            self.second_hunt.private_token = self.hunt.private_token
            self.second_hunt.full_clean()

    def test_duplicate_private_token(self):
        with(self.assertRaises(ValidationError)):
            self.second_hunt.private_token = None
            self.second_hunt.full_clean()

    def test_empty_private_token(self):
        with(self.assertRaises(ValidationError)):
            self.second_hunt.private_token = ''
            self.second_hunt.full_clean()

    def test_long_private_token(self):
        with(self.assertRaises(ValidationError)):
            self.second_hunt.private_token = 'x' * 65
            self.second_hunt.full_clean()

    def test_duplicate_name(self):
        with(self.assertRaises(ValidationError)):
            self.second_hunt.name = self.hunt.name
            self.second_hunt.full_clean()

    def test_missing_name(self):
        with(self.assertRaises(ValidationError)):
            self.second_hunt.name = None
            self.second_hunt.full_clean()

    def test_empty_name(self):
        with(self.assertRaises(ValidationError)):
            self.second_hunt.name = ''
            self.second_hunt.full_clean()

    def test_long_name(self):
        with(self.assertRaises(ValidationError)):
            self.second_hunt.name = 'x' * 256
            self.second_hunt.full_clean()

    def test_private_key_regeneration(self):
        previous_token = self.second_hunt.private_token
        self.second_hunt.regenerate_private_token()
        self.second_hunt.save()
        self.second_hunt.refresh_from_db()
        self.assertNotEquals(self.second_hunt.private_token, previous_token)

    def test_create_hunt_auth_token(self):
        hunt_auth_token = self.hunt.create_hunt_auth_token()
        self.assertEquals(hunt_auth_token.hunt, self.hunt)
        self.assertEquals(hunt_auth_token, HuntAuthorizationToken.objects.get(token=hunt_auth_token.token))
