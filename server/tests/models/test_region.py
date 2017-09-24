from django.test import TransactionTestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from server.models import *


class RegionTests(TransactionTestCase):
    def test_normal_creation(self):
        """
        Normal creation of regions. Regions must be unique based off of region name.
        """
        valid_regions = [
            {'name': 'First Region'},
            {'name': 'Second Region'},
            {'name': 'Third Region'},
        ]

        regions = []
        for region_data in valid_regions:
            region = Region.objects.create(name=region_data['name'])
            region.full_clean()
            regions.append(region)

        self.assertSequenceEqual(Region.objects.all(), regions)

    def test_duplicate_creation(self):
        """
        Duplicate regions must not exist. Regions must be unique based off of region name.
        """
        valid_regions = [
            {'name': 'First Region'},
            {'name': 'Second Region'},
            {'name': 'Third Region'},
        ]

        regions = []
        for region_data in valid_regions:
            regions.append(Region.objects.create(name=region_data['name']))

        for region_data in valid_regions:
            with self.assertRaises(IntegrityError):
                Region.objects.create(name=region_data['name'])

        self.assertSequenceEqual(Region.objects.all(), regions)

    def test_creation_validity(self):
        with self.assertRaises(ValidationError):
            Region(name=None).full_clean()
            Region(name='').full_clean()
            Region(name='x' * 256).full_clean()

        self.assertEqual(Region.objects.count(), 0)


