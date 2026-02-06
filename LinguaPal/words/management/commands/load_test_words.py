from django.core.management.base import BaseCommand
from words.models import Word, WordTranslation, Example, ExampleTranslation, WordCategory, PartOfSpeech
from accounts.models import Language


# Hiragana to Romaji mapping
HIRAGANA_TO_ROMAJI = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'を': 'wo', 'ん': 'n',
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    'ぁ': 'a', 'ぃ': 'i', 'ぅ': 'u', 'ぇ': 'e', 'ぉ': 'o',
    'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo', 'っ': '',
    # Yoon combinations
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


def hiragana_to_romaji(text: str) -> str:
    """Convert hiragana text to romaji."""
    result = []
    i = 0
    while i < len(text):
        # Try 2-character combinations first (for yoon)
        if i + 1 < len(text):
            two_char = text[i:i+2]
            if two_char in HIRAGANA_TO_ROMAJI:
                result.append(HIRAGANA_TO_ROMAJI[two_char])
                i += 2
                continue
        # Single character
        char = text[i]
        if char in HIRAGANA_TO_ROMAJI:
            result.append(HIRAGANA_TO_ROMAJI[char])
        else:
            result.append(char)
        i += 1
    return ''.join(result)


class Command(BaseCommand):
    help = '테스트용 단어 데이터를 로드합니다 (각 언어당 약 30개, 예문 포함)'

    def handle(self, *args, **options):
        self.stdout.write('테스트 단어 데이터 로딩 시작...')

        # 언어 조회
        japanese = Language.objects.filter(code='ja').first()
        korean = Language.objects.filter(code='ko').first()
        english = Language.objects.filter(code='en').first()
        spanish = Language.objects.filter(code='es').first()

        if not korean:
            self.stdout.write(self.style.ERROR('한국어(ko) 언어가 없습니다. load_initial_data를 먼저 실행하세요.'))
            return

        created_count = 0

        # ==================== 일본어 단어 (30개) ====================
        if japanese:
            japanese_words = [
                # 명사 (15개)
                {
                    'text': '猫', 'pronunciation': 'ねこ', 'pos': PartOfSpeech.NOUN, 'ko': '고양이', 'level': 1,
                    'example': '私の猫は白いです。', 'ex_highlight': [2, 3], 'ex_ko': '내 고양이는 하얗습니다.', 'ex_ko_highlight': [2, 5]
                },
                {
                    'text': '犬', 'pronunciation': 'いぬ', 'pos': PartOfSpeech.NOUN, 'ko': '개', 'level': 1,
                    'example': '犬が公園で遊んでいます。', 'ex_highlight': [0, 1], 'ex_ko': '개가 공원에서 놀고 있습니다.', 'ex_ko_highlight': [0, 1]
                },
                {
                    'text': '水', 'pronunciation': 'みず', 'pos': PartOfSpeech.NOUN, 'ko': '물', 'level': 1,
                    'example': '冷たい水を飲みたいです。', 'ex_highlight': [3, 4], 'ex_ko': '차가운 물을 마시고 싶습니다.', 'ex_ko_highlight': [4, 5]
                },
                {
                    'text': '本', 'pronunciation': 'ほん', 'pos': PartOfSpeech.NOUN, 'ko': '책', 'level': 1,
                    'example': 'この本はとても面白いです。', 'ex_highlight': [2, 3], 'ex_ko': '이 책은 매우 재미있습니다.', 'ex_ko_highlight': [2, 3]
                },
                {
                    'text': '学校', 'pronunciation': 'がっこう', 'pos': PartOfSpeech.NOUN, 'ko': '학교', 'level': 2,
                    'example': '学校まで歩いて行きます。', 'ex_highlight': [0, 2], 'ex_ko': '학교까지 걸어서 갑니다.', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': '先生', 'pronunciation': 'せんせい', 'pos': PartOfSpeech.NOUN, 'ko': '선생님', 'level': 2,
                    'example': '先生に質問があります。', 'ex_highlight': [0, 2], 'ex_ko': '선생님께 질문이 있습니다.', 'ex_ko_highlight': [0, 3]
                },
                {
                    'text': '友達', 'pronunciation': 'ともだち', 'pos': PartOfSpeech.NOUN, 'ko': '친구', 'level': 2,
                    'example': '友達と映画を見ました。', 'ex_highlight': [0, 2], 'ex_ko': '친구와 영화를 봤습니다.', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': '家族', 'pronunciation': 'かぞく', 'pos': PartOfSpeech.NOUN, 'ko': '가족', 'level': 2,
                    'example': '家族と一緒に旅行します。', 'ex_highlight': [0, 2], 'ex_ko': '가족과 함께 여행합니다.', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': '電車', 'pronunciation': 'でんしゃ', 'pos': PartOfSpeech.NOUN, 'ko': '전철', 'level': 2,
                    'example': '電車で会社に通います。', 'ex_highlight': [0, 2], 'ex_ko': '전철로 회사에 다닙니다.', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': '時間', 'pronunciation': 'じかん', 'pos': PartOfSpeech.NOUN, 'ko': '시간', 'level': 2,
                    'example': '時間がありません。', 'ex_highlight': [0, 2], 'ex_ko': '시간이 없습니다.', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': '天気', 'pronunciation': 'てんき', 'pos': PartOfSpeech.NOUN, 'ko': '날씨', 'level': 2,
                    'example': '今日は天気がいいですね。', 'ex_highlight': [3, 5], 'ex_ko': '오늘은 날씨가 좋네요.', 'ex_ko_highlight': [4, 6]
                },
                {
                    'text': '仕事', 'pronunciation': 'しごと', 'pos': PartOfSpeech.NOUN, 'ko': '일, 직장', 'level': 2,
                    'example': '仕事が忙しいです。', 'ex_highlight': [0, 2], 'ex_ko': '일이 바쁩니다.', 'ex_ko_highlight': [0, 1]
                },
                {
                    'text': '音楽', 'pronunciation': 'おんがく', 'pos': PartOfSpeech.NOUN, 'ko': '음악', 'level': 2,
                    'example': '音楽を聴くのが好きです。', 'ex_highlight': [0, 2], 'ex_ko': '음악 듣는 것을 좋아합니다.', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': '写真', 'pronunciation': 'しゃしん', 'pos': PartOfSpeech.NOUN, 'ko': '사진', 'level': 2,
                    'example': '写真を撮ってもいいですか。', 'ex_highlight': [0, 2], 'ex_ko': '사진을 찍어도 될까요?', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': '部屋', 'pronunciation': 'へや', 'pos': PartOfSpeech.NOUN, 'ko': '방', 'level': 2,
                    'example': '部屋を掃除しました。', 'ex_highlight': [0, 2], 'ex_ko': '방을 청소했습니다.', 'ex_ko_highlight': [0, 1]
                },
                # 동사 (10개)
                {
                    'text': '食べる', 'pronunciation': 'たべる', 'pos': PartOfSpeech.VERB, 'ko': '먹다', 'level': 1,
                    'grammar': {'type': '一段動詞', 'te_form': '食べて', 'past': '食べた'},
                    'example': '朝ごはんを食べます。', 'ex_highlight': [5, 8], 'ex_ko': '아침밥을 먹습니다.', 'ex_ko_highlight': [5, 9]
                },
                {
                    'text': '飲む', 'pronunciation': 'のむ', 'pos': PartOfSpeech.VERB, 'ko': '마시다', 'level': 1,
                    'grammar': {'type': '五段動詞', 'te_form': '飲んで', 'past': '飲んだ'},
                    'example': 'お茶を飲みませんか。', 'ex_highlight': [3, 5], 'ex_ko': '차를 마시지 않겠어요?', 'ex_ko_highlight': [3, 6]
                },
                {
                    'text': '行く', 'pronunciation': 'いく', 'pos': PartOfSpeech.VERB, 'ko': '가다', 'level': 1,
                    'grammar': {'type': '五段動詞', 'te_form': '行って', 'past': '行った'},
                    'example': '明日東京に行きます。', 'ex_highlight': [5, 7], 'ex_ko': '내일 도쿄에 갑니다.', 'ex_ko_highlight': [7, 10]
                },
                {
                    'text': '来る', 'pronunciation': 'くる', 'pos': PartOfSpeech.VERB, 'ko': '오다', 'level': 1,
                    'grammar': {'type': 'カ変動詞', 'te_form': '来て', 'past': '来た'},
                    'example': '友達が家に来ます。', 'ex_highlight': [5, 7], 'ex_ko': '친구가 집에 옵니다.', 'ex_ko_highlight': [7, 10]
                },
                {
                    'text': '見る', 'pronunciation': 'みる', 'pos': PartOfSpeech.VERB, 'ko': '보다', 'level': 1,
                    'grammar': {'type': '一段動詞', 'te_form': '見て', 'past': '見た'},
                    'example': 'テレビを見ています。', 'ex_highlight': [4, 6], 'ex_ko': '텔레비전을 보고 있습니다.', 'ex_ko_highlight': [6, 8]
                },
                {
                    'text': '書く', 'pronunciation': 'かく', 'pos': PartOfSpeech.VERB, 'ko': '쓰다', 'level': 1,
                    'grammar': {'type': '五段動詞', 'te_form': '書いて', 'past': '書いた'},
                    'example': '手紙を書きます。', 'ex_highlight': [3, 5], 'ex_ko': '편지를 씁니다.', 'ex_ko_highlight': [4, 7]
                },
                {
                    'text': '読む', 'pronunciation': 'よむ', 'pos': PartOfSpeech.VERB, 'ko': '읽다', 'level': 1,
                    'grammar': {'type': '五段動詞', 'te_form': '読んで', 'past': '読んだ'},
                    'example': '毎日新聞を読みます。', 'ex_highlight': [5, 7], 'ex_ko': '매일 신문을 읽습니다.', 'ex_ko_highlight': [7, 11]
                },
                {
                    'text': '話す', 'pronunciation': 'はなす', 'pos': PartOfSpeech.VERB, 'ko': '말하다', 'level': 2,
                    'grammar': {'type': '五段動詞', 'te_form': '話して', 'past': '話した'},
                    'example': '日本語を話せますか。', 'ex_highlight': [4, 6], 'ex_ko': '일본어를 할 수 있어요?', 'ex_ko_highlight': [5, 6]
                },
                {
                    'text': '聞く', 'pronunciation': 'きく', 'pos': PartOfSpeech.VERB, 'ko': '듣다, 묻다', 'level': 1,
                    'grammar': {'type': '五段動詞', 'te_form': '聞いて', 'past': '聞いた'},
                    'example': '音楽を聞きます。', 'ex_highlight': [3, 5], 'ex_ko': '음악을 듣습니다.', 'ex_ko_highlight': [4, 7]
                },
                {
                    'text': '買う', 'pronunciation': 'かう', 'pos': PartOfSpeech.VERB, 'ko': '사다', 'level': 1,
                    'grammar': {'type': '五段動詞', 'te_form': '買って', 'past': '買った'},
                    'example': 'デパートで服を買います。', 'ex_highlight': [7, 9], 'ex_ko': '백화점에서 옷을 삽니다.', 'ex_ko_highlight': [9, 12]
                },
                # 형용사 (5개)
                {
                    'text': '大きい', 'pronunciation': 'おおきい', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '크다', 'level': 1,
                    'grammar': {'type': 'い形容詞'},
                    'example': 'この犬は大きいです。', 'ex_highlight': [4, 7], 'ex_ko': '이 개는 큽니다.', 'ex_ko_highlight': [5, 8]
                },
                {
                    'text': '小さい', 'pronunciation': 'ちいさい', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '작다', 'level': 1,
                    'grammar': {'type': 'い形容詞'},
                    'example': '小さい声で話してください。', 'ex_highlight': [0, 3], 'ex_ko': '작은 목소리로 말해주세요.', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': '美味しい', 'pronunciation': 'おいしい', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '맛있다', 'level': 1,
                    'grammar': {'type': 'い形容詞'},
                    'example': 'この料理は美味しいです。', 'ex_highlight': [5, 8], 'ex_ko': '이 요리는 맛있습니다.', 'ex_ko_highlight': [6, 10]
                },
                {
                    'text': '楽しい', 'pronunciation': 'たのしい', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '즐겁다', 'level': 1,
                    'grammar': {'type': 'い形容詞'},
                    'example': '旅行は楽しかったです。', 'ex_highlight': [3, 6], 'ex_ko': '여행은 즐거웠습니다.', 'ex_ko_highlight': [4, 9]
                },
                {
                    'text': '静か', 'pronunciation': 'しずか', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '조용하다', 'level': 2,
                    'grammar': {'type': 'な形容詞'},
                    'example': 'この場所は静かです。', 'ex_highlight': [5, 7], 'ex_ko': '이 장소는 조용합니다.', 'ex_ko_highlight': [6, 10]
                },
            ]

            for word_data in japanese_words:
                # Convert hiragana pronunciation to romaji
                romaji = hiragana_to_romaji(word_data['pronunciation'])
                grammar = word_data.get('grammar', {'romanji': romaji})
                if 'romanji' not in grammar:
                    grammar['romanji'] = romaji

                word, created = Word.objects.get_or_create(
                    language=japanese,
                    text=word_data['text'],
                    category=WordCategory.WORD,
                    defaults={
                        'pronunciation': word_data['pronunciation'],
                        'part_of_speech': word_data['pos'],
                        'difficulty_level': word_data['level'],
                        'grammar': grammar,
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  생성: {word_data['text']} ({japanese.code})")

                # 한국어 번역
                WordTranslation.objects.get_or_create(
                    word=word,
                    language=korean,
                    defaults={'translated_text': word_data['ko']}
                )

                # 예문
                if word_data.get('example'):
                    example, _ = Example.objects.get_or_create(
                        word=word,
                        sentence=word_data['example'],
                        defaults={'highlight_indices': word_data.get('ex_highlight', [])}
                    )
                    if word_data.get('ex_ko'):
                        ex_trans, created = ExampleTranslation.objects.get_or_create(
                            example=example,
                            language=korean,
                            defaults={
                                'translated_sentence': word_data['ex_ko'],
                                'highlight_indices': word_data.get('ex_ko_highlight', [])
                            }
                        )
                        # 기존 데이터도 업데이트
                        if not created and word_data.get('ex_ko_highlight'):
                            ex_trans.highlight_indices = word_data['ex_ko_highlight']
                            ex_trans.save()

        # ==================== 영어 단어 (30개) ====================
        if english:
            english_words = [
                # 명사 (15개)
                {
                    'text': 'cat', 'pronunciation': '/kæt/', 'pos': PartOfSpeech.NOUN, 'ko': '고양이', 'level': 1,
                    'example': 'The cat is sleeping on the sofa.', 'ex_highlight': [4, 7], 'ex_ko': '고양이가 소파에서 자고 있습니다.', 'ex_ko_highlight': [0, 3]
                },
                {
                    'text': 'dog', 'pronunciation': '/dɔːɡ/', 'pos': PartOfSpeech.NOUN, 'ko': '개', 'level': 1,
                    'example': 'My dog loves to play fetch.', 'ex_highlight': [3, 6], 'ex_ko': '내 개는 공 던지기 놀이를 좋아합니다.', 'ex_ko_highlight': [2, 3]
                },
                {
                    'text': 'water', 'pronunciation': '/ˈwɔːtər/', 'pos': PartOfSpeech.NOUN, 'ko': '물', 'level': 1,
                    'example': 'Please give me some water.', 'ex_highlight': [20, 25], 'ex_ko': '물 좀 주세요.', 'ex_ko_highlight': [0, 1]
                },
                {
                    'text': 'book', 'pronunciation': '/bʊk/', 'pos': PartOfSpeech.NOUN, 'ko': '책', 'level': 1,
                    'example': 'I read a book every night.', 'ex_highlight': [9, 13], 'ex_ko': '나는 매일 밤 책을 읽습니다.', 'ex_ko_highlight': [8, 9]
                },
                {
                    'text': 'school', 'pronunciation': '/skuːl/', 'pos': PartOfSpeech.NOUN, 'ko': '학교', 'level': 1,
                    'example': 'The school is near my house.', 'ex_highlight': [4, 10], 'ex_ko': '학교는 내 집 근처에 있습니다.', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': 'friend', 'pronunciation': '/frend/', 'pos': PartOfSpeech.NOUN, 'ko': '친구', 'level': 1,
                    'example': 'My best friend lives in Seoul.', 'ex_highlight': [8, 14], 'ex_ko': '내 가장 친한 친구는 서울에 삽니다.', 'ex_ko_highlight': [7, 9]
                },
                {
                    'text': 'family', 'pronunciation': '/ˈfæməli/', 'pos': PartOfSpeech.NOUN, 'ko': '가족', 'level': 1,
                    'example': 'I love my family very much.', 'ex_highlight': [10, 16], 'ex_ko': '나는 내 가족을 매우 사랑합니다.', 'ex_ko_highlight': [5, 7]
                },
                {
                    'text': 'teacher', 'pronunciation': '/ˈtiːtʃər/', 'pos': PartOfSpeech.NOUN, 'ko': '선생님', 'level': 1,
                    'example': 'The teacher explained the lesson.', 'ex_highlight': [4, 11], 'ex_ko': '선생님이 수업을 설명했습니다.', 'ex_ko_highlight': [0, 3]
                },
                {
                    'text': 'student', 'pronunciation': '/ˈstuːdənt/', 'pos': PartOfSpeech.NOUN, 'ko': '학생', 'level': 1,
                    'example': 'She is a diligent student.', 'ex_highlight': [18, 25], 'ex_ko': '그녀는 부지런한 학생입니다.', 'ex_ko_highlight': [8, 10]
                },
                {
                    'text': 'city', 'pronunciation': '/ˈsɪti/', 'pos': PartOfSpeech.NOUN, 'ko': '도시', 'level': 1,
                    'example': 'This city has many tall buildings.', 'ex_highlight': [5, 9], 'ex_ko': '이 도시에는 높은 건물이 많습니다.', 'ex_ko_highlight': [2, 4]
                },
                {
                    'text': 'country', 'pronunciation': '/ˈkʌntri/', 'pos': PartOfSpeech.NOUN, 'ko': '나라, 시골', 'level': 1,
                    'example': 'Korea is a beautiful country.', 'ex_highlight': [21, 28], 'ex_ko': '한국은 아름다운 나라입니다.', 'ex_ko_highlight': [8, 10]
                },
                {
                    'text': 'food', 'pronunciation': '/fuːd/', 'pos': PartOfSpeech.NOUN, 'ko': '음식', 'level': 1,
                    'example': 'Korean food is very delicious.', 'ex_highlight': [7, 11], 'ex_ko': '한국 음식은 매우 맛있습니다.', 'ex_ko_highlight': [3, 5]
                },
                {
                    'text': 'music', 'pronunciation': '/ˈmjuːzɪk/', 'pos': PartOfSpeech.NOUN, 'ko': '음악', 'level': 1,
                    'example': 'I listen to music every day.', 'ex_highlight': [12, 17], 'ex_ko': '나는 매일 음악을 듣습니다.', 'ex_ko_highlight': [5, 7]
                },
                {
                    'text': 'weather', 'pronunciation': '/ˈweðər/', 'pos': PartOfSpeech.NOUN, 'ko': '날씨', 'level': 2,
                    'example': 'The weather is nice today.', 'ex_highlight': [4, 11], 'ex_ko': '오늘 날씨가 좋습니다.', 'ex_ko_highlight': [3, 5]
                },
                {
                    'text': 'computer', 'pronunciation': '/kəmˈpjuːtər/', 'pos': PartOfSpeech.NOUN, 'ko': '컴퓨터', 'level': 2,
                    'example': 'I use a computer for work.', 'ex_highlight': [8, 16], 'ex_ko': '나는 일하기 위해 컴퓨터를 사용합니다.', 'ex_ko_highlight': [10, 13]
                },
                # 동사 (10개)
                {
                    'text': 'eat', 'pronunciation': '/iːt/', 'pos': PartOfSpeech.VERB, 'ko': '먹다', 'level': 1,
                    'grammar': {'past': 'ate', 'past_participle': 'eaten', '3rd_singular': 'eats'},
                    'example': 'I eat breakfast at 7 AM.', 'ex_highlight': [2, 5], 'ex_ko': '나는 아침 7시에 아침을 먹습니다.', 'ex_ko_highlight': [14, 18]
                },
                {
                    'text': 'drink', 'pronunciation': '/drɪŋk/', 'pos': PartOfSpeech.VERB, 'ko': '마시다', 'level': 1,
                    'grammar': {'past': 'drank', 'past_participle': 'drunk', '3rd_singular': 'drinks'},
                    'example': 'I drink coffee every morning.', 'ex_highlight': [2, 7], 'ex_ko': '나는 매일 아침 커피를 마십니다.', 'ex_ko_highlight': [13, 17]
                },
                {
                    'text': 'go', 'pronunciation': '/ɡoʊ/', 'pos': PartOfSpeech.VERB, 'ko': '가다', 'level': 1,
                    'grammar': {'past': 'went', 'past_participle': 'gone', '3rd_singular': 'goes'},
                    'example': 'I go to work by subway.', 'ex_highlight': [2, 4], 'ex_ko': '나는 지하철로 출근합니다.', 'ex_ko_highlight': [8, 10]
                },
                {
                    'text': 'come', 'pronunciation': '/kʌm/', 'pos': PartOfSpeech.VERB, 'ko': '오다', 'level': 1,
                    'grammar': {'past': 'came', 'past_participle': 'come', '3rd_singular': 'comes'},
                    'example': 'Please come to my party.', 'ex_highlight': [7, 11], 'ex_ko': '내 파티에 와주세요.', 'ex_ko_highlight': [6, 7]
                },
                {
                    'text': 'see', 'pronunciation': '/siː/', 'pos': PartOfSpeech.VERB, 'ko': '보다', 'level': 1,
                    'grammar': {'past': 'saw', 'past_participle': 'seen', '3rd_singular': 'sees'},
                    'example': 'I can see the mountain from here.', 'ex_highlight': [6, 9], 'ex_ko': '여기서 산이 보입니다.', 'ex_ko_highlight': [7, 10]
                },
                {
                    'text': 'write', 'pronunciation': '/raɪt/', 'pos': PartOfSpeech.VERB, 'ko': '쓰다', 'level': 1,
                    'grammar': {'past': 'wrote', 'past_participle': 'written', '3rd_singular': 'writes'},
                    'example': 'I write in my diary every day.', 'ex_highlight': [2, 7], 'ex_ko': '나는 매일 일기를 씁니다.', 'ex_ko_highlight': [10, 13]
                },
                {
                    'text': 'read', 'pronunciation': '/riːd/', 'pos': PartOfSpeech.VERB, 'ko': '읽다', 'level': 1,
                    'grammar': {'past': 'read', 'past_participle': 'read', '3rd_singular': 'reads'},
                    'example': 'She reads books every weekend.', 'ex_highlight': [4, 9], 'ex_ko': '그녀는 매주 주말 책을 읽습니다.', 'ex_ko_highlight': [13, 17]
                },
                {
                    'text': 'speak', 'pronunciation': '/spiːk/', 'pos': PartOfSpeech.VERB, 'ko': '말하다', 'level': 1,
                    'grammar': {'past': 'spoke', 'past_participle': 'spoken', '3rd_singular': 'speaks'},
                    'example': 'Can you speak Korean?', 'ex_highlight': [8, 13], 'ex_ko': '한국어 할 수 있어요?', 'ex_ko_highlight': [4, 5]
                },
                {
                    'text': 'listen', 'pronunciation': '/ˈlɪsən/', 'pos': PartOfSpeech.VERB, 'ko': '듣다', 'level': 1,
                    'grammar': {'past': 'listened', 'past_participle': 'listened', '3rd_singular': 'listens'},
                    'example': 'I listen to podcasts while commuting.', 'ex_highlight': [2, 8], 'ex_ko': '나는 출퇴근하면서 팟캐스트를 듣습니다.', 'ex_ko_highlight': [16, 20]
                },
                {
                    'text': 'buy', 'pronunciation': '/baɪ/', 'pos': PartOfSpeech.VERB, 'ko': '사다', 'level': 1,
                    'grammar': {'past': 'bought', 'past_participle': 'bought', '3rd_singular': 'buys'},
                    'example': 'I want to buy a new phone.', 'ex_highlight': [10, 13], 'ex_ko': '새 휴대폰을 사고 싶습니다.', 'ex_ko_highlight': [7, 9]
                },
                # 형용사 (5개)
                {
                    'text': 'big', 'pronunciation': '/bɪɡ/', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '큰', 'level': 1,
                    'grammar': {'comparative': 'bigger', 'superlative': 'biggest'},
                    'example': 'This is a big house.', 'ex_highlight': [10, 13], 'ex_ko': '이것은 큰 집입니다.', 'ex_ko_highlight': [4, 5]
                },
                {
                    'text': 'small', 'pronunciation': '/smɔːl/', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '작은', 'level': 1,
                    'grammar': {'comparative': 'smaller', 'superlative': 'smallest'},
                    'example': 'I have a small garden.', 'ex_highlight': [9, 14], 'ex_ko': '나는 작은 정원이 있습니다.', 'ex_ko_highlight': [3, 5]
                },
                {
                    'text': 'happy', 'pronunciation': '/ˈhæpi/', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '행복한', 'level': 1,
                    'grammar': {'comparative': 'happier', 'superlative': 'happiest'},
                    'example': 'She looks very happy today.', 'ex_highlight': [15, 20], 'ex_ko': '그녀는 오늘 매우 행복해 보입니다.', 'ex_ko_highlight': [10, 13]
                },
                {
                    'text': 'beautiful', 'pronunciation': '/ˈbjuːtɪfəl/', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '아름다운', 'level': 2,
                    'grammar': {'comparative': 'more beautiful', 'superlative': 'most beautiful'},
                    'example': 'The sunset is beautiful.', 'ex_highlight': [14, 23], 'ex_ko': '노을이 아름답습니다.', 'ex_ko_highlight': [4, 9]
                },
                {
                    'text': 'difficult', 'pronunciation': '/ˈdɪfɪkəlt/', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '어려운', 'level': 2,
                    'grammar': {'comparative': 'more difficult', 'superlative': 'most difficult'},
                    'example': 'This problem is difficult.', 'ex_highlight': [16, 25], 'ex_ko': '이 문제는 어렵습니다.', 'ex_ko_highlight': [6, 10]
                },
            ]

            for word_data in english_words:
                grammar = word_data.get('grammar', {})
                word, created = Word.objects.get_or_create(
                    language=english,
                    text=word_data['text'],
                    category=WordCategory.WORD,
                    defaults={
                        'pronunciation': word_data['pronunciation'],
                        'part_of_speech': word_data['pos'],
                        'difficulty_level': word_data['level'],
                        'grammar': grammar,
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

                if word_data.get('example'):
                    example, _ = Example.objects.get_or_create(
                        word=word,
                        sentence=word_data['example'],
                        defaults={'highlight_indices': word_data.get('ex_highlight', [])}
                    )
                    if word_data.get('ex_ko'):
                        ex_trans, created = ExampleTranslation.objects.get_or_create(
                            example=example,
                            language=korean,
                            defaults={
                                'translated_sentence': word_data['ex_ko'],
                                'highlight_indices': word_data.get('ex_ko_highlight', [])
                            }
                        )
                        if not created and word_data.get('ex_ko_highlight'):
                            ex_trans.highlight_indices = word_data['ex_ko_highlight']
                            ex_trans.save()

        # ==================== 스페인어 단어 (30개) ====================
        if spanish:
            spanish_words = [
                # 명사 (15개) - 성별 표기
                {
                    'text': 'gato', 'pronunciation': '/ˈɡa.to/', 'pos': PartOfSpeech.NOUN, 'ko': '고양이', 'level': 1,
                    'grammar': {'gender': 'masculino', 'plural': 'gatos', 'article': 'el'},
                    'example': 'El gato duerme en el sofá.', 'ex_highlight': [3, 7], 'ex_ko': '고양이가 소파에서 잡니다.', 'ex_ko_highlight': [0, 3]
                },
                {
                    'text': 'perro', 'pronunciation': '/ˈpe.ro/', 'pos': PartOfSpeech.NOUN, 'ko': '개', 'level': 1,
                    'grammar': {'gender': 'masculino', 'plural': 'perros', 'article': 'el'},
                    'example': 'Mi perro es muy juguetón.', 'ex_highlight': [3, 8], 'ex_ko': '내 개는 매우 장난기가 많습니다.', 'ex_ko_highlight': [2, 3]
                },
                {
                    'text': 'agua', 'pronunciation': '/ˈa.ɣwa/', 'pos': PartOfSpeech.NOUN, 'ko': '물', 'level': 1,
                    'grammar': {'gender': 'femenino', 'plural': 'aguas', 'article': 'el (특수)', 'note': '여성명사이지만 el agua 사용'},
                    'example': 'El agua está fría.', 'ex_highlight': [3, 7], 'ex_ko': '물이 차갑습니다.', 'ex_ko_highlight': [0, 1]
                },
                {
                    'text': 'libro', 'pronunciation': '/ˈli.βɾo/', 'pos': PartOfSpeech.NOUN, 'ko': '책', 'level': 1,
                    'grammar': {'gender': 'masculino', 'plural': 'libros', 'article': 'el'},
                    'example': 'Este libro es interesante.', 'ex_highlight': [5, 10], 'ex_ko': '이 책은 흥미롭습니다.', 'ex_ko_highlight': [2, 3]
                },
                {
                    'text': 'escuela', 'pronunciation': '/esˈkwe.la/', 'pos': PartOfSpeech.NOUN, 'ko': '학교', 'level': 1,
                    'grammar': {'gender': 'femenino', 'plural': 'escuelas', 'article': 'la'},
                    'example': 'La escuela está cerca de mi casa.', 'ex_highlight': [3, 10], 'ex_ko': '학교는 우리 집 근처에 있습니다.', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': 'amigo', 'pronunciation': '/aˈmi.ɣo/', 'pos': PartOfSpeech.NOUN, 'ko': '친구 (남)', 'level': 1,
                    'grammar': {'gender': 'masculino', 'plural': 'amigos', 'article': 'el', 'feminine': 'amiga'},
                    'example': 'Mi amigo vive en Madrid.', 'ex_highlight': [3, 8], 'ex_ko': '내 친구는 마드리드에 삽니다.', 'ex_ko_highlight': [2, 4]
                },
                {
                    'text': 'familia', 'pronunciation': '/faˈmi.lja/', 'pos': PartOfSpeech.NOUN, 'ko': '가족', 'level': 1,
                    'grammar': {'gender': 'femenino', 'plural': 'familias', 'article': 'la'},
                    'example': 'Mi familia es grande.', 'ex_highlight': [3, 10], 'ex_ko': '내 가족은 대가족입니다.', 'ex_ko_highlight': [2, 4]
                },
                {
                    'text': 'casa', 'pronunciation': '/ˈka.sa/', 'pos': PartOfSpeech.NOUN, 'ko': '집', 'level': 1,
                    'grammar': {'gender': 'femenino', 'plural': 'casas', 'article': 'la'},
                    'example': 'La casa es muy bonita.', 'ex_highlight': [3, 7], 'ex_ko': '그 집은 매우 예쁩니다.', 'ex_ko_highlight': [2, 3]
                },
                {
                    'text': 'comida', 'pronunciation': '/koˈmi.ða/', 'pos': PartOfSpeech.NOUN, 'ko': '음식', 'level': 1,
                    'grammar': {'gender': 'femenino', 'plural': 'comidas', 'article': 'la'},
                    'example': 'La comida mexicana es deliciosa.', 'ex_highlight': [3, 9], 'ex_ko': '멕시코 음식은 맛있습니다.', 'ex_ko_highlight': [4, 6]
                },
                {
                    'text': 'música', 'pronunciation': '/ˈmu.si.ka/', 'pos': PartOfSpeech.NOUN, 'ko': '음악', 'level': 1,
                    'grammar': {'gender': 'femenino', 'plural': 'músicas', 'article': 'la'},
                    'example': 'Me gusta la música latina.', 'ex_highlight': [12, 18], 'ex_ko': '나는 라틴 음악을 좋아합니다.', 'ex_ko_highlight': [6, 8]
                },
                {
                    'text': 'ciudad', 'pronunciation': '/θjuˈðað/', 'pos': PartOfSpeech.NOUN, 'ko': '도시', 'level': 1,
                    'grammar': {'gender': 'femenino', 'plural': 'ciudades', 'article': 'la'},
                    'example': 'Barcelona es una ciudad hermosa.', 'ex_highlight': [17, 23], 'ex_ko': '바르셀로나는 아름다운 도시입니다.', 'ex_ko_highlight': [11, 13]
                },
                {
                    'text': 'país', 'pronunciation': '/paˈis/', 'pos': PartOfSpeech.NOUN, 'ko': '나라', 'level': 1,
                    'grammar': {'gender': 'masculino', 'plural': 'países', 'article': 'el'},
                    'example': 'España es un país europeo.', 'ex_highlight': [13, 17], 'ex_ko': '스페인은 유럽 국가입니다.', 'ex_ko_highlight': [8, 10]
                },
                {
                    'text': 'tiempo', 'pronunciation': '/ˈtjem.po/', 'pos': PartOfSpeech.NOUN, 'ko': '시간, 날씨', 'level': 1,
                    'grammar': {'gender': 'masculino', 'plural': 'tiempos', 'article': 'el'},
                    'example': 'No tengo tiempo hoy.', 'ex_highlight': [9, 15], 'ex_ko': '오늘은 시간이 없습니다.', 'ex_ko_highlight': [4, 6]
                },
                {
                    'text': 'trabajo', 'pronunciation': '/tɾaˈβa.xo/', 'pos': PartOfSpeech.NOUN, 'ko': '일, 직장', 'level': 1,
                    'grammar': {'gender': 'masculino', 'plural': 'trabajos', 'article': 'el'},
                    'example': 'Mi trabajo es interesante.', 'ex_highlight': [3, 10], 'ex_ko': '내 일은 흥미롭습니다.', 'ex_ko_highlight': [2, 3]
                },
                {
                    'text': 'coche', 'pronunciation': '/ˈko.tʃe/', 'pos': PartOfSpeech.NOUN, 'ko': '자동차', 'level': 1,
                    'grammar': {'gender': 'masculino', 'plural': 'coches', 'article': 'el'},
                    'example': 'Compré un coche nuevo.', 'ex_highlight': [10, 15], 'ex_ko': '새 차를 샀습니다.', 'ex_ko_highlight': [2, 3]
                },
                # 동사 (10개) - 동사변화 포함
                {
                    'text': 'comer', 'pronunciation': '/koˈmeɾ/', 'pos': PartOfSpeech.VERB, 'ko': '먹다', 'level': 1,
                    'grammar': {
                        'type': '-er 동사', 'infinitive': 'comer',
                        'present': {'yo': 'como', 'tú': 'comes', 'él': 'come', 'nosotros': 'comemos', 'ellos': 'comen'},
                        'past': 'comí', 'future': 'comeré'
                    },
                    'example': 'Yo como paella los domingos.', 'ex_highlight': [3, 7], 'ex_ko': '나는 일요일에 파에야를 먹습니다.', 'ex_ko_highlight': [13, 17]
                },
                {
                    'text': 'beber', 'pronunciation': '/beˈβeɾ/', 'pos': PartOfSpeech.VERB, 'ko': '마시다', 'level': 1,
                    'grammar': {
                        'type': '-er 동사', 'infinitive': 'beber',
                        'present': {'yo': 'bebo', 'tú': 'bebes', 'él': 'bebe', 'nosotros': 'bebemos', 'ellos': 'beben'},
                        'past': 'bebí', 'future': 'beberé'
                    },
                    'example': 'Bebo café por la mañana.', 'ex_highlight': [0, 4], 'ex_ko': '아침에 커피를 마십니다.', 'ex_ko_highlight': [8, 12]
                },
                {
                    'text': 'hablar', 'pronunciation': '/aˈβlaɾ/', 'pos': PartOfSpeech.VERB, 'ko': '말하다', 'level': 1,
                    'grammar': {
                        'type': '-ar 동사', 'infinitive': 'hablar',
                        'present': {'yo': 'hablo', 'tú': 'hablas', 'él': 'habla', 'nosotros': 'hablamos', 'ellos': 'hablan'},
                        'past': 'hablé', 'future': 'hablaré'
                    },
                    'example': '¿Hablas español?', 'ex_highlight': [1, 7], 'ex_ko': '스페인어 하세요?', 'ex_ko_highlight': [5, 8]
                },
                {
                    'text': 'vivir', 'pronunciation': '/biˈβiɾ/', 'pos': PartOfSpeech.VERB, 'ko': '살다', 'level': 1,
                    'grammar': {
                        'type': '-ir 동사', 'infinitive': 'vivir',
                        'present': {'yo': 'vivo', 'tú': 'vives', 'él': 'vive', 'nosotros': 'vivimos', 'ellos': 'viven'},
                        'past': 'viví', 'future': 'viviré'
                    },
                    'example': 'Vivo en Seúl.', 'ex_highlight': [0, 4], 'ex_ko': '서울에 삽니다.', 'ex_ko_highlight': [4, 7]
                },
                {
                    'text': 'ir', 'pronunciation': '/iɾ/', 'pos': PartOfSpeech.VERB, 'ko': '가다', 'level': 1,
                    'grammar': {
                        'type': '불규칙 동사', 'infinitive': 'ir',
                        'present': {'yo': 'voy', 'tú': 'vas', 'él': 'va', 'nosotros': 'vamos', 'ellos': 'van'},
                        'past': 'fui', 'future': 'iré'
                    },
                    'example': 'Voy al supermercado.', 'ex_highlight': [0, 3], 'ex_ko': '슈퍼마켓에 갑니다.', 'ex_ko_highlight': [6, 9]
                },
                {
                    'text': 'venir', 'pronunciation': '/beˈniɾ/', 'pos': PartOfSpeech.VERB, 'ko': '오다', 'level': 1,
                    'grammar': {
                        'type': '불규칙 동사', 'infinitive': 'venir',
                        'present': {'yo': 'vengo', 'tú': 'vienes', 'él': 'viene', 'nosotros': 'venimos', 'ellos': 'vienen'},
                        'past': 'vine', 'future': 'vendré'
                    },
                    'example': '¿Vienes a la fiesta?', 'ex_highlight': [1, 7], 'ex_ko': '파티에 올 거야?', 'ex_ko_highlight': [4, 5]
                },
                {
                    'text': 'escribir', 'pronunciation': '/eskɾiˈβiɾ/', 'pos': PartOfSpeech.VERB, 'ko': '쓰다', 'level': 1,
                    'grammar': {
                        'type': '-ir 동사', 'infinitive': 'escribir',
                        'present': {'yo': 'escribo', 'tú': 'escribes', 'él': 'escribe', 'nosotros': 'escribimos', 'ellos': 'escriben'},
                        'past': 'escribí', 'future': 'escribiré'
                    },
                    'example': 'Escribo un correo electrónico.', 'ex_highlight': [0, 7], 'ex_ko': '이메일을 씁니다.', 'ex_ko_highlight': [5, 8]
                },
                {
                    'text': 'leer', 'pronunciation': '/leˈeɾ/', 'pos': PartOfSpeech.VERB, 'ko': '읽다', 'level': 1,
                    'grammar': {
                        'type': '-er 동사', 'infinitive': 'leer',
                        'present': {'yo': 'leo', 'tú': 'lees', 'él': 'lee', 'nosotros': 'leemos', 'ellos': 'leen'},
                        'past': 'leí', 'future': 'leeré'
                    },
                    'example': 'Leo el periódico todos los días.', 'ex_highlight': [0, 3], 'ex_ko': '매일 신문을 읽습니다.', 'ex_ko_highlight': [7, 11]
                },
                {
                    'text': 'comprar', 'pronunciation': '/komˈpɾaɾ/', 'pos': PartOfSpeech.VERB, 'ko': '사다', 'level': 1,
                    'grammar': {
                        'type': '-ar 동사', 'infinitive': 'comprar',
                        'present': {'yo': 'compro', 'tú': 'compras', 'él': 'compra', 'nosotros': 'compramos', 'ellos': 'compran'},
                        'past': 'compré', 'future': 'compraré'
                    },
                    'example': 'Quiero comprar un regalo.', 'ex_highlight': [7, 14], 'ex_ko': '선물을 사고 싶습니다.', 'ex_ko_highlight': [4, 6]
                },
                {
                    'text': 'ver', 'pronunciation': '/beɾ/', 'pos': PartOfSpeech.VERB, 'ko': '보다', 'level': 1,
                    'grammar': {
                        'type': '불규칙 동사', 'infinitive': 'ver',
                        'present': {'yo': 'veo', 'tú': 'ves', 'él': 've', 'nosotros': 'vemos', 'ellos': 'ven'},
                        'past': 'vi', 'future': 'veré'
                    },
                    'example': 'Veo la televisión por la noche.', 'ex_highlight': [0, 3], 'ex_ko': '밤에 텔레비전을 봅니다.', 'ex_ko_highlight': [9, 12]
                },
                # 형용사 (5개) - 성/수 변화 포함
                {
                    'text': 'grande', 'pronunciation': '/ˈɡɾan.de/', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '큰', 'level': 1,
                    'grammar': {'forms': {'m.sg': 'grande', 'f.sg': 'grande', 'm.pl': 'grandes', 'f.pl': 'grandes'}, 'before_noun': 'gran'},
                    'example': 'Es una casa grande.', 'ex_highlight': [12, 18], 'ex_ko': '큰 집입니다.', 'ex_ko_highlight': [0, 1]
                },
                {
                    'text': 'pequeño', 'pronunciation': '/peˈke.ɲo/', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '작은', 'level': 1,
                    'grammar': {'forms': {'m.sg': 'pequeño', 'f.sg': 'pequeña', 'm.pl': 'pequeños', 'f.pl': 'pequeñas'}},
                    'example': 'Tengo un perro pequeño.', 'ex_highlight': [15, 22], 'ex_ko': '작은 개가 있습니다.', 'ex_ko_highlight': [0, 2]
                },
                {
                    'text': 'bonito', 'pronunciation': '/boˈni.to/', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '예쁜', 'level': 1,
                    'grammar': {'forms': {'m.sg': 'bonito', 'f.sg': 'bonita', 'm.pl': 'bonitos', 'f.pl': 'bonitas'}},
                    'example': '¡Qué vestido tan bonito!', 'ex_highlight': [17, 23], 'ex_ko': '정말 예쁜 드레스네요!', 'ex_ko_highlight': [3, 5]
                },
                {
                    'text': 'feliz', 'pronunciation': '/feˈliθ/', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '행복한', 'level': 1,
                    'grammar': {'forms': {'m.sg': 'feliz', 'f.sg': 'feliz', 'm.pl': 'felices', 'f.pl': 'felices'}},
                    'example': 'Estoy muy feliz hoy.', 'ex_highlight': [10, 15], 'ex_ko': '오늘 매우 행복합니다.', 'ex_ko_highlight': [6, 10]
                },
                {
                    'text': 'difícil', 'pronunciation': '/diˈfi.θil/', 'pos': PartOfSpeech.ADJECTIVE, 'ko': '어려운', 'level': 2,
                    'grammar': {'forms': {'m.sg': 'difícil', 'f.sg': 'difícil', 'm.pl': 'difíciles', 'f.pl': 'difíciles'}},
                    'example': 'El examen es muy difícil.', 'ex_highlight': [17, 24], 'ex_ko': '시험이 매우 어렵습니다.', 'ex_ko_highlight': [7, 11]
                },
            ]

            for word_data in spanish_words:
                grammar = word_data.get('grammar', {})
                word, created = Word.objects.get_or_create(
                    language=spanish,
                    text=word_data['text'],
                    category=WordCategory.WORD,
                    defaults={
                        'pronunciation': word_data['pronunciation'],
                        'part_of_speech': word_data['pos'],
                        'difficulty_level': word_data['level'],
                        'grammar': grammar,
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

                if word_data.get('example'):
                    example, _ = Example.objects.get_or_create(
                        word=word,
                        sentence=word_data['example'],
                        defaults={'highlight_indices': word_data.get('ex_highlight', [])}
                    )
                    if word_data.get('ex_ko'):
                        ex_trans, created = ExampleTranslation.objects.get_or_create(
                            example=example,
                            language=korean,
                            defaults={
                                'translated_sentence': word_data['ex_ko'],
                                'highlight_indices': word_data.get('ex_ko_highlight', [])
                            }
                        )
                        if not created and word_data.get('ex_ko_highlight'):
                            ex_trans.highlight_indices = word_data['ex_ko_highlight']
                            ex_trans.save()

        self.stdout.write(self.style.SUCCESS(f'\n테스트 단어 로딩 완료! (새로 생성: {created_count}개)'))

        # 요약 출력
        total_words = Word.objects.filter(category=WordCategory.WORD).count()
        ja_words = Word.objects.filter(language=japanese, category=WordCategory.WORD).count() if japanese else 0
        en_words = Word.objects.filter(language=english, category=WordCategory.WORD).count() if english else 0
        es_words = Word.objects.filter(language=spanish, category=WordCategory.WORD).count() if spanish else 0
        total_examples = Example.objects.count()

        self.stdout.write(f'\n=== 요약 ===')
        self.stdout.write(f'총 단어 수: {total_words}개')
        self.stdout.write(f'  - 일본어: {ja_words}개')
        self.stdout.write(f'  - 영어: {en_words}개')
        self.stdout.write(f'  - 스페인어: {es_words}개')
        self.stdout.write(f'총 예문 수: {total_examples}개')
