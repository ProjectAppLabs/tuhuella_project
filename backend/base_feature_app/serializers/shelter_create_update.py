from django.core.files.base import ContentFile
from rest_framework import serializers

from base_feature_app.models import Shelter
from django_attachments.models import Library, Attachment


class ShelterCreateUpdateSerializer(serializers.ModelSerializer):
    website = serializers.URLField(required=False, allow_blank=True)
    cover_image_upload = serializers.ImageField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Shelter
        fields = [
            'id', 'name', 'legal_name', 'description_es', 'description_en',
            'city', 'address', 'phone', 'email', 'website', 'video',
            'cover_image_upload',
        ]

    def update(self, instance, validated_data):
        cover_upload = validated_data.pop('cover_image_upload', None)
        instance = super().update(instance, validated_data)
        if cover_upload is not None:
            self._set_cover_image(instance, cover_upload)
        return instance

    def create(self, validated_data):
        cover_upload = validated_data.pop('cover_image_upload', None)
        instance = super().create(validated_data)
        if cover_upload is not None:
            self._set_cover_image(instance, cover_upload)
        return instance

    @staticmethod
    def _set_cover_image(shelter, image_file):
        image_data = image_file.read()
        width = getattr(getattr(image_file, 'image', None), 'width', 0) or 0
        height = getattr(getattr(image_file, 'image', None), 'height', 0) or 0
        filename = image_file.name or 'cover.jpg'

        library = Library.objects.create(title=f'Cover: {shelter.name}')
        attachment = Attachment(
            library=library,
            rank=0,
            original_name=filename,
            filesize=len(image_data),
            image_width=width,
            image_height=height,
        )
        attachment.file.save(filename, ContentFile(image_data), save=False)
        attachment.save()
        library.primary_attachment = attachment
        library.save(update_fields=['primary_attachment'])
        shelter.cover_image = library
        shelter.save(update_fields=['cover_image'])
