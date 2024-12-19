'''
Serializers for Creating the User account and profile
'''
from django.contrib.auth.models import User
from api.models import Profile
# serializers
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def validate_username(self, value):
        if value == '':
            raise serializers.ValidationError('Username Field cannot be Empty')
        return value
    
    def create(self, validated_data):
        user = User.objects.create_user(
            **validated_data
        )

        return user


class LogInUserSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


# class ProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Profile
#         fields = ['location', 'phone', 'state', 'profile_picture','recommended_by']
        

class ProfileSerializer(serializers.ModelSerializer):
    # Use a CharField for recommended_by to accept a string
    recommended_by = serializers.CharField(required=False)

    class Meta:
        model = Profile
        fields = ['location', 'phone', 'state', 'profile_picture', 'recommended_by','code']

    # def validate_recommended_by(self, value):
    #     # Validate and convert the recommended_by string to a User instance
    #     try:
    #         user = User.objects.get(username=value)
    #         if user:
    #             return user
    #         else:
    #             user = User.objects.get(username='admin')
    #             return user
    #     except User.DoesNotExist:
    #         return  User.objects.get_or_create(username='admin')
    #def validate_recommended_by(self, value):
        # Validate and convert the recommended_by string to a User instance
        #try:
            #user = User.objects.get(username=value)
            #if user:
                #return user
            #else:
                #user = User.objects.get(username='admin')
                #return user
        #except User.DoesNotExist:
            #return  User.objects.get_or_create(username='admin')
            # raise serializers.ValidationError("User with this username does not exist.")



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
