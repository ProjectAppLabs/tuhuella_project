from rest_framework import serializers
from base_feature_app.models import ShelterInvite
from base_feature_app.utils.shelter_access import user_can_manage_shelter


class ShelterInviteCreateUpdateSerializer(serializers.ModelSerializer):
    def validate_shelter(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if not user_can_manage_shelter(request.user, value):
                raise serializers.ValidationError('You cannot manage this shelter.')
        return value

    class Meta:
        model = ShelterInvite
        fields = ['id', 'shelter', 'adopter_intent', 'message']
