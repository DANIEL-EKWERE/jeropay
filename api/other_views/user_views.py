# time delta
from datetime import timedelta, datetime

# uuid
import uuid

# random
import random

# dj
from django.contrib.humanize.templatetags.humanize import naturaltime, naturalday
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.models import User
import requests,json
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

# rf
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# FCM
from fcm_django.models import FCMDevice

# import models
from api.models import Wallet, Profile, Transaction, ReservedAccount, Announcement, VirtualAccount

# serializers
from api.other_serializers.auth_serializers import UserSerializer, ProfileSerializer
from api.other_serializers.account_serializers import VirtualAccountsSerializer, WalletSerializer, TransactionSerializer, ConfirmPaymentSerializer, PhoneNumbersSerializer
from api.other_serializers.user_serializers import FCMDeviceIDSerializer, ReserveAcctountSerializer, AnnouncementSerializer

# import packages
from api.date_package.converterv2 import TodaysDate, OtherDateFilters


class UserDashboardView(GenericAPIView):
    '''index of the API's dashboard'''
    permission_classes = [IsAuthenticated,]
    
    def get(self, request, *args, **kwargs):
        # user info
        user = request.user
        user_serializer = UserSerializer(user)

        # Profile info
        try:
            profile = Profile.objects.get(user=request.user)
        except:
            return Response(
                data={
                    'status': 'error',
                    'message': 'No Profile found'
                },
                status=403,
            )
        
        try:
            virtual_accounts = VirtualAccount.objects.all()
        except:
            return Response(
                data={
                    'status': 'error',
                    'message': 'No virtual accounts found'
                },
                status=403,
            )
                
        
        # wallet infomation
        wallet = Wallet.objects.get(user=profile)
        wallet_serializer = WalletSerializer(wallet)
        wallet_balance = wallet.balance

        # virtaul accounts
        accounts_serializer = VirtualAccountsSerializer(virtual_accounts, many=True)

        
        # orders/transactions
        transactions = Transaction.objects.select_related().filter(user=user).order_by('-date_and_time')[:10]
        
        for trans in transactions:
            trans.date_and_time = naturalday(trans.date_and_time)
        trans_serializer = TransactionSerializer(transactions, many=True)
            
        return Response(
            data = {
                'status': 'success',
                'data': {
                    'name': profile.fullName,
                    'location': profile.location,
                    'phone' : profile.phone,
                    'profile': user_serializer.data,
                    'wallet': wallet_serializer.data,
                    'transactions': trans_serializer.data,
                    'wallet_balance':wallet_balance,
                    'virtual_accounts': accounts_serializer.data
                }
            },
            status=200
        )


class RecentTransactions(GenericAPIView):
    permission_classes = [IsAuthenticated,]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']

    def get(self, request, *args, **kwargs):
        user = self.request.user
        # orders/transactions
        transactions = Transaction.objects.select_related().filter(user=user).order_by('-date_and_time')[:10]
        
        for trans in transactions:
            trans.date_and_time = naturalday(trans.date_and_time)
        trans_serializer = TransactionSerializer(transactions, many=True)

        return Response(
            data = {
                'status': 'success',
                'transactions': trans_serializer.data,
            },
            status=200
        )


class PaymentProofView(GenericAPIView):
    serializer_class = ConfirmPaymentSerializer
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(profile=request.user)
            return Response(
                {
                    'status': 'success',
                    'data': {
                        'message': 'file upload successful',
                    }
                }
            )
        return Response(
            {
                'status':'error',
                'data': serializer.errors
            }
        )

class SingleTransaction(GenericAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated,]

    def get(self, request, trans_uuid, *args, **kwargs):
        try:
            transaction = Transaction.objects.get(id=trans_uuid)
            # transaction.date_and_time = datetime.strptime(transaction.date_and_time, "%Y-%m-%d")
            trans_date_time = transaction.date_and_time
            transaction.date_and_time = trans_date_time.strftime("%m/%d/%Y, %H:%M:%S")

            trans_serializer = self.get_serializer(transaction)
            return Response(
                {
                    'status': 'success',
                    'data': trans_serializer.data
                },
                status=200
            )
        except:
            return Response(
                {
                    'status': 'error',
                    'data' : f'{trans_uuid} is not valid, check the number and try again.',
                },
                status=400
            )


# class ReserveAccount(GenericAPIView):
#     permission_classes = [IsAuthenticated,]
    
#     def get(self, request, *args, **kwargs):

#         try:

#             def create_id():
#                 num = random.randint(1, 10)
#                 num_2 = random.randint(1, 10)
#                 num_3 = random.randint(1, 10)
#                 return str(num_2)+str(num_3)+str(uuid.uuid4())[:4]

#             body = {
#                 "accountReference": create_id(),
#                 "accountName": request.user.username,
#                 "currencyCode": "NGN",
#                 "contractCode": f"{config.monnify_contract_code}",
#                 "customerEmail": request.user.email,
#                 "incomeSplitConfig": [],
#                 "restrictPaymentSource": False,
#                 "allowedPaymentSources": {},
#                 "customerName": request.user.username,
#                 "getAllAvailableBanks": True,
#             }

#             if not request.user.accounts:

#                 data = json.dumps(body)
#                 ad = requests.post("https://api.monnify.com/api/v1/auth/login", auth=HTTPBasicAuth(f'{config.monnify_API_KEY}', f'{config.monnify_SECRET_KEY}'))
#                 mydata = json.loads(ad.text)
#                 headers = {'Content-Type': 'application/json', 'User-Agent': 'Custom', "Authorization": "Bearer {}" .format(mydata['responseBody']["accessToken"])}
#                 ab = requests.post("https://api.monnify.com/api/v2/bank-transfer/reserved-accounts",headers=headers, data=data)

#                 mydata = json.loads(ab.text)

#                 user = request.user
#                 user.reservedaccountNumber = mydata["responseBody"]["accounts"][0]["accountNumber"]
#                 user.reservedbankName = mydata["responseBody"]["accounts"][0]["bankName"]
#                 user.reservedaccountReference = mydata["responseBody"]["accountReference"]
#                 user.accounts = json.dumps({"accounts":mydata["responseBody"]["accounts"]})
#                 user.save()

#             else:
#                 pass

#         except:
#             pass


def post(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)

    if serializer.is_valid():
        serializer_inst = serializer.save(user=request.user, reseller=False)
        Wallet.objects.create(user=serializer_inst, balance=0.0)

        # Set bank details in the profile model
        serializer_inst.bank_name = "Bank XYZ"  # Replace with actual bank name
        serializer_inst.account_number = "1234567890"  # Replace with actual account number
        serializer_inst.account_name = "John Doe"  # Replace with actual account name
        serializer_inst.save()

        # Call create_reserved_account function after creating a profile
        create_reserved_account(
            email=request.user.email,
            name=request.user.username,
            phone_number=serializer_inst.phone,
            bank_code=["120001"],  # Replace with the actual bank code
            business_id="064A4A647B0E4C3D8D83F68985FA31A9"  # Replace with the actual business ID
        )

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



def create_reserved_account(email, name, phone_number, bank_code, business_id):
    try:
        headers = {
            'api-key': 'PVKEY-K6AICOC1BP6W8TVSQD3WOJM2SIWCX57K',
            'api-secret': 'Bearer PVSECRET-5CQIJKA16EBCVL6WY7DH8OQ57DZQDZ2YXGA76NK64QRBGT5OCRWQ8KBZTYYA603S',
            'Content-Type': 'application/json'  
        }

        data = {
            "email": email,
            "name": name,
            "phoneNumber": phone_number,
            "bankcode": bank_code,
            "businessid": business_id
        }

        response = requests.post(
            'https://api.payvessel.com/api/external/request/customerReservedAccount/',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            data_json = response.json()
            reserved_account, created = ReservedAccount.objects.get_or_create(user=None)

            if not reserved_account.accounts:
                bank_name = data_json['banks'][0]['bankName']
                account_number = data_json['banks'][0]['accountNumber']
                account_name = data_json['banks'][0]['accountName']
                
                reserved_account.reservedaccountNumber = account_number
                reserved_account.reservedbankName = bank_name
                reserved_account.reservedaccountName = account_name
                reserved_account.accounts = True
                reserved_account.save()
        else:
            print(f'Error creating reserved account: {response.status_code}')

    except Exception as e:
        print(f'Error creating reserved account: {e}')

# You can then use this function in your CreateProfileAPIView as mentioned in your previous message.
   # },status=200)

class ReservedAccountCreation(GenericAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = ReserveAcctountSerializer
    def get(self, request, *args, **kwargs):
        try:
            user = self.request.user
            reservered = ReservedAccount.objects.get(user=request.user)
            pro = Profile.objects.get(user=user)
            phone_number = pro.phone
        except:
            def create_id():
                num = random.randint(1, 10)
                num_2 = random.randint(1, 10)
                num_3 = random.randint(7, 9)
                return str(0)+str(num_3)+str(uuid.uuid4())[:9]
            phone_number = create_id()
            
        try:
            headers= {
              'api-key': 'PVKEY-K6AICOC1BP6W8TVSQD3WOJM2SIWCX57K',
              'api-secret': 'Bearer PVSECRET-5CQIJKA16EBCVL6WY7DH8OQ57DZQDZ2YXGA76NK64QRBGT5OCRWQ8KBZTYYA603S',
              'Content-Type': 'application/json'  
            }
            User

            data = {
                "email":request.user.email,
                "name": request.user.username,
                "phoneNumber": "07013116710",
                "bankcode":["120001"],
                "businessid":"064A4A647B0E4C3D8D83F68985FA31A9"
            }
            
            response = requests.post(
                'https://api.payvessel.com/api/external/request/customerReservedAccount/',
                headers=headers,
                json=data
                )

            if response.status_code == 200:
                dat = response.json()
                if not ReservedAccount.accounts:
                    bank_name = dat['banks'][0]['bankName'],
                    account_number = dat['banks'][0]['accountNumber'],
                    account_name = dat['banks'][0]['accountName'],
                    reservered.reservedaccountNumber = account_number,
                    reservered.reservedbankName = bank_name,
                    reservered.reservedaccountName = account_name
                    reservered.accounts = True,
                    reservered.save()
            else:
                return Response({'error':response.status_code})

        except:
            return Response({'message':'unable to generate vitual acct '})
        else:
            return Response({'status':response.status_code, 'response body':response.json()})
        return Response({
             "bankName": bank_name,
             "accountNumber": account_number,
             "accountName": account_name,
        },status=200)




        
class GetAllReservedAccount(ListAPIView):
    serializer_class = ReserveAcctountSerializer
    # queryset = ReservedAccount.objects.get(request.user)

    def get(self, request, *args, **kwargs):
        acct = ReservedAccount.objects.filter(user=request.user)

        serialized_acct = ReserveAcctountSerializer(acct,many= True,)
        return Response({'accts':serialized_acct.data},status=200)
    # def get_queryset(self):
    #     return ReservedAccount.objects.filter(user=self.kwargs['user'])



class AnnouncementApiView(GenericAPIView):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated,]

    def get(self, request, *args, **kwargs):
        announcement = Announcement.objects.get(id=1)
        serialized_announcement = AnnouncementSerializer(announcement)
        return Response({'announcement':serialized_announcement.data},status=200)


'''
collect Transaction Data for periods that go into the app
# Today
# yesterday
# current / past  Week
# current / past  Month
# current / past  Year
'''

class TransFilterMixin(OtherDateFilters):
    def single_date_filter(self, request, singleDateFn):
        transactions = Transaction.objects.filter(user=request.user, date_and_time__date=singleDateFn).order_by('-date_and_time')
        for trans in transactions:
            trans.date_and_time = naturalday(trans.date_and_time)
        return transactions

    def filter_date_by_range(self, request, start_date, end_date):
        transactions = Transaction.objects.filter(user=request.user, date_and_time__range=[start_date, end_date]).order_by('-date_and_time')
        for trans in transactions:
            trans.date_and_time = naturalday(trans.date_and_time)
        return transactions

    def transaction_sum(self, type, transaction_instance):
        return transaction_instance.filter(type=type).aggregate(Sum('amount'))['amount__sum'] or 0

    def total_trans_amount(self, transaction_instance):
        airtime = self.transaction_sum('Airtime', transaction_instance)
        data = self.transaction_sum('Data', transaction_instance)
        electricity = self.transaction_sum('Electricity', transaction_instance)
        cable = self.transaction_sum('Cable', transaction_instance)

        return airtime + data + electricity + cable

class TransactionsToday(TransFilterMixin,GenericAPIView):
    '''
    view transaction records for today
    '''
    permission_classes = [IsAuthenticated,]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']

    def get(self, request, *args, **kwargs):

        trans = self.single_date_filter(request, self.todays_date_time())
        trans_serializer = TransactionSerializer(trans, many=True).data
        
        total_sum = self.total_trans_amount(trans)
        
        return Response(
            data={
                'status': 'success',
                'total_amount': total_sum,
                'data': trans_serializer,
            },
            status=200
        )

class TransactionsYesterday(TransFilterMixin, GenericAPIView):
    '''
    view transaction records for yesterday
    '''
    permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']

    def get(self, request, *args, **kwargs):

        trans = self.single_date_filter(request, self.yesterday())
        trans_serializer = TransactionSerializer(trans, many=True).data
        
        airtime_amount_filter = trans.filter(type='Airtime').aggregate(Sum('amount'))['amount__sum'] or 0
        data_amount_filter = trans.filter(type='Data').aggregate(Sum('amount'))['amount__sum'] or 0

        total_sum = airtime_amount_filter + data_amount_filter

        return Response(
            data={
                'status': 'success',
                'total_amount': total_sum,
                'data': trans_serializer,
            },
            status=200
        )


class GenericTransactionsRangeMixin(TransFilterMixin, GenericAPIView):
    '''
    A generic Mixin to aid with filtering records based different periods
    of the date
    i.e This week, Past week etc.
    '''
    start_date = None
    end_date = None
    
    def get(self, request, *args, **kwargs):
        trans = self.filter_date()
        trans_serializer = TransactionSerializer(trans, many=True).data

        total_sum = self.total_trans_amount(trans)

        return Response(
            data={
                'status': 'success',
                'total_amount': total_sum,
                'data': trans_serializer,
            },
            status=200
        )
    
    def filter_date(self):
        
        return self.filter_date_by_range(self.request, self.start_date, self.end_date)

class TransactionsLastWeek(GenericTransactionsRangeMixin):
    '''
    Transactions for Previous week
    '''
    permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']

    start_date = OtherDateFilters().past_monday()
    end_date = OtherDateFilters().monday()

class TransactionsThisWeek(GenericTransactionsRangeMixin):
    '''
    Transactions for current week
    '''
    permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']

    start_date = OtherDateFilters().monday()
    end_date = timezone.now() + timedelta(days=1)

class TransactionsLastMonth(GenericTransactionsRangeMixin):
    '''
    Transactions for previous month
    '''
    permission_classes = [IsAuthenticated,]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']

    start_date = OtherDateFilters().currenMonthStart() - timedelta(days=30)
    end_date = OtherDateFilters().currenMonthEnd() - timedelta(days=30)

class TransactionsThisMonth(GenericTransactionsRangeMixin):
    '''
    Transactions for current month
    '''
    permission_classes = [IsAuthenticated,]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']

    start_date = OtherDateFilters().currenMonthStart()
    end_date = OtherDateFilters().currenMonthEnd()

class TransactionByRange(GenericTransactionsRangeMixin):
    permission_classes = [IsAuthenticated,]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']

    def get(self, request, start_date, end_date, *args, **kwargs):
        end_date_str_to_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        end_date_date_to_str = datetime.strftime(end_date_str_to_date, '%Y-%m-%d')
        trans = self.filter_date_by_range(request, start_date=start_date, end_date=end_date_date_to_str).order_by('-date_and_time')


       
        for transaction in trans: # duplicated code to fix the issue
            transaction.date_and_time = naturalday(transaction.date_and_time)

        trans_serializer = TransactionSerializer(trans, many=True).data

       
        total_sum = self.total_trans_amount(trans)
        return Response(
            data={
                'status': 'success',
                'total_amount': total_sum,
                'data': trans_serializer,
            },
            status=200
        )



class ToBeFilteredTransactions(ListAPIView):
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(user=user).order_by('-date_and_time')

class WalleStatistic(GenericTransactionsRangeMixin):
    permission_classes = [IsAuthenticated,]
    serializer_class = ProfileSerializer

    def get(self, request, *args, **kwargs):
        # to get the total transaction
        trans = Transaction.objects.filter(user=request.user).order_by('-date_and_time')
        total_sum = self.total_trans_amount(trans)


        user = request.user
        user_serializer = UserSerializer(user)

        # Profile info
        try:
            profile = Profile.objects.get(user=request.user)
        except:
            return Response(
                data={
                    'status': 'error',
                    'message': 'No Profile found'
                },
                status=403,
            )


        #to get the total deposit
       # user = Profile.objects.get(user=request.user)
        totaldep = Wallet.objects.get(user=profile)
        serializer = WalletSerializer(totaldep).data
        total_deposit = totaldep.total_deposit

        #to get the total purchase
        #user = Profile.objects.get(user=request.user)
        totalpur = Wallet.objects.get(user=profile)
        serializer = WalletSerializer(totaldep).data
        total_deposit = totalpur.total_purchase

        return Response({
            'total_transactions': total_sum,
            'total_deposit':totaldep.total_deposit,
            'total_purchase': totalpur.total_purchase, 
        },status=200)





class AllTransactionRecords(GenericTransactionsRangeMixin):
    permission_classes = [IsAuthenticated,]

    def get(self, request, *args, **kwargs):
        
        trans = Transaction.objects.filter(user=request.user).order_by('-date_and_time')

        for transaction in trans: # duplicated code to fix the issue
            transaction.date_and_time = naturalday(transaction.date_and_time)

        trans_serializer = TransactionSerializer(trans, many=True).data

        total_sum = self.total_trans_amount(trans)

        return Response(
            data={
                'status': 'success',
                'total_amount': total_sum,
                'data': trans_serializer,
            },
            status=200
        )


''' 
### Filter out All the phone Numbers a User has transacted with ###
'''
class FilterPhoneNumbersFromTransactions(GenericAPIView):
    permission_classes = [IsAuthenticated, ]
    queryset = Transaction.objects.all()
    serializer_class = PhoneNumbersSerializer
    
    def get(self, request, *args, **kwargs):
        phone_number_list =  set()
        phone_numbers_queryset = Transaction.objects.filter(user=request.user).values('phone_number')
        
        for i, number in enumerate(phone_numbers_queryset):

            if number['phone_number'] == "":
                pass
            else:
                if number['phone_number'] in phone_number_list:
                    pass
                else:
                    phone_number_list.add(number['phone_number'])
                    
        return Response(
                {
                'numbers': phone_number_list
                }
            )
    

class FCMDeviceInfoConnectorAPI(GenericAPIView):
    serializer_class = FCMDeviceIDSerializer
    permission_classes = [IsAuthenticated, ]
    queryset = FCMDevice.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            sers_data = serializer.validated_data
            device_id = sers_data['device_id']
            
            user = User.objects.get(username=request.user)

            # query and check if a user exists in a device
            fcm = FCMDevice.objects.filter(user=user)

            if fcm.exists():
                fcm.update(
                    device_id=device_id,
                    registration_id=device_id,
                    active=True #update to active, if it was set to false
                )
                return Response(
                    data={
                        'updated',
                    }
                )
            
            FCMDevice.objects.create(
                name=f'{user.first_name} Device',
                user=user,
                device_id=device_id,
                registration_id=device_id,
                type= sers_data['device_type'],
            )
            return Response(
                data={},
                status=200
            )
        return Response(
            data=serializer.errors,
            status=400
        )