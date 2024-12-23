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

from api.models import Profile, Wallet

# import serializers
from api.other_serializers.auth_serializers import UserSerializer, ProfileSerializer, ChangePasswordSerializer, LogInUserSerializer
from api.other_serializers.user_serializers import AnnouncementSerializer
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


class CreateUserAccountView(GenericAPIView):
    serializer_class = UserSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            ser_data = serializer.validated_data

            username = ser_data['username']
            password = ser_data['password']

            user = authenticate(request, username=username, password=password)
            user1 = request.user
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
                    profile = Profile.objects.get(user=request.user)
                    my_recs = profile.get_recommened_profiles()
                    profileSerializer = ProfileSerializer(my_recs,many=True)
                except:
                    return Response(
                        data={
                            'status': 'success',
                            'token': access_token,
                            'user_id': user.id,
                            'username': username,
                            # 'my_recs':my_recs,
                        },
                        status=201,
                    )
                
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

class LogOut(GenericAPIView):
    def post(self, request, *args, **kwargs):
        logout(request)

        return Response({'status':'logged out successful'})

'''
view for profiles
# Creating profile
# updating profile
'''      
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
                    'Authorization': 'Bearer Bill_Stack-SEC-KEY-299b074531bcfed779edb3f7fdaac87b',
                    'Content-Type': 'application/json'  
                }

                data = {
                    "email": request.user.email,
                    "reference": f"sna{phone_numbet}"
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
                    #data_json = response.json()
                    data = json.loads(response)
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
                        # If recommended_profile is not found, set it to a default user (e.g., admin)
                    recommended_user, created = User.objects.get_or_create(username='admin')

                    
                    
                    
                    # serializer_inst = serializer.save(
                    #     user=request.user,
                    #     reseller=False,
                    #     bank_name=bank_name,
                    #     account_number=account_number,
                    #     account_name=account_name,
                    #     recommended_by=recommended_user.username
                    # )




                    # referral = serializer_inst['recommended_by']
                    # print(referral)
                    # recommended_profile = Profile.objects.get(code=referral)
                    # print('recommened',recommended_profile)
                    # registered_profile = Profile.objects.get(user=request.user)
                    # registered_profile.recommended_by = recommended_profile.user 
                    #registered_profile.save()
                    serializer_inst = serializer.save(user=request.user, reseller=False,bank_name=bank_name,account_number=account_number,account_name=account_name,recommended_by=recommended_user)
                    Wallet.objects.create(user=serializer_inst, balance=0.0)
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
