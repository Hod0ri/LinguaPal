from django.core.management.base import BaseCommand
from accounts.models import Language, Country
import requests


class Command(BaseCommand):
    help = 'Load initial language and country data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-countries',
            action='store_true',
            help='Skip fetching countries from REST Countries API',
        )

    def handle(self, *args, **options):
        # Language data (4 basic languages)
        languages = [
            {'code': 'ko', 'name_ko': '한국어', 'name_en': 'Korean'},
            {'code': 'en', 'name_ko': '영어', 'name_en': 'English'},
            {'code': 'ja', 'name_ko': '일본어', 'name_en': 'Japanese'},
            {'code': 'es', 'name_ko': '스페인어', 'name_en': 'Spanish'},
        ]

        # Load languages
        created_languages = 0
        updated_languages = 0
        for lang_data in languages:
            language, created = Language.objects.get_or_create(
                code=lang_data['code'],
                defaults={
                    'name_ko': lang_data['name_ko'],
                    'name_en': lang_data['name_en']
                }
            )
            if created:
                created_languages += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Language created: {language.name_en} ({language.code})"))
            else:
                language.name_ko = lang_data['name_ko']
                language.name_en = lang_data['name_en']
                language.save()
                updated_languages += 1
                self.stdout.write(self.style.WARNING(f"🔄 Language updated: {language.name_en} ({language.code})"))

        self.stdout.write(self.style.SUCCESS(f"\n📚 Languages: {created_languages} created, {updated_languages} updated"))

        # Load countries from REST Countries API
        if not options['skip_countries']:
            self.stdout.write(self.style.WARNING(f"\n🌍 Fetching countries from REST Countries API..."))
            try:
                # Fetch all countries with specific fields
                response = requests.get(
                    'https://restcountries.com/v3.1/all',
                    params={
                        'fields': 'cca2,name,translations'
                    },
                    timeout=10
                )
                response.raise_for_status()
                countries_data = response.json()

                created_countries = 0
                updated_countries = 0
                skipped_countries = 0

                for country_info in countries_data:
                    try:
                        code = country_info.get('cca2')  # ISO 3166-1 alpha-2 code
                        name_en = country_info.get('name', {}).get('common', '')

                        # Get Korean name from translations
                        translations = country_info.get('translations', {})
                        name_ko = translations.get('kor', {}).get('common', name_en)

                        if not code or not name_en:
                            skipped_countries += 1
                            continue

                        # Create or update country
                        country, created = Country.objects.get_or_create(
                            code=code,
                            defaults={
                                'name_ko': name_ko,
                                'name_en': name_en
                            }
                        )

                        if created:
                            created_countries += 1
                            if created_countries <= 10:  # Show first 10
                                self.stdout.write(
                                    self.style.SUCCESS(f"  ✅ {country.name_en} ({country.code}) - {country.name_ko}")
                                )
                        else:
                            # Update existing country
                            country.name_ko = name_ko
                            country.name_en = name_en
                            country.save()
                            updated_countries += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Error processing country: {e}")
                        )
                        continue

                if created_countries > 10:
                    self.stdout.write(self.style.SUCCESS(f"  ... and {created_countries - 10} more"))

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n🌍 Countries: {created_countries} created, {updated_countries} updated, {skipped_countries} skipped"
                    )
                )

            except requests.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(f"\n❌ Failed to fetch countries from API: {e}")
                )
                self.stdout.write(
                    self.style.WARNING(f"💡 You can run this command again or use --skip-countries to skip country loading")
                )
        else:
            self.stdout.write(self.style.WARNING(f"\n⏭️  Skipping country data fetch (--skip-countries)"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Initial data loading completed!"))
