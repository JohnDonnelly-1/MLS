"""
Management command to create sample security labels for testing the classification helper.

Usage:
    docker-compose exec web python manage.py setup_sample_labels
"""

from django.core.management.base import BaseCommand
from mls_core.models import SecurityLabel


class Command(BaseCommand):
    help = 'Create sample security labels for classification helper demo'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample security labels...'))

        labels_created = 0

        # Classification Levels
        levels = [
            {'short_code': 'UNCLASS', 'name': 'Unclassified', 'rank': 0, 'color': '#008000',
             'description': 'Information that is not classified'},
            {'short_code': 'CONFIDENTIAL', 'name': 'Confidential', 'rank': 1, 'color': '#0000FF',
             'description': 'Information that could cause damage to national security'},
            {'short_code': 'SECRET', 'name': 'Secret', 'rank': 2, 'color': '#FFA500',
             'description': 'Information that could cause serious damage to national security'},
            {'short_code': 'TS', 'name': 'Top Secret', 'rank': 3, 'color': '#FF0000',
             'description': 'Information that could cause exceptionally grave damage to national security'},
        ]

        for level in levels:
            obj, created = SecurityLabel.objects.get_or_create(
                short_code=level['short_code'],
                defaults={
                    'name': level['name'],
                    'label_type': 'LVL',
                    'rank': level['rank'],
                    'color': level['color'],
                    'description': level['description']
                }
            )
            if created:
                labels_created += 1
                self.stdout.write(f'  ✓ Created level: {level["short_code"]}')
            else:
                self.stdout.write(f'  - Level already exists: {level["short_code"]}')

        # SCI Caveats
        sci_caveats = [
            {'short_code': 'SCI-TK', 'name': 'Talent Keyhole', 'color': '#800080',
             'description': 'Overhead collection systems'},
            {'short_code': 'SCI-SI', 'name': 'Special Intelligence', 'color': '#800080',
             'description': 'Signals intelligence sources'},
            {'short_code': 'SCI-G', 'name': 'Gamma', 'color': '#800080',
             'description': 'Extremely sensitive communications intelligence'},
            {'short_code': 'SCI-HCS', 'name': 'HUMINT Control System', 'color': '#800080',
             'description': 'Human intelligence sources'},
        ]

        for sci in sci_caveats:
            obj, created = SecurityLabel.objects.get_or_create(
                short_code=sci['short_code'],
                defaults={
                    'name': sci['name'],
                    'label_type': 'CAT',
                    'rank': 0,
                    'color': sci['color'],
                    'description': sci['description']
                }
            )
            if created:
                labels_created += 1
                self.stdout.write(f'  ✓ Created SCI: {sci["short_code"]}')
            else:
                self.stdout.write(f'  - SCI already exists: {sci["short_code"]}')

        # SAP Access
        sap_programs = [
            {'short_code': 'SAP-ALPHA', 'name': 'SAP Alpha Program', 'color': '#8B4513',
             'description': 'Special Access Program Alpha'},
            {'short_code': 'SAP-BRAVO', 'name': 'SAP Bravo Program', 'color': '#8B4513',
             'description': 'Special Access Program Bravo'},
            {'short_code': 'SAP-CHARLIE', 'name': 'SAP Charlie Program', 'color': '#8B4513',
             'description': 'Special Access Program Charlie'},
        ]

        for sap in sap_programs:
            obj, created = SecurityLabel.objects.get_or_create(
                short_code=sap['short_code'],
                defaults={
                    'name': sap['name'],
                    'label_type': 'CAT',
                    'rank': 0,
                    'color': sap['color'],
                    'description': sap['description']
                }
            )
            if created:
                labels_created += 1
                self.stdout.write(f'  ✓ Created SAP: {sap["short_code"]}')
            else:
                self.stdout.write(f'  - SAP already exists: {sap["short_code"]}')

        # Dissemination Controls
        dissemination = [
            {'short_code': 'NOFORN', 'name': 'Not Releasable to Foreign Nationals', 'color': '#FF6347',
             'description': 'Information not authorized for release to foreign nationals'},
            {'short_code': 'ORCON', 'name': 'Originator Controlled', 'color': '#FF6347',
             'description': 'Dissemination controlled by originator'},
            {'short_code': 'PROPIN', 'name': 'Proprietary Information', 'color': '#FF6347',
             'description': 'Contains proprietary information'},
            {'short_code': 'RELTO', 'name': 'Releasable To', 'color': '#4169E1',
             'description': 'Releasable to specified countries'},
            {'short_code': 'FOUO', 'name': 'For Official Use Only', 'color': '#FFD700',
             'description': 'For official use only, not for public release'},
            {'short_code': 'LES', 'name': 'Law Enforcement Sensitive', 'color': '#FFD700',
             'description': 'Law enforcement sensitive information'},
        ]

        for diss in dissemination:
            obj, created = SecurityLabel.objects.get_or_create(
                short_code=diss['short_code'],
                defaults={
                    'name': diss['name'],
                    'label_type': 'CAT',
                    'rank': 0,
                    'color': diss['color'],
                    'description': diss['description']
                }
            )
            if created:
                labels_created += 1
                self.stdout.write(f'  ✓ Created dissemination: {diss["short_code"]}')
            else:
                self.stdout.write(f'  - Dissemination already exists: {diss["short_code"]}')

        # Releasability (countries) - REL TO markings
        countries = [
            {'short_code': 'USA', 'name': 'United States'},
            {'short_code': 'GBR', 'name': 'United Kingdom'},
            {'short_code': 'CAN', 'name': 'Canada'},
            {'short_code': 'AUS', 'name': 'Australia'},
            {'short_code': 'NZL', 'name': 'New Zealand'},
            {'short_code': 'DEU', 'name': 'Germany'},
            {'short_code': 'FRA', 'name': 'France'},
            {'short_code': 'ITA', 'name': 'Italy'},
            {'short_code': 'ESP', 'name': 'Spain'},
            {'short_code': 'NLD', 'name': 'Netherlands'},
            {'short_code': 'BEL', 'name': 'Belgium'},
            {'short_code': 'POL', 'name': 'Poland'},
            {'short_code': 'NOR', 'name': 'Norway'},
            {'short_code': 'DNK', 'name': 'Denmark'},
            {'short_code': 'PRT', 'name': 'Portugal'},
            {'short_code': 'GRC', 'name': 'Greece'},
            {'short_code': 'TUR', 'name': 'Turkey'},
            {'short_code': 'JPN', 'name': 'Japan'},
            {'short_code': 'KOR', 'name': 'South Korea'},
            {'short_code': 'ISR', 'name': 'Israel'},
        ]

        for country in countries:
            obj, created = SecurityLabel.objects.get_or_create(
                short_code=country['short_code'],
                defaults={
                    'name': country['name'],
                    'label_type': 'REL',
                    'rank': 0,
                    'color': '#1B7F79',
                    'description': f"Releasable to {country['name']}"
                }
            )
            if created:
                labels_created += 1
                self.stdout.write(f'  ✓ Created releasability: {country["short_code"]}')
            else:
                self.stdout.write(f'  - Releasability already exists: {country["short_code"]}')

        self.stdout.write(self.style.SUCCESS(f'\n✓ Done! Created {labels_created} new labels.'))
        self.stdout.write(self.style.SUCCESS(f'Total labels in system: {SecurityLabel.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('\nYou can now try the classification helper at:'))
        self.stdout.write(self.style.SUCCESS('http://localhost:8000/mls/classify/'))
