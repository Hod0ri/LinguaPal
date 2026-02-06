from django.contrib import admin
from .models import Word, WordTranslation, Example, ExampleTranslation, Vocabulary, VocabularyWord


class WordTranslationInline(admin.TabularInline):
    model = WordTranslation
    extra = 1


class ExampleInline(admin.TabularInline):
    model = Example
    extra = 1
    show_change_link = True


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ['text', 'language', 'part_of_speech', 'difficulty_level', 'is_active', 'created_at']
    list_filter = ['language', 'part_of_speech', 'difficulty_level', 'is_active']
    search_fields = ['text', 'pronunciation']
    ordering = ['-created_at']
    inlines = [WordTranslationInline, ExampleInline]


class ExampleTranslationInline(admin.TabularInline):
    model = ExampleTranslation
    extra = 1


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = ['word', 'sentence', 'created_at']
    list_filter = ['word__language']
    search_fields = ['sentence', 'word__text']
    inlines = [ExampleTranslationInline]


@admin.register(WordTranslation)
class WordTranslationAdmin(admin.ModelAdmin):
    list_display = ['word', 'language', 'translated_text', 'created_at']
    list_filter = ['language']
    search_fields = ['word__text', 'translated_text']


@admin.register(ExampleTranslation)
class ExampleTranslationAdmin(admin.ModelAdmin):
    list_display = ['example', 'language', 'translated_sentence', 'created_at']
    list_filter = ['language']
    search_fields = ['translated_sentence']


class VocabularyWordInline(admin.TabularInline):
    model = VocabularyWord
    extra = 1
    raw_id_fields = ['word']


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'language', 'word_count', 'is_active', 'created_at']
    list_filter = ['language', 'is_active', 'created_at']
    search_fields = ['name', 'user__email', 'description']
    ordering = ['-created_at']
    inlines = [VocabularyWordInline]

    def word_count(self, obj):
        """단어장에 포함된 단어 수"""
        return obj.words.count()
    word_count.short_description = '단어 수'


@admin.register(VocabularyWord)
class VocabularyWordAdmin(admin.ModelAdmin):
    list_display = ['vocabulary', 'word', 'added_at']
    list_filter = ['vocabulary__language', 'added_at']
    search_fields = ['vocabulary__name', 'word__text', 'notes']
    raw_id_fields = ['vocabulary', 'word']
