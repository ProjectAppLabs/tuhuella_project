from rest_framework import serializers

from base_feature_app.models import UpdatePost
from base_feature_app.utils.shelter_access import user_can_manage_shelter


class UpdatePostCreateUpdateSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)

    def validate_shelter(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if not user_can_manage_shelter(request.user, value):
                raise serializers.ValidationError('You cannot manage this shelter.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        shelter = attrs.get('shelter', getattr(self.instance, 'shelter', None))
        errors = {}
        for field in ('campaign', 'animal'):
            related_object = attrs.get(field, getattr(self.instance, field, None))
            if related_object is not None and related_object.shelter_id != shelter.pk:
                errors[field] = 'This object does not belong to the selected shelter.'
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    class Meta:
        model = UpdatePost
        fields = [
            'id', 'shelter', 'campaign', 'animal',
            'title_es', 'title_en', 'content_es', 'content_en',
            'image', 'image_url',
        ]
        extra_kwargs = {
            'image': {'required': False},
        }

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
