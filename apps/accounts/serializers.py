from rest_framework import serializers
from accounts.models import Plan, PlanFeature
from django.contrib.auth import get_user_model

User = get_user_model()

class PlanFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFeature
        fields = ('id', 'feature',)

class PlanSerializer(serializers.ModelSerializer):
    features = PlanFeatureSerializer(many=True)
    class Meta:
        model = Plan
        fields = ('id', 'name', 'billing_period', 'price', 'duration', 'active', 'discount_note', 'order', 'features')
        read_only_fields = ('id',)

    def create(self, validated_data):
        features = validated_data.pop("features", [])
        plan = Plan.objects.create(**validated_data)
        for feature in features:
            PlanFeature.objects.create(plan=plan, **feature)
        return plan
    
    def update(self, instance, validated_data):
        features = validated_data.pop("features", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if features is not None:
            PlanFeature.objects.filter(plan=instance).delete()
            for feature in features:
                PlanFeature.objects.create(plan=instance, **feature)
        return instance

class UserSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'password': {'required': True, 'write_only': True}
        }

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class EmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)

class EmailPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

class EmptySerializer(serializers.Serializer):
    pass

class UpdateUserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'profile_picture')


