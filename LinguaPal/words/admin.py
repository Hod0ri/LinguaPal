from django.contrib import admin
from .models import Word, WordTranslation, Example, ExampleTranslation


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
