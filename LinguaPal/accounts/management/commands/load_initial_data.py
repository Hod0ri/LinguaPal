from django.core.management.base import BaseCommand
from accounts.models import Language, Country
from words.models import Word, WordTranslation, WordCategory, PartOfSpeech
import requests


class Command(BaseCommand):
    help = 'Load initial language and country data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-countries',
            action='store_true',
            help='Skip fetching countries from REST Countries API',
        )
        parser.add_argument(
            '--skip-japanese-chars',
            action='store_true',
            help='Skip loading Japanese hiragana/katakana characters',
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

        # Load Japanese hiragana and katakana characters
        if not options['skip_japanese_chars']:
            self.load_japanese_characters()
        else:
            self.stdout.write(self.style.WARNING(f"\n⏭️  Skipping Japanese characters (--skip-japanese-chars)"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Initial data loading completed!"))

    def load_japanese_characters(self):
        """Load hiragana and katakana characters for Japanese language learning"""
        self.stdout.write(self.style.WARNING(f"\n🇯🇵 Loading Japanese hiragana and katakana characters..."))

        # Get Japanese and Korean languages
        try:
            japanese = Language.objects.get(code='ja')
            korean_lang = Language.objects.get(code='ko')
        except Language.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Japanese or Korean language not found. Please load languages first."))
            return

        # Hiragana data: (character, romanji, korean_pronunciation, row, order)
        hiragana_data = [
            # あ행 (a-row)
            ('あ', 'a', '아', 'あ행', 1),
            ('い', 'i', '이', 'あ행', 2),
            ('う', 'u', '우', 'あ행', 3),
            ('え', 'e', '에', 'あ행', 4),
            ('お', 'o', '오', 'あ행', 5),
            # か행 (ka-row)
            ('か', 'ka', '카', 'か행', 6),
            ('き', 'ki', '키', 'か행', 7),
            ('く', 'ku', '쿠', 'か행', 8),
            ('け', 'ke', '케', 'か행', 9),
            ('こ', 'ko', '코', 'か행', 10),
            # さ행 (sa-row)
            ('さ', 'sa', '사', 'さ행', 11),
            ('し', 'shi', '시', 'さ행', 12),
            ('す', 'su', '스', 'さ행', 13),
            ('せ', 'se', '세', 'さ행', 14),
            ('そ', 'so', '소', 'さ행', 15),
            # た행 (ta-row)
            ('た', 'ta', '타', 'た행', 16),
            ('ち', 'chi', '치', 'た행', 17),
            ('つ', 'tsu', '츠', 'た행', 18),
            ('て', 'te', '테', 'た행', 19),
            ('と', 'to', '토', 'た행', 20),
            # な행 (na-row)
            ('な', 'na', '나', 'な행', 21),
            ('に', 'ni', '니', 'な행', 22),
            ('ぬ', 'nu', '누', 'な행', 23),
            ('ね', 'ne', '네', 'な행', 24),
            ('の', 'no', '노', 'な행', 25),
            # は행 (ha-row)
            ('は', 'ha', '하', 'は행', 26),
            ('ひ', 'hi', '히', 'は행', 27),
            ('ふ', 'fu', '후', 'は행', 28),
            ('へ', 'he', '헤', 'は행', 29),
            ('ほ', 'ho', '호', 'は행', 30),
            # ま행 (ma-row)
            ('ま', 'ma', '마', 'ま행', 31),
            ('み', 'mi', '미', 'ま행', 32),
            ('む', 'mu', '무', 'ま행', 33),
            ('め', 'me', '메', 'ま행', 34),
            ('も', 'mo', '모', 'ま행', 35),
            # や행 (ya-row)
            ('や', 'ya', '야', 'や행', 36),
            ('ゆ', 'yu', '유', 'や행', 37),
            ('よ', 'yo', '요', 'や행', 38),
            # ら행 (ra-row)
            ('ら', 'ra', '라', 'ら행', 39),
            ('り', 'ri', '리', 'ら행', 40),
            ('る', 'ru', '루', 'ら행', 41),
            ('れ', 're', '레', 'ら행', 42),
            ('ろ', 'ro', '로', 'ら행', 43),
            # わ행 (wa-row)
            ('わ', 'wa', '와', 'わ행', 44),
            ('を', 'wo', '오/wo', 'わ행', 45),
            # ん (n)
            ('ん', 'n', '응', 'ん', 46),
        ]

        # Katakana data: (character, romanji, korean_pronunciation, row, order)
        katakana_data = [
            # ア행 (a-row)
            ('ア', 'a', '아', 'ア행', 1),
            ('イ', 'i', '이', 'ア행', 2),
            ('ウ', 'u', '우', 'ア행', 3),
            ('エ', 'e', '에', 'ア행', 4),
            ('オ', 'o', '오', 'ア행', 5),
            # カ행 (ka-row)
            ('カ', 'ka', '카', 'カ행', 6),
            ('キ', 'ki', '키', 'カ행', 7),
            ('ク', 'ku', '쿠', 'カ행', 8),
            ('ケ', 'ke', '케', 'カ행', 9),
            ('コ', 'ko', '코', 'カ행', 10),
            # サ행 (sa-row)
            ('サ', 'sa', '사', 'サ행', 11),
            ('シ', 'shi', '시', 'サ행', 12),
            ('ス', 'su', '스', 'サ행', 13),
            ('セ', 'se', '세', 'サ행', 14),
            ('ソ', 'so', '소', 'サ행', 15),
            # タ행 (ta-row)
            ('タ', 'ta', '타', 'タ행', 16),
            ('チ', 'chi', '치', 'タ행', 17),
            ('ツ', 'tsu', '츠', 'タ행', 18),
            ('テ', 'te', '테', 'タ행', 19),
            ('ト', 'to', '토', 'タ행', 20),
            # ナ행 (na-row)
            ('ナ', 'na', '나', 'ナ행', 21),
            ('ニ', 'ni', '니', 'ナ행', 22),
            ('ヌ', 'nu', '누', 'ナ행', 23),
            ('ネ', 'ne', '네', 'ナ행', 24),
            ('ノ', 'no', '노', 'ナ행', 25),
            # ハ행 (ha-row)
            ('ハ', 'ha', '하', 'ハ행', 26),
            ('ヒ', 'hi', '히', 'ハ행', 27),
            ('フ', 'fu', '후', 'ハ행', 28),
            ('ヘ', 'he', '헤', 'ハ행', 29),
            ('ホ', 'ho', '호', 'ハ행', 30),
            # マ행 (ma-row)
            ('マ', 'ma', '마', 'マ행', 31),
            ('ミ', 'mi', '미', 'マ행', 32),
            ('ム', 'mu', '무', 'マ행', 33),
            ('メ', 'me', '메', 'マ행', 34),
            ('モ', 'mo', '모', 'マ행', 35),
            # ヤ행 (ya-row)
            ('ヤ', 'ya', '야', 'ヤ행', 36),
            ('ユ', 'yu', '유', 'ヤ행', 37),
            ('ヨ', 'yo', '요', 'ヤ행', 38),
            # ラ행 (ra-row)
            ('ラ', 'ra', '라', 'ラ행', 39),
            ('リ', 'ri', '리', 'ラ행', 40),
            ('ル', 'ru', '루', 'ラ행', 41),
            ('レ', 're', '레', 'ラ행', 42),
            ('ロ', 'ro', '로', 'ラ행', 43),
            # ワ행 (wa-row)
            ('ワ', 'wa', '와', 'ワ행', 44),
            ('ヲ', 'wo', '오/wo', 'ワ행', 45),
            # ン (n)
            ('ン', 'n', '응', 'ン', 46),
        ]

        created_hiragana = 0
        created_katakana = 0
        skipped = 0

        # Load Hiragana
        for char, romanji, korean_pron, row, order in hiragana_data:
            word, created = Word.objects.get_or_create(
                language=japanese,
                text=char,
                category=WordCategory.HIRAGANA,
                defaults={
                    'part_of_speech': PartOfSpeech.CHARACTER,
                    'pronunciation': romanji,
                    'grammar': {'romanji': romanji, 'row': row},
                    'order': order,
                    'difficulty_level': 1,
                    'is_active': True,
                }
            )
            if created:
                # Add Korean translation
                WordTranslation.objects.create(
                    word=word,
                    language=korean_lang,
                    translated_text=korean_pron,
                    notes=f'로마자: {romanji}'
                )
                created_hiragana += 1
            else:
                skipped += 1

        # Load Katakana
        for char, romanji, korean_pron, row, order in katakana_data:
            word, created = Word.objects.get_or_create(
                language=japanese,
                text=char,
                category=WordCategory.KATAKANA,
                defaults={
                    'part_of_speech': PartOfSpeech.CHARACTER,
                    'pronunciation': romanji,
                    'grammar': {'romanji': romanji, 'row': row},
                    'order': order,
                    'difficulty_level': 1,
                    'is_active': True,
                }
            )
            if created:
                # Add Korean translation
                WordTranslation.objects.create(
                    word=word,
                    language=korean_lang,
                    translated_text=korean_pron,
                    notes=f'로마자: {romanji}'
                )
                created_katakana += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f"  ✅ Hiragana: {created_hiragana} characters created"))
        self.stdout.write(self.style.SUCCESS(f"  ✅ Katakana: {created_katakana} characters created"))
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f"  ⏭️  Skipped: {skipped} (already exist)"))
