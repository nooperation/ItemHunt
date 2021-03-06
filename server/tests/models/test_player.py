from django.test import TransactionTestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from server.models import *


class PlayerTests(TransactionTestCase):
    def setUp(self):
        self.hunt = Hunt.objects.create(
            name='First hunt',
            private_token='j14WVsOPsIdzQIZGQeymFmpPv4LqpHQWck8ua0ZdCY71'
        )
        self.second_hunt = Hunt.objects.create(
            name='Second hunt',
            private_token='a' * 32
        )

    def test_normal_creation(self):
        valid_players = [
            {'name': 'First Agent', 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'hunt': self.hunt},
            {'name': 'Second Agent', 'uuid': '3a208475-b8a7-3dea-fbf0-67c4bfa461af', 'hunt': self.hunt},
            {'name': 'Third Agent', 'uuid': 'a7488bf2-fef3-4846-a898-fc60dea73dbb', 'hunt': self.hunt},
        ]

        players = []
        for player_data in valid_players:
            player = Player.objects.create(name=player_data['name'], uuid=player_data['uuid'])
            player.full_clean()
            players.append(player)

        self.assertSequenceEqual(Player.objects.all(), players)

    def test_duplicate_uuid_different_name_same_hunt(self):
        original_player = Player.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af')

        with self.assertRaises(ValidationError):
            player = Player(name='Invalid Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af')
            player.full_clean()
            player.save()

        self.assertSequenceEqual(Player.objects.all(), [original_player])

    def test_duplicate_name_different_uuid_same_hunt(self):
        original_player = Player.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af')

        with self.assertRaises(ValidationError):
            player = Player(name='First Agent', uuid='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
            player.full_clean()
            player.save()

        self.assertSequenceEqual(Player.objects.all(), [original_player])

    def test_duplicate_creation(self):
        valid_players = [
            {'name': 'First Agent', 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af'},
            {'name': 'Second Agent', 'uuid': '3a208475-b8a7-3dea-fbf0-67c4bfa461af'},
            {'name': 'Third Agent', 'uuid': 'a7488bf2-fef3-4846-a898-fc60dea73dbb'},
        ]

        players = []
        for player_data in valid_players:
            players.append(Player.objects.create(name=player_data['name'], uuid=player_data['uuid']))

        for player_data in valid_players:
            with self.assertRaises(IntegrityError):
                Player.objects.create(name=player_data['name'], uuid=player_data['uuid']).full_clean()

        self.assertSequenceEqual(Player.objects.all(), players)

    def test_creation_validity(self):
        with self.assertRaises(ValidationError):
            Player(name=None, uuid='41f94400-2a3e-408a-9b80-1774724f62af').full_clean()
        with self.assertRaises(ValidationError):
            Player(name='Second Agent', uuid=None).full_clean()
        with self.assertRaises(ValidationError):
            Player(name=None, uuid=None).full_clean()
        with self.assertRaises(ValidationError):
            Player(name='', uuid='00000000-0000-0000-0000-000000000001').full_clean()
        with self.assertRaises(ValidationError):
            Player(name='x' * 256, uuid='00000000-0000-0000-0000-000000000002').full_clean()
        with self.assertRaises(ValidationError):
            Player(name='third name', uuid='').full_clean()
        with self.assertRaises(ValidationError):
            Player(name='fourth name', uuid='00000000-0000-0000-0000-00000000000X').full_clean()
        with self.assertRaises(ValidationError):
            Player(name='fifth name', uuid='00000000-0000-0000-0000-0000000000012').full_clean()
