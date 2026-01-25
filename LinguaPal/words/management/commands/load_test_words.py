from django.core.management.base import BaseCommand
from words.models import Word, WordTranslation, WordCategory, PartOfSpeech
from accounts.models import Language


class Command(BaseCommand):
    help = '테스트용 단어 데이터를 로드합니다 (약 30개)'

    def handle(self, *args, **options):
        self.stdout.write('테스트 단어 데이터 로딩 시작...')

        # 언어 조회
        japanese = Language.objects.filter(code='ja').first()
        korean = Language.objects.filter(code='ko').first()
        english = Language.objects.filter(code='en').first()
        spanish = Language.objects.filter(code='es').first()

        if not japanese or not korean:
            self.stdout.write(self.style.ERROR('일본어(ja) 또는 한국어(ko) 언어가 없습니다. load_initial_data를 먼저 실행하세요.'))
            return

        # 일본어 단어 데이터 (한국어 번역 포함)
        japanese_words = [
            # 명사
            {'text': '猫', 'pronunciation': 'ねこ', 'pos': PartOfSpeech.NOUN, 'ko': '고양이', 'level': 1},
            {'text': '犬', 'pronunciation': 'いぬ', 'pos': PartOfSpeech.NOUN, 'ko': '개', 'level': 1},
            {'text': '水', 'pronunciation': 'みず', 'pos': PartOfSpeech.NOUN, 'ko': '물', 'level': 1},
            {'text': '火', 'pronunciation': 'ひ', 'pos': PartOfSpeech.NOUN, 'ko': '불', 'level': 1},
            {'text': '山', 'pronunciation': 'やま', 'pos': PartOfSpeech.NOUN, 'ko': '산', 'level': 1},
            {'text': '川', 'pronunciation': 'かわ', 'pos': PartOfSpeech.NOUN, 'ko': '강', 'level': 1},
            {'text': '空', 'pronunciation': 'そら', 'pos': PartOfSpeech.NOUN, 'ko': '하늘', 'level': 1},
            {'text': '海', 'pronunciation': 'うみ', 'pos': PartOfSpeech.NOUN, 'ko': '바다', 'level': 1},
            {'text': '花', 'pronunciation': 'はな', 'pos': PartOfSpeech.NOUN, 'ko': '꽃', 'level': 1},
            {'text': '木', 'pronunciation': 'き', 'pos': PartOfSpeech.NOUN, 'ko': '나무', 'level': 1},
            {'text': '本', 'pronunciation': 'ほん', 'pos': PartOfSpeech.NOUN, 'ko': '책', 'level': 1},
            {'text': '学校', 'pronunciation': 'がっこう', 'pos': PartOfSpeech.NOUN, 'ko': '학교', 'level': 2},
            {'text': '先生', 'pronunciation': 'せんせい', 'pos': PartOfSpeech.NOUN, 'ko': '선생님', 'level': 2},
            {'text': '友達', 'pronunciation': 'ともだち', 'pos': PartOfSpeech.NOUN, 'ko': '친구', 'level': 2},
            {'text': '家族', 'pronunciation': 'かぞく', 'pos': PartOfSpeech.NOUN, 'ko': '가족', 'level': 2},
            # 동사
            {'text': '食べる', 'pronunciation': 'たべる', 'pos': PartOfSpeech.VERB, 'ko': '먹다', 'level': 1},
            {'text': '飲む', 'pronunciation': 'のむ', 'pos': PartOfSpeech.VERB, 'ko': '마시다', 'level': 1},
            {'text': '行く', 'pronunciation': 'いく', 'pos': PartOfSpeech.VERB, 'ko': '가다', 'level': 1},
            {'text': '来る', 'pronunciation': 'くる', 'pos': PartOfSpeech.VERB, 'ko': '오다', 'level': 1},
            {'text': '見る', 'pronunciation': 'みる', 'pos': PartOfSpeech.VERB, 'ko': '보다', 'level': 1},
            # 형용사
            {'text': '大きい', 'pronunciation': 'おおきい', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '크다', 'level': 1},
            {'text': '小さい', 'pronunciation': 'ちいさい', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '작다', 'level': 1},
            {'text': '新しい', 'pronunciation': 'あたらしい', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '새롭다', 'level': 2},
            {'text': '古い', 'pronunciation': 'ふるい', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '오래되다', 'level': 2},
            {'text': '美味しい', 'pronunciation': 'おいしい', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '맛있다', 'level': 1},
        ]

        # 영어 단어 데이터 (한국어 번역 포함)
        english_words = []
        if english:
            english_words = [
                {'text': 'cat', 'pronunciation': '/kæt/', 'pos': PartOfSpeech.NOUN, 'ko': '고양이', 'level': 1},
                {'text': 'dog', 'pronunciation': '/dɔːɡ/', 'pos': PartOfSpeech.NOUN, 'ko': '개', 'level': 1},
                {'text': 'water', 'pronunciation': '/ˈwɔːtər/', 'pos': PartOfSpeech.NOUN, 'ko': '물', 'level': 1},
                {'text': 'book', 'pronunciation': '/bʊk/', 'pos': PartOfSpeech.NOUN, 'ko': '책', 'level': 1},
                {'text': 'school', 'pronunciation': '/skuːl/', 'pos': PartOfSpeech.NOUN, 'ko': '학교', 'level': 1},
            ]

        # 스페인어 단어 데이터 (한국어 번역 포함)
        spanish_words = []
        if spanish:
            spanish_words = [
                {'text': 'gato', 'pronunciation': '/ˈɡato/', 'pos': PartOfSpeech.NOUN, 'ko': '고양이', 'level': 1},
                {'text': 'perro', 'pronunciation': '/ˈpero/', 'pos': PartOfSpeech.NOUN, 'ko': '개', 'level': 1},
                {'text': 'agua', 'pronunciation': '/ˈaɣwa/', 'pos': PartOfSpeech.NOUN, 'ko': '물', 'level': 1},
                {'text': 'libro', 'pronunciation': '/ˈliβɾo/', 'pos': PartOfSpeech.NOUN, 'ko': '책', 'level': 1},
                {'text': 'escuela', 'pronunciation': '/esˈkwela/', 'pos': PartOfSpeech.NOUN, 'ko': '학교', 'level': 1},
            ]

        created_count = 0

        # 일본어 단어 생성
        for word_data in japanese_words:
            word, created = Word.objects.get_or_create(
                language=japanese,
                text=word_data['text'],
                category=WordCategory.WORD,
                defaults={
                    'pronunciation': word_data['pronunciation'],
                    'part_of_speech': word_data['pos'],
                    'difficulty_level': word_data['level'],
                    'grammar': {'romanji': word_data['pronunciation']},
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"  생성: {word_data['text']} ({japanese.code})")

            # 한국어 번역 추가
            WordTranslation.objects.get_or_create(
                word=word,
                language=korean,
                defaults={'translated_text': word_data['ko']}
            )

        # 영어 단어 생성
        if english:
            for word_data in english_words:
                word, created = Word.objects.get_or_create(
                    language=english,
                    text=word_data['text'],
                    category=WordCategory.WORD,
                    defaults={
                        'pronunciation': word_data['pronunciation'],
                        'part_of_speech': word_data['pos'],
                        'difficulty_level': word_data['level'],
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  생성: {word_data['text']} ({english.code})")

                WordTranslation.objects.get_or_create(
                    word=word,
                    language=korean,
                    defaults={'translated_text': word_data['ko']}
                )

        # 스페인어 단어 생성
        if spanish:
            for word_data in spanish_words:
                word, created = Word.objects.get_or_create(
                    language=spanish,
                    text=word_data['text'],
                    category=WordCategory.WORD,
                    defaults={
                        'pronunciation': word_data['pronunciation'],
                        'part_of_speech': word_data['pos'],
                        'difficulty_level': word_data['level'],
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  생성: {word_data['text']} ({spanish.code})")

                WordTranslation.objects.get_or_create(
                    word=word,
                    language=korean,
                    defaults={'translated_text': word_data['ko']}
                )

        self.stdout.write(self.style.SUCCESS(f'테스트 단어 로딩 완료! (새로 생성: {created_count}개)'))

        # 요약 출력
        total_words = Word.objects.filter(category=WordCategory.WORD).count()
        ja_words = Word.objects.filter(language=japanese, category=WordCategory.WORD).count() if japanese else 0
        en_words = Word.objects.filter(language=english, category=WordCategory.WORD).count() if english else 0
        es_words = Word.objects.filter(language=spanish, category=WordCategory.WORD).count() if spanish else 0

        self.stdout.write(f'\n총 단어 수: {total_words}개')
        self.stdout.write(f'  - 일본어: {ja_words}개')
        self.stdout.write(f'  - 영어: {en_words}개')
        self.stdout.write(f'  - 스페인어: {es_words}개')
