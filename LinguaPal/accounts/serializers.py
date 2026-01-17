from rest_framework import serializers
from .models import User, UserProfile, Language, Country


class LanguageSerializer(serializers.ModelSerializer):
    """언어 시리얼라이저"""
    class Meta:
        model = Language
        fields = ['id', 'code', 'name_ko', 'name_en']
        read_only_fields = ['id']


class CountrySerializer(serializers.ModelSerializer):
    """국가 시리얼라이저"""
    class Meta:
        model = Country
        fields = ['id', 'code', 'name_ko', 'name_en']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """사용자 프로필 시리얼라이저 (조회용)"""
    country = CountrySerializer(read_only=True)
    learning_languages = LanguageSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user_email', 'nickname', 'country', 'learning_languages', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_email', 'created_at', 'updated_at']


class UserProfileCreateSerializer(serializers.ModelSerializer):
    """사용자 프로필 생성 시리얼라이저"""
    learning_language_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        min_length=1,
        help_text="배우고자 하는 언어 ID 리스트"
    )

    class Meta:
        model = UserProfile
        fields = ['nickname', 'country', 'learning_language_ids']

    def validate_nickname(self, value):
        """Nickname validation"""
        if len(value) < 2:
            raise serializers.ValidationError("Nickname must be at least 2 characters long.")
        if len(value) > 50:
            raise serializers.ValidationError("Nickname cannot exceed 50 characters.")

        # Check for duplicate nickname (exclude own nickname for updates)
        if self.instance:
            if UserProfile.objects.exclude(pk=self.instance.pk).filter(nickname=value).exists():
                raise serializers.ValidationError("This nickname is already in use.")
        else:
            if UserProfile.objects.filter(nickname=value).exists():
                raise serializers.ValidationError("This nickname is already in use.")

        return value

    def validate_learning_language_ids(self, value):
        """Learning language IDs validation"""
        if not value:
            raise serializers.ValidationError("At least one language must be selected.")

        # Check if language IDs exist
        existing_ids = set(Language.objects.filter(id__in=value).values_list('id', flat=True))
        invalid_ids = set(value) - existing_ids

        if invalid_ids:
            raise serializers.ValidationError(f"Invalid language IDs: {invalid_ids}")

        return value

    def create(self, validated_data):
        """프로필 생성"""
        learning_language_ids = validated_data.pop('learning_language_ids')
        profile = UserProfile.objects.create(**validated_data)
        profile.learning_languages.set(learning_language_ids)
        return profile

    def update(self, instance, validated_data):
        """프로필 업데이트"""
        learning_language_ids = validated_data.pop('learning_language_ids', None)

        # 닉네임, 국가 업데이트
        instance.nickname = validated_data.get('nickname', instance.nickname)
        instance.country = validated_data.get('country', instance.country)
        instance.save()

        # 배우고자 하는 언어 업데이트
        if learning_language_ids is not None:
            instance.learning_languages.set(learning_language_ids)

        return instance


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """User profile update serializer (nickname and languages only)"""
    learning_language_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        min_length=1,
        help_text="List of learning language IDs"
    )

    class Meta:
        model = UserProfile
        fields = ['nickname', 'learning_language_ids']

    def validate_nickname(self, value):
        """Nickname validation"""
        if len(value) < 2:
            raise serializers.ValidationError("Nickname must be at least 2 characters long.")
        if len(value) > 50:
            raise serializers.ValidationError("Nickname cannot exceed 50 characters.")

        # Check for duplicate nickname (exclude own nickname)
        if UserProfile.objects.exclude(pk=self.instance.pk).filter(nickname=value).exists():
            raise serializers.ValidationError("This nickname is already in use.")

        return value

    def validate_learning_language_ids(self, value):
        """Learning language IDs validation"""
        if not value:
            raise serializers.ValidationError("At least one language must be selected.")

        # Check if language IDs exist
        existing_ids = set(Language.objects.filter(id__in=value).values_list('id', flat=True))
        invalid_ids = set(value) - existing_ids

        if invalid_ids:
            raise serializers.ValidationError(f"Invalid language IDs: {invalid_ids}")

        return value

    def update(self, instance, validated_data):
        """프로필 업데이트 (닉네임, 언어만)"""
        learning_language_ids = validated_data.pop('learning_language_ids', None)

        # 닉네임 업데이트
        instance.nickname = validated_data.get('nickname', instance.nickname)
        instance.save()

        # 배우고자 하는 언어 업데이트
        if learning_language_ids is not None:
            instance.learning_languages.set(learning_language_ids)

        return instance


class UserSerializer(serializers.ModelSerializer):
    """사용자 시리얼라이저"""
    profile = UserProfileSerializer(read_only=True)
    has_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'profile_image', 'google_id', 'date_joined', 'profile', 'has_profile']
        read_only_fields = ['id', 'google_id', 'date_joined']

    def get_has_profile(self, obj):
        """프로필 존재 여부"""
        return hasattr(obj, 'profile')
