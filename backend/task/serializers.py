from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task
from django.utils import timezone

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class TaskSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'due_date', 'created_at', 'updated_at', 'owner']

    def validate(self, data):
        if data.get('status') == 'done' and data.get('due_date') and data['due_date'] > timezone.now():
            raise serializers.ValidationError("Cannot mark task as done before its due date.")
        return data
