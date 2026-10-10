from rest_framework import serializers
from base_feature_app.models import UpdatePost
from base_feature_app.serializers.utils import get_lang, library_primary_url


class UpdatePostDetailSerializer(serializers.ModelSerializer):
    shelter_name = serializers.CharField(source='shelter.name', read_only=True)
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = UpdatePost
        fields = [
            'id', 'title', 'content', 'shelter', 'shelter_name',
            'campaign', 'animal', 'image_url', 'created_at', 'updated_at',
        ]

    def get_title(self, obj):
        return getattr(obj, f'title_{get_lang(self)}')

    def get_content(self, obj):
        return getattr(obj, f'content_{get_lang(self)}')

    def get_image_url(self, obj):
        return library_primary_url(obj.image, default=None)
