"""
Management command to fix grammar data in Word model.
Fixes:
1. romanji/romaji fields containing kana -> convert to actual romaji
2. Standardize grammar property keys
"""
from django.core.management.base import BaseCommand
from words.models import Word


# Hiragana to Romaji mapping
HIRAGANA_TO_ROMAJI = {
    # Basic vowels
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    # K row
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    # S row
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    # T row
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    # N row
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    # H row
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    # M row
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    # Y row
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    # R row
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    # W row
    'わ': 'wa', 'を': 'wo', 'ん': 'n',
    # Dakuten (voiced)
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    # Handakuten
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    # Small kana
    'ぁ': 'a', 'ぃ': 'i', 'ぅ': 'u', 'ぇ': 'e', 'ぉ': 'o',
    'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo', 'っ': '',
    # Combinations (yoon)
    'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo',
    'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho',
    'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho',
    'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
    'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo',
    'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
    'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
    'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
    'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo',
    'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
    'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo',
}

# Katakana to Romaji mapping
KATAKANA_TO_ROMAJI = {
    # Basic vowels
    'ア': 'a', 'イ': 'i', 'ウ': 'u', 'エ': 'e', 'オ': 'o',
    # K row
    'カ': 'ka', 'キ': 'ki', 'ク': 'ku', 'ケ': 'ke', 'コ': 'ko',
    # S row
    'サ': 'sa', 'シ': 'shi', 'ス': 'su', 'セ': 'se', 'ソ': 'so',
    # T row
    'タ': 'ta', 'チ': 'chi', 'ツ': 'tsu', 'テ': 'te', 'ト': 'to',
    # N row
    'ナ': 'na', 'ニ': 'ni', 'ヌ': 'nu', 'ネ': 'ne', 'ノ': 'no',
    # H row
    'ハ': 'ha', 'ヒ': 'hi', 'フ': 'fu', 'ヘ': 'he', 'ホ': 'ho',
    # M row
    'マ': 'ma', 'ミ': 'mi', 'ム': 'mu', 'メ': 'me', 'モ': 'mo',
    # Y row
    'ヤ': 'ya', 'ユ': 'yu', 'ヨ': 'yo',
    # R row
    'ラ': 'ra', 'リ': 'ri', 'ル': 'ru', 'レ': 're', 'ロ': 'ro',
    # W row
    'ワ': 'wa', 'ヲ': 'wo', 'ン': 'n',
    # Dakuten (voiced)
    'ガ': 'ga', 'ギ': 'gi', 'グ': 'gu', 'ゲ': 'ge', 'ゴ': 'go',
    'ザ': 'za', 'ジ': 'ji', 'ズ': 'zu', 'ゼ': 'ze', 'ゾ': 'zo',
    'ダ': 'da', 'ヂ': 'di', 'ヅ': 'du', 'デ': 'de', 'ド': 'do',
    'バ': 'ba', 'ビ': 'bi', 'ブ': 'bu', 'ベ': 'be', 'ボ': 'bo',
    # Handakuten
    'パ': 'pa', 'ピ': 'pi', 'プ': 'pu', 'ペ': 'pe', 'ポ': 'po',
    # Small kana
    'ァ': 'a', 'ィ': 'i', 'ゥ': 'u', 'ェ': 'e', 'ォ': 'o',
    'ャ': 'ya', 'ュ': 'yu', 'ョ': 'yo', 'ッ': '',
    # Long vowel mark
    'ー': '',
    # Combinations (yoon)
    'キャ': 'kya', 'キュ': 'kyu', 'キョ': 'kyo',
    'シャ': 'sha', 'シュ': 'shu', 'ショ': 'sho',
    'チャ': 'cha', 'チュ': 'chu', 'チョ': 'cho',
    'ニャ': 'nya', 'ニュ': 'nyu', 'ニョ': 'nyo',
    'ヒャ': 'hya', 'ヒュ': 'hyu', 'ヒョ': 'hyo',
    'ミャ': 'mya', 'ミュ': 'myu', 'ミョ': 'myo',
    'リャ': 'rya', 'リュ': 'ryu', 'リョ': 'ryo',
    'ギャ': 'gya', 'ギュ': 'gyu', 'ギョ': 'gyo',
    'ジャ': 'ja', 'ジュ': 'ju', 'ジョ': 'jo',
    'ビャ': 'bya', 'ビュ': 'byu', 'ビョ': 'byo',
    'ピャ': 'pya', 'ピュ': 'pyu', 'ピョ': 'pyo',
    # Extended katakana
    'ヴァ': 'va', 'ヴィ': 'vi', 'ヴ': 'vu', 'ヴェ': 've', 'ヴォ': 'vo',
    'ファ': 'fa', 'フィ': 'fi', 'フェ': 'fe', 'フォ': 'fo',
    'ティ': 'ti', 'ディ': 'di',
    'トゥ': 'tu', 'ドゥ': 'du',
    'ウィ': 'wi', 'ウェ': 'we', 'ウォ': 'wo',
}

# Combined mapping
KANA_TO_ROMAJI = {**HIRAGANA_TO_ROMAJI, **KATAKANA_TO_ROMAJI}


def contains_kana(text: str) -> bool:
    """Check if text contains Japanese kana characters."""
    for char in text:
        if char in KANA_TO_ROMAJI:
            return True
        # Check Unicode ranges for kana
        code = ord(char)
        # Hiragana: 3040-309F, Katakana: 30A0-30FF
        if 0x3040 <= code <= 0x309F or 0x30A0 <= code <= 0x30FF:
            return True
    return False


def kana_to_romaji(text: str) -> str:
    """Convert kana text to romaji."""
    result = []
    i = 0
    while i < len(text):
        # Try 2-character combinations first (for yoon combinations)
        if i + 1 < len(text):
            two_char = text[i:i+2]
            if two_char in KANA_TO_ROMAJI:
                result.append(KANA_TO_ROMAJI[two_char])
                i += 2
                continue

        # Single character
        char = text[i]
        if char in KANA_TO_ROMAJI:
            result.append(KANA_TO_ROMAJI[char])
        else:
            # Keep non-kana characters as-is
            result.append(char)
        i += 1

    return ''.join(result)


class Command(BaseCommand):
    help = 'Fix grammar data in Word model (convert kana to romaji, standardize keys)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually changing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        words = Word.objects.exclude(grammar={})
        total_words = words.count()
        fixed_count = 0

        self.stdout.write(f'Checking {total_words} words with grammar data...\n')

        for word in words:
            grammar = word.grammar
            original_grammar = dict(grammar)  # Copy for comparison
            changes = []

            # Fix 1: Convert kana in romanji/romaji to actual romaji
            for key in ['romanji', 'romaji']:
                if key in grammar:
                    value = grammar[key]
                    if isinstance(value, str) and contains_kana(value):
                        new_value = kana_to_romaji(value)
                        changes.append(f'  {key}: "{value}" -> "{new_value}"')
                        grammar[key] = new_value

            # Fix 2: If word.text is kana but pronunciation is empty, set pronunciation
            if word.category in ['hiragana', 'katakana'] and not word.pronunciation:
                if contains_kana(word.text):
                    romaji = kana_to_romaji(word.text)
                    if romaji != word.text:
                        changes.append(f'  pronunciation: "" -> "{romaji}"')
                        if not dry_run:
                            word.pronunciation = romaji

            # Fix 3: If grammar has 'romanji' but contains kana, also check 'kana' field
            if 'romanji' in grammar or 'romaji' in grammar:
                # Ensure the romaji value is actually romaji (alphabet)
                for key in ['romanji', 'romaji']:
                    if key in grammar:
                        value = grammar[key]
                        if isinstance(value, str) and contains_kana(value):
                            # This was already fixed above, but double-check
                            pass

            # Fix 4: If word is a kana character, add 'kana' field with the character
            if word.category in ['hiragana', 'katakana']:
                if 'kana' not in grammar:
                    grammar['kana'] = word.text
                    changes.append(f'  Added kana: "{word.text}"')

                # Set type based on category
                if 'type' not in grammar:
                    grammar['type'] = word.category
                    changes.append(f'  Added type: "{word.category}"')

            # Save if there were changes
            if grammar != original_grammar or changes:
                fixed_count += 1
                self.stdout.write(f'\n{word.text} (ID: {word.id}):')
                for change in changes:
                    self.stdout.write(change)

                if not dry_run:
                    word.grammar = grammar
                    word.save()

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(f'Would fix {fixed_count} words'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} words'))
