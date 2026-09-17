# import User
from django.contrib.auth.models import User
from django.contrib.auth import login
# rest framework
from rest_framework.generics import GenericAPIView, UpdateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from rest_framework.permissions import IsAuthenticated
import requests,json
# import models

from api.models import Profile, Wallet, VirtualAccount, TransactionPin

# import serializers
from api.other_serializers.auth_serializers import UserSerializer, ProfileSerializer, ChangePasswordSerializer, LogInUserSerializer, virtaualAccountSerializer, TransactionPinSerializer,TransactionPinWithPasswordSerializer,ChangePasswordSerializer
from api.other_serializers.user_serializers import AnnouncementSerializer
from api.serializer import CustomPasswordResetSerializer
class CreateUserAccountView1(GenericAPIView):
    serializer_class = UserSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                data={
                    'status': 'success',
                    'data': serializer.data
                },
                status=201
            )
        return Response(
            data={
                'status': 'error',
                'data': serializer.errors
            },
            status=400
        )


# class CreateUserAccountView(GenericAPIView):
#     serializer_class = UserSerializer
    
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
        
#         if serializer.is_valid():
#             serializer.save()
#             ser_data = serializer.validated_data

#             username = ser_data['username']
#             password = ser_data['password']

#             user = authenticate(request, username=username, password=password)
#             user1 = request.user
#             if user is not None:
#                 login(request, user)

#                 refresh = RefreshToken.for_user(user)
#                 access_token = str(refresh.access_token)
#                 return Response(
#                     data={
#                         'status': 'success',
#                         'data': serializer.data,
#                         'access_token': access_token,
#                     },
#                     status=201
#                 )
#         return Response(
#             data={
#                 'status': 'error',
#                 'data': serializer.errors
#             },
#             status=400
#         )


class CreateUserAccountView(GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Authenticate and login the user
            username = user.username
            password = request.data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                return Response(
                    data={
                        'status': 'success',
                        'data': serializer.data,
                        'access_token': access_token,
                    },
                    status=201
                )
        return Response(
            data={
                'status': 'error',
                'data': serializer.errors
            },
            status=400
        )
    

class LoginUser(GenericAPIView):
    serializer_class = LogInUserSerializer

    def post(self, request, *args, **kwargs):
        serializer =  self.get_serializer(data= request.data)

        if serializer.is_valid():
            ser_data = serializer.validated_data

            username = ser_data['username']
            password = ser_data['password']

            user = authenticate(username=username,password=password)
            login(request,user)
            return Response({'success':'user login successfull','token':'xxx'})
        else:
            return Response({'error':'user not logged in!!!'})




# class LoginUser(GenericAPIView):
#     serializer_class = LogInUserSerializer

#     def post(self, request, *args, **kwargs):
#         serializer =  self.get_serializer(data=request.data)

#         if serializer.is_valid():
#             ser_data = serializer.validated_data

#             username = ser_data['username']
#             password = ser_data['password']

#             user = authenticate(username=username,password=password)
#             login(request,user)
#             try:
#                 response = requests.post('http://127.0.0.1:8000/api/token/',data={'username':username,'password':password})
#                 if response.status_code == 200 or response.status_code == 201:
#                    res_data = response.json()
#                    access_token = res_data.get('access')
#                 else:
#                     return Response({'message':response.status_code})
#             except:
#                 return Response({
#                     'status':'error',
#                     'message':ser_data.errors
#                 })

#             return Response({
#                                 'status':'success',
#                                 'token': access_token,
#                                 'userId': self.request.user.id,
#                                 'username':username,
#                             },status=200)
#         else:
#             return Response({
#                             'status':'error'
#                             },status=400)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login

# from .serializers import LogInUserSerializer  # Update with your actual serializer

class LoginUser(APIView):
    serializer_class = LogInUserSerializer

    

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            ser_data = serializer.validated_data

            username = ser_data['username']
            password = ser_data['password']

            user = authenticate(request, username=username, password=password)
            user1 = request.user
            if user is not None:
                login(request, user)

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
               # pro = Profile.objects.get(request.user)
               # serializer = ProfileSerializer(pro)
                # try:
                #     profile = Profile.objects.get(user=request.user)
                #     my_recs1 = profile.get_recommened_profiles()
                #     my_recs_data = {'username':my_recs1}
                # except Profile.DoesNotExist as e:
                #     print("Having issues with the recommended: ", e)
                #     my_recs_data = []

                # Now my_recs_data is a list of dictionaries, which




                try:
                    #proserializer = None
                    profile = Profile.objects.get(user=user)
                    virtaualAccounts = VirtualAccount.objects.filter(profile=profile)
                    VirtaualAccountsserializer = virtaualAccountSerializer(virtaualAccounts, many=True)
                    my_recs = profile.get_recommened_profiles()
                    profileSerializer = ProfileSerializer(profile)
                    pin ,created = TransactionPin.objects.get_or_create(profile=profile)
                    proserializer = TransactionPinSerializer(pin).data
                    return Response(
                        data={
                            'status': 'success',
                            'token': access_token,
                            'user_id': user.id,
                            'username': username,
                            "accounts" : VirtaualAccountsserializer.data,
                            "profile" : profileSerializer.data,
                            "pin" : proserializer
                            # 'my_recs':my_recs,
                        },
                        status=201,
                    )
                except:
                    return Response({
                        "error": " something went wrong"
                    })
                    
                
                return Response({
                    'status': 'success',
                    'token': access_token,
                    'user_id': user.id,
                    'username': username,
                    'profile_id': profile.id,
                    'phone_number': profile.phone,
                    'email':user.email,
                    'first_name':user.first_name,
                    'last_name':user.last_name,
                    'bank_name':profile.bank_name,
                    'account_number':profile.account_number,
                    'account_name':profile.account_name,
                    'location':profile.location,
                    'state':profile.state,
                    'recommended_by': profile.recommended_by.username,
                     'my_recs':profileSerializer.data,
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Invalid credentials',
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({
                'status': 'error',
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)












# import request
from django.contrib.auth import logout
from rest_framework_simplejwt.tokens import RefreshToken as RefreshTokenClass
from rest_framework_simplejwt.exceptions import TokenError

class LogOut(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Blacklist the refresh token if provided
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshTokenClass(refresh_token)
                token.blacklist()
            except TokenError:
                pass

        logout(request)
        return Response({'status': 'logged out successfully', 'message': 'You have been logged out'})

'''
view for profiles
# Creating profile
# updating profile
'''   
class UpdateTransactionPinWithPasswordAPIView(GenericAPIView):
    serializer_class = TransactionPinWithPasswordSerializer
    queryset = TransactionPin.objects.all()
    permission_classes = (IsAuthenticated, )

    def put(self, request, *args, **kwargs):

            
        serializer = TransactionPinWithPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer_inst = serializer.validated_data
            username = serializer_inst["username"]
            password = serializer_inst["password"]
            pin = serializer_inst["pin"]
            user = authenticate(request, username=username,password=password)
            if user is not None:
                profile = Profile.objects.get(user=user)
        
                transaction_pin = TransactionPin.objects.get(profile=profile)
        
                serializer = TransactionPinSerializer(transaction_pin, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        "status": "success",
                        "message": "Transaction Pin updated successfully.",
                        "data": serializer.data
                    }, status=200)
                else:
                    return Response({
                        "status": "error",
                        "message": serializer.errors
                    }, status=400)
            else:
                return Response({
                        "status": "error",
                        "message": "user not found"
                    }, status=400)
        return Response({
                        "status": "error",
                        "message": serializer.errors
                    }, status=400)


class ChangePasswordAPIView(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated, )      

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = request.user

            if not user.check_password(serializer.validated_data['old_password']):
                return Response({
                    "status":"error",
                    "message":"wrong passowrd"
                },status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            return Response({
                "status":"success",
                "mesasge":"Password Changed suucessfully."
            },status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,status.HTTP_400_BAD_REQUEST
        )



class CreateTransactionPinAPIView(GenericAPIView):
    serializer_class = TransactionPinSerializer
    queryset = TransactionPin.objects.all()
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            transactioPIn = TransactionPin.objects.get(profile=profile)
            serialiser = TransactionPinSerializer(transactioPIn)
            return Response(serialiser.data)
        except TransactionPin.DoesNotExist:
            return Response(
                status=404,
                data={
                    "status": 'error',
                    'message': 'Transaction Pin not found',
                    'error': 'No pin for this profile' 
                })
        except Profile.DoesNotExist:
            return Response(
                status=404,
                data={
                    "status": 'error',
                    'message': 'Profile not found',
                    'error': 'No profile for this user' 
                })
        
            
            


    def post(self, request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            serializer = TransactionPinSerializer(data=request.data)
            if serializer.is_valid():
                serializer_inst = serializer.validated_data
                pin = serializer_inst["pin"]
                TransactionPin.objects.update_or_create(
                    profile=profile,
                    defaults={'pin': pin}
                )
                return Response(
                    status=201,
                    data={
                        "status": "success",
                        "pin": pin,
                        "data": serializer.data
                    }
                )
            else:
                return Response({
                    "error": serializer.errors
                })
        except Profile.DoesNotExist:
            return Response({
                "error": "Profile does not exist"
            })
        
    def put(self, request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            try:
                transaction_pin = TransactionPin.objects.get(profile=profile)
            except TransactionPin.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "Transaction Pin not found for this profile."
                }, status=404)
            serializer = TransactionPinSerializer(transaction_pin, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "Transaction Pin updated successfully.",
                    "data": serializer.data
                }, status=200)
            else:
                return Response({
                    "status": "error",
                    "message": serializer.errors
                }, status=400)
        except Profile.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Profile does not exist"
            }, status=404)

    def delete(self, request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            try:
                transaction_pin = TransactionPin.objects.get(profile=profile)
            except TransactionPin.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "Transaction Pin not found for this profile."
                }, status=404)
            transaction_pin.delete()
            return Response({
                "status": "success",
                "message": "Transaction Pin deleted successfully."
            }, status=204)
        except Profile.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Profile does not exist"
            }, status=404)    


class CreateProfileAPIView1(GenericAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = ProfileSerializer

    def get(self, request, *args, **kwargs):
        
        try:
            pro = Profile.objects.get(user=request.user)
            serializer = self.get_serializer(pro)
            return Response(
                data={
                    'status': 'success',
                    "user": serializer.data,
                    "profileId": pro.id,
                    "profileImage":pro.image.url,
                }
                ,status=200
            )
        except:
            return Response(
                data ={
                    'status': 'error',
                    'data': 'THis user does not have a profile'
                }, status=400
            )
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer_inst = serializer.save(user=request.user, reseller=False)
            Wallet.objects.create(user=serializer_inst, balance=0.0)
            
            return Response(
                data={
                    'status': 'success profile created',
                    'data': serializer.data
                },
                status=201
            )
        return Response(
            data={
                'status': 'error',
                'data': serializer.errors
            },
            status=400
        )

        #=================================================
        ''' this is a modified version of the profile '''

class CreateProfileAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get(self, request, *args, **kwargs):
        try:
            pro = Profile.objects.get(user=request.user)
            serializer = self.get_serializer(pro)
            return Response(
                data={
                    'status': 'success',
                    "user": serializer.data,
                    "profileId": pro.id,
                    "profileImage": pro.profile_picture.url,
                },
                status=200
            )
        except Profile.DoesNotExist:
            return Response(
                data={
                    'status': 'error',
                    'data': 'This user does not have a profile'
                },
                status=400
            )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            #serializer_inst = self.get_serializer(user=self.request.user)
            serializer_inst = serializer.validated_data


            # Retrieve the phone number from the user's profile
            phone_number = serializer_inst['phone']
            

            # Call create_reserved_account function after creating a profile
            try:
                headers = {
                    #'api-key': 'PVKEY-K6AICOC1BP6W8TVSQD3WOJM2SIWCX57K',
                    'Authorization': 'Bearer Bill_Stack-SEC-KEY-5a72c6e35a87d7e00a3a0b7885199bec',
                    'Content-Type': 'application/json'  
                }

                data = {
                    "email": request.user.email,
                    "reference": f"sna{phone_number}",
                    "firstName": request.user.first_name,
                    "lastName": request.user.last_name,
                    "phone": phone_number,
                    "bank":"PALMPAY",
                    #"businessid":"064A4A647B0E4C3D8D83F68985FA31A9"
                }

                response = requests.post(
                    #'https://api.payvessel.com/api/external/request/customerReservedAccount/',
                    'https://api.billstack.co/v2/thirdparty/generateVirtualAccount/',
                    headers=headers,
                    json=data
                )
                print("status_code",response.status_code)
                print(response.text)
                if response.status_code == 200:
                    data = response.json()
                    #data = json.loads(response)
                    # reserved_account, created = ReservedAccount.objects.get_or_create(user=None)

                    #bank_name = data_json['banks'][0]['bankName']
                    #account_number = data_json['banks'][0]['accountNumber']
                    #account_name = data_json['banks'][0]['accountName']
                    #print(bank_name)
                    #print(account_number)
                    #print(account_name)
                    account_info = data["data"]["account"][0]
                    bank_name = account_info["bank_name"]
                    account_number = account_info["account_number"]
                    account_name = account_info["account_name"]
                    created_at = account_info["created_at"]
                    # Set bank details in the profile model
                    # serializer_inst.bank_name = bank_name  # Replace with actual bank name
                    # serializer_inst.account_number = account_number  # Replace with actual account number
                    # serializer_inst.account_name = account_name  # Replace with actual account name
                    # serializer_inst.save()
                    
                    






                #     recommended_by_username = serializer_inst.get('recommended_by')
                #     recommended_profile = None

                #     if recommended_by_username:
                #         try:
                #             recommended_profile = Profile.objects.get(code=recommended_by_username)
                #         except Profile.DoesNotExist:
                #             print(f"User with code {recommended_by_username} not found. Setting recommended_by to admin.")

                #     # Continue with profile creation
                #    # recommended_user = recommended_profile.user if recommended_profile else User.objects.get(username='admin')
                #     if recommended_profile:
                #         recommended_user = recommended_profile.user
                #     else:
                    # Resolve referral code if provided
                    referred_by_code = request.data.get('referred_by', '').strip()
                    recommended_user = None
                    if referred_by_code:
                        ref_profile = Profile.objects.filter(code__iexact=referred_by_code).first()
                        if ref_profile and ref_profile.user != request.user:
                            recommended_user = ref_profile.user

                    serializer_inst = serializer.save(
                        user=request.user,
                        reseller=False,
                        bank_name=bank_name,
                        account_number=account_number,
                        account_name=account_name,
                        recommended_by=recommended_user,
                    )
                    Wallet.objects.create(user=serializer_inst, balance=0.0)

                    # Credit ₦3 referral bonus to the referrer
                    if recommended_user:
                        try:
                            from decimal import Decimal
                            from django.db.models import F
                            referrer_profile = Profile.objects.get(user=recommended_user)
                            Wallet.objects.filter(user=referrer_profile).update(
                                commission_balance=F('commission_balance') + Decimal('3.00')
                            )
                        except Exception:
                            pass

                    # except ProfileDoesNotExit:
                    #     serializer_inst = serializer.save(user=request.user, reseller=False,bank_name=bank_name,account_number=account_number,account_name=account_name)
                    #     Wallet.objects.create(user=serializer_inst, balance=0.0)

            except Exception as e:
                print(f'Error creating reserved account: {e}')

            return Response(
                data={
                    'status': 'success profile created',
                    'data': serializer.data
                },
                status=201
            )

        return Response(
            data={
                'status': 'error',
                'data': serializer.errors
            },
            status=400
        )


        #================================================
''' the create profile method about is to be tested '''

# {
#     "user": 
#             5
#         ,
#         "location": 
#             "Nigeria"
#         ,
#         "phone": 
#             "07043194111"
#         ,
#         "state": 
#             "Akwa Ibom"
        
# }

class SumUp(GenericAPIView):
    CreateUserAccountView
    CreateProfileAPIView 


class UpdateProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        user = User.objects.get(username = self.request.user)
        obj = Profile.objects.get(user=user)
        return obj


'''
    Changing password views
'''
class ChangePasswordView(UpdateAPIView):
    # change Password
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated, ]
    model = User

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data['old_password']):
                return Response(
                    {
                        'old_password': 'Wrong Password',
                    },
                    status=400
                )
            self.object.set_password(serializer.data['new_password'])
            self.object.save()

            response = {
                'status': 'success',
                'code': 200,
                'message': 'Password Updated successfully',
            }
            return Response(response,status=200)
        return Response(serializer.errors, status=401)


from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from rest_framework.views import APIView

class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        
        try:
            user = User.objects.get(email=email)
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create password reset link
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
            
            # Send email
            send_mail(
                'Password Reset Request',
                f'Click the following link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return Response({
                'status': 'success',
                'message': 'Password reset link has been sent to your email'
            }, status=200)
            
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'No user found with this email address'
            }, status=404)
        
from django_rest_passwordreset.views import ResetPasswordRequestToken

from django.contrib.auth import get_user_model
User = get_user_model()

class CustomResetPassword(ResetPasswordRequestToken):
    serializer_class = CustomPasswordResetSerializer


# ─────────────────────────────────────────────────────────────────────────────
# Google / Firebase Auth
# ─────────────────────────────────────────────────────────────────────────────
import firebase_admin.auth as fb_auth
from django.conf import settings as django_settings
from rest_framework_simplejwt.tokens import RefreshToken


class GoogleAuthView(GenericAPIView):
    """
    Accepts a Firebase ID token from the Flutter app (obtained after Google Sign-In).
    - If the Firebase email maps to an existing user → logs in, returns 200.
    - If the email is new → creates user + profile + wallet, returns 201.
    """

    def post(self, request, *args, **kwargs):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'status': 'error', 'message': 'id_token is required'}, status=400)

        # Verify token with Firebase Auth (jeropay-baa6f project)
        try:
            decoded = fb_auth.verify_id_token(id_token, app=django_settings.FIREBASE_AUTH_APP)
        except Exception as e:
            return Response({'status': 'error', 'message': f'Invalid token: {str(e)}'}, status=401)

        email = decoded.get('email')
        name = decoded.get('name', '')
        if not email:
            return Response({'status': 'error', 'message': 'Email not found in token'}, status=400)

        # Look up existing user by email (email is not unique in Django by default)
        existing = User.objects.filter(email=email).order_by('id')
        user = existing.first()
        created = user is None

        if created:
            base_username = email.split('@')[0].replace('.', '_').replace('+', '_')
            username = base_username
            suffix = 1
            while User.objects.filter(username=username).exists():
                username = f'{base_username}{suffix}'
                suffix += 1
            parts = name.strip().split(' ', 1) if name else ['', '']
            user = User.objects.create(
                email=email,
                username=username,
                first_name=parts[0],
                last_name=parts[1] if len(parts) > 1 else '',
            )
            user.set_unusable_password()
            user.save()

        # Ensure profile + wallet exist for new Google users
        profile, profile_created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'location': '',
                'phone': '',
                'fullName': name,
                'reseller': False,
                'state': 'Lagos',
            }
        )
        Wallet.objects.get_or_create(user=profile)
        pin, _ = TransactionPin.objects.get_or_create(profile=profile)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        virtual_accounts = VirtualAccount.objects.filter(profile=profile)
        va_serializer = virtaualAccountSerializer(virtual_accounts, many=True)
        profile_serializer = ProfileSerializer(profile)
        pin_serializer = TransactionPinSerializer(pin)

        status_code = 201 if created else 200
        return Response(
            data={
                'status': 'success',
                'token': access_token,
                'refresh': str(refresh),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'accounts': va_serializer.data,
                'profile': profile_serializer.data,
                'pin': pin_serializer.data,
                'profile_complete': bool(profile.phone),
            },
            status=status_code,
        )


APPLE_BUNDLE_ID = 'com.jeropay.ng.jeropay'
_apple_jwk_client = None


def _get_apple_jwk_client():
    """Lazily build (and cache) the PyJWT client that fetches/caches Apple's
    public signing keys from https://appleid.apple.com/auth/keys."""
    global _apple_jwk_client
    if _apple_jwk_client is None:
        import jwt as _jwt
        _apple_jwk_client = _jwt.PyJWKClient('https://appleid.apple.com/auth/keys')
    return _apple_jwk_client


class AppleAuthView(GenericAPIView):
    """
    Accepts the raw Apple-issued identity_token straight from the Flutter
    app (via sign_in_with_apple), verified directly against Apple's public
    keys — no Firebase involved. Routing Apple sign-in through Firebase
    (verify a Firebase-wrapped credential) reliably failed with
    "invalid-credential: invalid OAuth response from apple.com" even with a
    correct entitlement, nonce and audience; going straight to Apple's own
    JWKS endpoint is the pattern already proven working in the NoveluX app.

    Apple only returns the user's name on their very first authorization
    ever — the client sends the name it captured at that first authorization
    as `full_name`, used as a fallback when creating the user.

    Apple's "Hide My Email" relay addresses (…@privaterelay.appleid.com)
    are valid, real, routable emails — they're treated the same as any
    other email here.
    """

    permission_classes = []  # public

    def post(self, request, *args, **kwargs):
        import jwt as _jwt

        identity_token = request.data.get('identity_token', '').strip()
        if not identity_token:
            return Response({'status': 'error', 'message': 'identity_token is required'}, status=400)

        # Verify directly against Apple's public keys (RS256, audience = our
        # app's bundle id, issuer = Apple) — no Firebase in this path.
        try:
            signing_key = _get_apple_jwk_client().get_signing_key_from_jwt(identity_token)
            decoded = _jwt.decode(
                identity_token,
                signing_key.key,
                algorithms=['RS256'],
                audience=APPLE_BUNDLE_ID,
                issuer='https://appleid.apple.com',
            )
        except _jwt.PyJWTError as e:
            return Response({'status': 'error', 'message': f'Invalid Apple token: {str(e)}'}, status=401)

        email = (decoded.get('email') or request.data.get('email', '')).lower()
        name = request.data.get('full_name', '')
        if not email:
            return Response({'status': 'error', 'message': 'Email not found in token'}, status=400)

        # Look up existing user by email (email is not unique in Django by default)
        existing = User.objects.filter(email=email).order_by('id')
        user = existing.first()
        created = user is None

        if created:
            base_username = email.split('@')[0].replace('.', '_').replace('+', '_')
            username = base_username
            suffix = 1
            while User.objects.filter(username=username).exists():
                username = f'{base_username}{suffix}'
                suffix += 1
            parts = name.strip().split(' ', 1) if name else ['', '']
            user = User.objects.create(
                email=email,
                username=username,
                first_name=parts[0],
                last_name=parts[1] if len(parts) > 1 else '',
            )
            user.set_unusable_password()
            user.save()

        # Ensure profile + wallet exist for new Apple users
        profile, profile_created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'location': '',
                'phone': '',
                'fullName': name,
                'reseller': False,
                'state': 'Lagos',
            }
        )
        Wallet.objects.get_or_create(user=profile)
        pin, _ = TransactionPin.objects.get_or_create(profile=profile)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        virtual_accounts = VirtualAccount.objects.filter(profile=profile)
        va_serializer = virtaualAccountSerializer(virtual_accounts, many=True)
        profile_serializer = ProfileSerializer(profile)
        pin_serializer = TransactionPinSerializer(pin)

        status_code = 201 if created else 200
        return Response(
            data={
                'status': 'success',
                'token': access_token,
                'refresh': str(refresh),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'accounts': va_serializer.data,
                'profile': profile_serializer.data,
                'pin': pin_serializer.data,
                'profile_complete': bool(profile.phone),
            },
            status=status_code,
        )


class MyReferralsView(GenericAPIView):
    """
    GET /my-referrals
    Returns everyone who signed up using the authenticated user's referral
    code (Profile.recommended_by), plus a count. The Flutter app's referral
    screen was already built to call this exact path — it just never
    existed server-side, so every request 404'd and the screen always
    showed an empty/zero state. Referral-bonus crediting (Wallet
    .commission_balance) already happens at signup in UserSerializer.create;
    this view only surfaces who was referred.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        referred_profiles = (
            Profile.objects.filter(recommended_by=request.user)
            .select_related('user')
            .order_by('-user__date_joined')
        )

        referrals = [
            {
                'full_name': p.fullName,
                'username': p.user.username,
                'email': p.user.email,
                'date_joined': p.user.date_joined,
            }
            for p in referred_profiles
        ]

        return Response({
            'status': 'success',
            'count': len(referrals),
            'referrals': referrals,
        })


class MoveBonusToWalletView(GenericAPIView):
    """
    POST /user/move-bonus-to-wallet/
    Moves the whole referral bonus (Wallet.commission_balance) into the main
    wallet balance and records it as a 'Bonus' transaction.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from decimal import Decimal
        from django.db import transaction as db_transaction
        from api.models import Transaction
        from api.utils.push import send_push

        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response({'status': 'error', 'message': 'This account does not have a profile.'}, status=400)

        with db_transaction.atomic():
            # lock the row so two taps can't move the same bonus twice
            wallet = Wallet.objects.select_for_update().filter(user=profile).first()
            if wallet is None:
                return Response({'status': 'error', 'message': 'This account does not have a wallet.'}, status=400)

            bonus = wallet.commission_balance or Decimal('0')
            if bonus <= 0:
                return Response({'status': 'error', 'message': 'You have no referral bonus to move.'}, status=400)

            old_balance = wallet.balance
            new_balance = old_balance + bonus
            Wallet.objects.filter(pk=wallet.pk).update(balance=new_balance, commission_balance=Decimal('0'))

            Transaction.objects.create(
                user=request.user,
                detail=f'Referral bonus of ₦{bonus} moved to wallet',
                network='N/A',
                response='Referral bonus moved to wallet',
                request_id='N/A',
                old_balance=old_balance,
                new_balance=new_balance,
                phone_number='N/A',
                status='Success',
                amount=bonus,
                type='Bonus',
            )

        send_push(request.user, 'Bonus Moved to Wallet', f'₦{bonus} referral bonus has been added to your wallet.')

        return Response({
            'status': 'success',
            'message': f'₦{bonus} has been moved to your wallet.',
            'amount': bonus,
            'balance': new_balance,
            'commission_balance': Decimal('0'),
        })


# ─────────────────────────────────────────────────────────────────────────────
# Virtual Account Retry (for users whose accounts were not generated on signup)
# ─────────────────────────────────────────────────────────────────────────────
BILLSTACK_KEY = 'Bearer Bill_Stack-SEC-KEY-5a72c6e35a87d7e00a3a0b7885199bec'
BILLSTACK_URL = 'https://api.billstack.co/v2/thirdparty/generateVirtualAccount/'
BANK_CODES = ['PALMPAY', '9PSB', 'SAFEHAVEN']


class RetryVirtualAccountsView(GenericAPIView):
    """
    Generates any missing virtual bank accounts for the authenticated user.
    Call this if a user signed up but their accounts were not created.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response({'status': 'error', 'message': 'Profile not found'}, status=404)

        existing_codes = set(
            VirtualAccount.objects.filter(profile=profile).values_list('bank_code', flat=True)
        )
        missing_codes = [c for c in BANK_CODES if c not in existing_codes]

        if not missing_codes:
            accounts = VirtualAccount.objects.filter(profile=profile)
            return Response({
                'status': 'success',
                'message': 'All accounts already exist',
                'accounts': virtaualAccountSerializer(accounts, many=True).data,
            })

        created = []
        failed = []
        headers = {
            'Authorization': BILLSTACK_KEY,
            'Content-Type': 'application/json',
        }

        for bank_code in missing_codes:
            data = {
                'email': request.user.email,
                'reference': f'sna{profile.phone}-{bank_code}',
                'firstName': request.user.first_name or request.user.username,
                'lastName': request.user.last_name or '',
                'phone': profile.phone,
                'bank': bank_code,
            }
            try:
                resp = requests.post(BILLSTACK_URL, headers=headers, json=data, timeout=15)
                if resp.status_code == 200:
                    account_info = resp.json()['data']['account'][0]
                    va = VirtualAccount.objects.create(
                        profile=profile,
                        bank_name=account_info.get('bank_name', ''),
                        account_number=account_info.get('account_number', ''),
                        account_name=account_info.get('account_name', ''),
                        bank_code=bank_code,
                    )
                    created.append(virtaualAccountSerializer(va).data)
                else:
                    failed.append({'bank_code': bank_code, 'error': resp.text})
            except Exception as e:
                failed.append({'bank_code': bank_code, 'error': str(e)})

        all_accounts = VirtualAccount.objects.filter(profile=profile)
        return Response({
            'status': 'success' if created else 'partial',
            'created': created,
            'failed': failed,
            'accounts': virtaualAccountSerializer(all_accounts, many=True).data,
        }, status=200)