from rest_framework import serializers
from base_feature_app.models import Shelter
from base_feature_app.serializers.utils import (
    can_view_shelter_owner_email,
    get_lang,
    library_primary_url,
)


class ShelterListSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    logo_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Shelter
        fields = [
            'id', 'name', 'description', 'city', 'verification_status',
            'is_verified', 'logo_url', 'cover_image_url',
            'owner_email', 'created_at',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not can_view_shelter_owner_email(self, instance):
            data.pop('owner_email', None)
        return data

    def get_description(self, obj):
        return getattr(obj, f'description_{get_lang(self)}')

    # logo and cover_image are SingleImageField — FKs to a django_attachments
    # Library, not file fields. Reading `.url` off the Library raised
    # AttributeError and 500'd the whole list endpoint for any shelter that had
    # an image. Same helper the detail serializer uses.
    def get_logo_url(self, obj):
        return library_primary_url(obj.logo)

    def get_cover_image_url(self, obj):
        return library_primary_url(obj.cover_image)
