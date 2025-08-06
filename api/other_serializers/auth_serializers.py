'''
Serializers for Creating the User account and profile
'''
from django.contrib.auth.models import User
from api.models import Profile, Wallet, VirtualAccount, TransactionPin
# serializers
from rest_framework import serializers


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['username', 'email', 'first_name', 'last_name', 'password']

#     def validate_username(self, value):
#         if value == '':
#             raise serializers.ValidationError('Username Field cannot be Empty')
#         return value
    
#     def create(self, validated_data):
#         user = User.objects.create_user(
#             **validated_data
#         )

#         return user


class UserSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True)
    address_area = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['fullname', 'username', 'email', 'phone', 'address_area', 'referral_code', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if value == '':
            raise serializers.ValidationError('Username Field cannot be Empty')
        return value

    def create(self, validated_data):
        fullname = validated_data.pop('fullname')
        phone = validated_data.pop('phone')
        address_area = validated_data.pop('address_area')
        referral_code = validated_data.pop('referral_code', None)
        password = validated_data.pop('password')
        # Split fullname into first_name and last_name
        names = fullname.strip().split(' ', 1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else ''
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        user.save()
        # Create profile
        profile = Profile.objects.create(
            user=user,
            phone=phone,
            fullName=fullname,
            location=address_area,
            reseller=False,
            recommended_by=referral_code if referral_code else None
        )
        Wallet.objects.create(user=profile, balance=0.0)
        return user

class LogInUserSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


# class ProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Profile
#         fields = ['location', 'phone', 'state', 'profile_picture','recommended_by']
        

class virtaualAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualAccount
        fields = "__all__" 

class TransactionPinSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionPin
        fields = ['pin']         


class ProfileSerializer(serializers.ModelSerializer):
    # Use a CharField for recommended_by to accept a string
    recommended_by = serializers.CharField(required=False)

    class Meta:
        model = Profile
        fields = ['location', 'phone', 'state','fullName', 'profile_picture', 'recommended_by','code']

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
