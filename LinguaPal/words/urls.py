from django.urls import path
from .views import (
    # Word
    admin_word_list,
    admin_word_create,
    admin_word_detail,
    admin_word_update,
    admin_word_delete,
    # WordTranslation
    admin_word_translation_list,
    admin_word_translation_create,
    admin_word_translation_update,
    admin_word_translation_delete,
    # Example
    admin_example_list,
    admin_example_create,
    admin_example_update,
    admin_example_delete,
    # ExampleTranslation
    admin_example_translation_create,
    admin_example_translation_update,
    admin_example_translation_delete,
)

app_name = 'words'

urlpatterns = [
    # Word CRUD
    path('admin/words', admin_word_list, name='admin_word_list'),
    path('admin/words/create', admin_word_create, name='admin_word_create'),
    path('admin/words/<int:pk>', admin_word_detail, name='admin_word_detail'),
    path('admin/words/<int:pk>/update', admin_word_update, name='admin_word_update'),
    path('admin/words/<int:pk>/delete', admin_word_delete, name='admin_word_delete'),

    # WordTranslation CRUD
    path('admin/words/<int:word_id>/translations',
         admin_word_translation_list, name='admin_word_translation_list'),
    path('admin/words/<int:word_id>/translations/create',
         admin_word_translation_create, name='admin_word_translation_create'),
    path('admin/words/<int:word_id>/translations/<int:translation_id>/update',
         admin_word_translation_update, name='admin_word_translation_update'),
    path('admin/words/<int:word_id>/translations/<int:translation_id>/delete',
         admin_word_translation_delete, name='admin_word_translation_delete'),

    # Example CRUD
    path('admin/words/<int:word_id>/examples',
         admin_example_list, name='admin_example_list'),
    path('admin/words/<int:word_id>/examples/create',
         admin_example_create, name='admin_example_create'),
    path('admin/words/<int:word_id>/examples/<int:example_id>/update',
         admin_example_update, name='admin_example_update'),
    path('admin/words/<int:word_id>/examples/<int:example_id>/delete',
         admin_example_delete, name='admin_example_delete'),

    # ExampleTranslation CRUD
    path('admin/words/<int:word_id>/examples/<int:example_id>/translations/create',
         admin_example_translation_create, name='admin_example_translation_create'),
    path('admin/words/<int:word_id>/examples/<int:example_id>/translations/<int:translation_id>/update',
         admin_example_translation_update, name='admin_example_translation_update'),
    path('admin/words/<int:word_id>/examples/<int:example_id>/translations/<int:translation_id>/delete',
         admin_example_translation_delete, name='admin_example_translation_delete'),
]
