from rest_framework import serializers
from subactivities.models import SubActivity


class SubActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubActivity
        fields = '__all__'


class ValidateSubactivityTentativeDateSerializer(serializers.Serializer):
    subactivity = serializers.IntegerField(required=True)
    tentative_date = serializers.DateTimeField(required=True)