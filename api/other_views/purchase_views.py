import logging
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from django.db.models import F
from django.db.models.functions import Coalesce

# rest framework Modules
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

# requests
import requests, json, urllib3

# models
from api.models import Transaction, Data, Profile, CableSubscription, Wallet, ExamPinPrice
from api.network_control import available_plans, network_block_message
from api.utils.push import send_push as _send_push

# serializers
from api.other_serializers.purchase_serializers import (
    TransactionSerializer,
    AirtimeSerializer,
    DataSerializer,
    DeductAirtimeSerializer,
    DeductDataSerializer,
    PurchaseExamEpinSerializer,

    # electricity bills
    ValidateMeterNumberSerializer,
    ElectricBillPaymentSerializer,

    # cable tv
    ValidateCableNumber,
    CablePaymentSerializer,

    # price
    DataPriceSerializer,
    )

# wallet
from api.other_views.mixins.wallet_check_mixins import WalletCheckMixin

# constants
from api.constants import (
    EXAM_RESULT_CHECKER,
    NETWORK_ID, 
    ELECTRIC_DISCO_ID,
    CABLE_PROVIDER_ID,
    KVDATA_BASE_URL,
    KVDATA_PROVIDER_TOKEN,
    API_BASE_URL,
    API_PROVIDER_TOKEN,

    RequestWrapper
    )

logger = logging.getLogger(__name__)

"""
Section for purchasing Services i.e airtime, data, elect, etc
"""

'''
me testing here below
'''

class DeductTest(WalletCheckMixin, GenericAPIView):
    serializer_class = DeductAirtimeSerializer
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        return Response({'success':'deduct api received'},status=200)

    def post(self, request, *args, **kwargs):
        amount = 200
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            vd = serializer.validated_data
            phone_number = vd['phone_number']
            network = vd['network'].upper()
            amount = vd['amount']
            wallet = self.check_wallet_balance(amount=amount)

            
            message = f'You have purchased {amount} airtime from {network}'
            
            balances = self.deduct_amount_from_balance(amount=amount)

            trans = Transaction.objects.create(
                user=request.user,
                detail= message,
                old_balance=balances[0],
                new_balance= balances[1],
                phone_number=phone_number,
                status='Success',
                amount=amount,
                type= 'Airtime',
            )

            trans_serializer = TransactionSerializer(trans).data

            return Response(
                data={
                    'status': 'success',
                    'data': trans_serializer
                },
                status=200
            )
        return Response(
            data={
                'status': 'error',
                'message': response.json()
            },
        status=400
        )

            # return Response({"success":"purchase successfull, enoy!!!"})
        return Response({"try again later":"something went wrong pls try again later"})


class DeductData(WalletCheckMixin,GenericAPIView):
    serializer_class = DeductDataSerializer

    def get(self, request, *args, **kwargs):
        return Response({
            "success":"deduct data api callled successfully"
        })

    def post(self, request, data_plan_uuid, *args, **kwargs):
        try:
            data = Data.objects.get(id=data_plan_uuid)
        except:
            return Response({
                "error":"uuid does not exit"
            })

        data_network = data.network
        data_plan_id = data.network_id
        data_bandwidth = data.bandwidth

        # handle reseller pricing
        data_plan_price = data.amount

        profile = Profile.objects.get(user=request.user)
        if profile.reseller == True:
            # update the data plan price to the reseller price
            data_plan_price = data.reseller_amount

        # get the network ID dynamically 
        network_id = NETWORK_ID[data_network]

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # get serialized information
            vd = serializer.validated_data
            phone_number = vd['phone_number']

             # check wallet balance against the price of the data plan
            wallet = self.check_wallet_balance(amount=data_plan_price)
            balances = self.deduct_amount_from_balance(amount=data_plan_price)
            message = f'You have purchased {data_bandwidth} Data from {data_network}'
            trans = Transaction.objects.create(
                user=request.user,
                detail= message,
                old_balance=balances[0],
                new_balance= balances[1],
                phone_number=phone_number,
                status='Success',
                amount= data_plan_price,
                type= 'Data',
            )

            trans_serializer = TransactionSerializer(trans).data

            return Response(
                            data={
                                'status': 'success',
                                'message': trans_serializer
                            },
                            status=200
                        )
        else:
            return Response(
                data={
                    'status': 'error',
                    'message': response.json()
                },
                status=400
            )
        
'''
me testing the api for purchase above
'''

"""
Shared 247API purchase flow.

Money is taken from the wallet BEFORE the provider is called, so two requests
fired at the same time can't both pass the balance check and get value for one
payment. After the provider responds:
  - success          -> transaction saved as Success
  - definite failure -> wallet refunded, transaction saved as Refunded
  - unknown outcome  -> transaction saved as Pending, money held (timeouts,
                        5xx, unreadable responses). The provider may still
                        deliver, so refunding here could give value away.
                        The 247API webhook (or an admin) settles it.
"""
PROVIDER_TIMEOUT = (10, 60)  # (connect, read) seconds

OUTCOME_SUCCESS = 'success'
OUTCOME_FAILED = 'failed'
OUTCOME_PENDING = 'pending'

SERVICE_UNAVAILABLE_MSG = 'This service is temporarily unavailable. Please try again later.'


def _provider_headers():
    return {
        'Authorization': f'Token {API_PROVIDER_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


def _provider_status(body):
    if body.get('status') is False:
        return 'fail'
    return str(body.get('status') or body.get('Status') or '').strip().lower()


def _provider_text(body):
    for key in ('api_response', 'response', 'message'):
        value = body.get(key)
        if value:
            return str(value)
    return ''


def _clip(value, length):
    value = '' if value is None else str(value)
    return value[:length]


def call_provider(endpoint, payload):
    """POST to 247API. Returns (outcome, body_dict)."""
    try:
        resp = requests.post(
            API_BASE_URL + endpoint,
            json=payload,
            headers=_provider_headers(),
            timeout=PROVIDER_TIMEOUT,
        )
    except requests.exceptions.ConnectTimeout:
        # never reached the provider, nothing was purchased
        logger.error('247API connect timeout on %s', endpoint)
        return OUTCOME_FAILED, {'message': SERVICE_UNAVAILABLE_MSG}
    except requests.exceptions.RequestException as e:
        # request may have reached the provider (read timeout, dropped connection)
        logger.error('247API request error on %s: %s', endpoint, e)
        return OUTCOME_PENDING, {}

    try:
        body = resp.json()
    except ValueError:
        body = None
    if not isinstance(body, dict):
        logger.error('247API non-JSON response on %s (HTTP %s): %s', endpoint, resp.status_code, resp.text[:500])
        if 400 <= resp.status_code < 500:
            return OUTCOME_FAILED, {}
        return OUTCOME_PENDING, {}

    status = _provider_status(body)
    text = _provider_text(body).lower()

    if resp.status_code in (200, 201) and status in ('success', 'successful'):
        return OUTCOME_SUCCESS, body

    if status in ('fail', 'failed', 'error') or 400 <= resp.status_code < 500:
        if 'balance is low' in text or 'insufficient' in text or resp.status_code in (401, 403):
            # OUR 247API wallet/key problem, not the customer's - don't show it to them
            logger.error('247API account problem on %s (HTTP %s): %s', endpoint, resp.status_code, body)
            return OUTCOME_FAILED, {**body, 'message': SERVICE_UNAVAILABLE_MSG}
        return OUTCOME_FAILED, body

    logger.warning('247API unclear outcome on %s (HTTP %s): %s', endpoint, resp.status_code, body)
    return OUTCOME_PENDING, body


def _first_error(errors):
    for field, messages in errors.items():
        if isinstance(messages, (list, tuple)) and messages:
            return f'{field}: {messages[0]}'
        return f'{field}: {messages}'
    return 'Invalid request'


def error_response(message, status=400):
    return Response({'status': 'error', 'message': message}, status=status)


class ProviderPurchaseMixin(WalletCheckMixin):
    """Runs a purchase through 247API with deduct-first / refund-on-failure."""

    def add_to_total_purchase(self, amount):
        Wallet.objects.filter(user=self.check_profile()).update(
            total_purchase=Coalesce(F('total_purchase'), Decimal('0')) + amount
        )

    def run_purchase(self, *, amount, endpoint, payload, detail, trans_type,
                     phone_number='', network=None, success_detail=None, push_label=''):
        """
        success_detail: optional callable(body) -> (detail, response_text)
        used to put tokens / PINs on the receipt.
        """
        amount = Decimal(str(amount))
        if amount <= 0:
            return error_response('Invalid amount.')

        try:
            old_balance, new_balance = self.deduct_amount_from_balance(amount=amount)
        except ValidationError:
            return error_response('Wallet balance is too low for the transaction, Please fund your Wallet.')

        payload.setdefault('request-id', str(uuid4()))
        our_request_id = payload['request-id']

        outcome, body = call_provider(endpoint, payload)
        provider_text = _provider_text(body)

        record = {
            'detail': _clip(detail, 300),
            'phone_number': _clip(phone_number, 11),
            'amount': amount,
            'type': trans_type,
            'old_balance': old_balance,
            'response': _clip(provider_text or 'N/A', 300),
            'request_id': _clip(body.get('request-id') or our_request_id, 300),
        }
        if network is not None:
            record['network'] = _clip(network, 300)

        if outcome == OUTCOME_FAILED:
            self.refund_amount_to_balance(amount=amount)
            self.create_transaction_record(status='Refunded', new_balance=old_balance, **record)
            _send_push(self.request.user, f'{push_label} Purchase Failed', f'₦{amount} has been refunded to your wallet.')
            message = body.get('message') or provider_text or 'Purchase failed.'
            return error_response(f'{message} Your wallet has been refunded.')

        if outcome == OUTCOME_PENDING:
            # keep OUR id so the webhook can find this record
            record['request_id'] = our_request_id
            record['response'] = _clip(provider_text or 'Awaiting provider confirmation', 300)
            trans = self.create_transaction_record(status='Pending', new_balance=new_balance, **record)
            _send_push(self.request.user, f'{push_label} Purchase Processing', f'Your ₦{amount} {push_label.lower()} purchase is being processed.')
            trans_data = TransactionSerializer(trans).data
            return Response(
                {'status': 'pending', 'message': 'Transaction is processing. Check your transaction history shortly.', 'data': trans_data},
                status=202,
            )

        if success_detail is not None:
            detail_text, response_text = success_detail(body)
            record['detail'] = _clip(detail_text, 300)
            record['response'] = _clip(response_text, 300)

        trans = self.create_transaction_record(status='Success', new_balance=new_balance, **record)
        self.add_to_total_purchase(amount)
        _send_push(self.request.user, f'{push_label} Purchase Successful', record['detail'])

        trans_data = TransactionSerializer(trans).data
        # the app reads the receipt from 'data' (airtime, cable, electricity) or 'message' (data, exam)
        return Response({'status': 'success', 'data': trans_data, 'message': trans_data}, status=200)


class PurchaseAirtimeView(ProviderPurchaseMixin, GenericAPIView):
    serializer_class = AirtimeSerializer
    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        return Response({
            'status': 'success',
        }, status=200)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={'status': 'error', 'message': _first_error(serializer.errors), 'details': serializer.errors},
                status=400,
            )

        vd = serializer.validated_data
        phone_number = vd['phone_number']
        network = vd['network'].upper()
        amount = vd['amount']

        network_id = NETWORK_ID.get(network)
        if network_id is None:
            return error_response('This network is not supported.')
        blocked = network_block_message(network)
        if blocked:
            return error_response(blocked, status=503)

        payload = {
            "network": network_id,
            "phone": phone_number,
            "bypass": False,
            "plan_type": "VTU",
            "amount": int(amount),
        }
        return self.run_purchase(
            amount=amount,
            endpoint='airtime/',
            payload=payload,
            detail=f'You have purchased {amount} airtime from {network}',
            trans_type='Airtime',
            phone_number=phone_number,
            network=network,
            push_label='Airtime',
        )

 #================================================================================

''' modified code for airtime purchase '''

class PurchaseDataView1(WalletCheckMixin, GenericAPIView):
    serializer_class = DataSerializer
    # queryset = Airtime.
    permission_classes = [IsAuthenticated, ]
    
    
    def get(self, request, *args, **kwargs):
        return Response({
            'status': 'success',
        }, status=200)
    
    def post(self, request, data_plan_uuid, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            # Retrieve data plan information
            data = Data.objects.get(id=data_plan_uuid)
        except Data.DoesNotExist:
            return  JsonResponse({'status': 'error', 'message': 'This UUID does not exist'}, status=404)

        # Process data plan pricing
        data_plan_price = data.reseller_amount if Profile.objects.get(user=request.user).reseller else data.amount



        if serializer.is_valid():
            vd = serializer.validated_data

            # Data from the serializers
            phone_number = vd['phone_number']
            # network = vd['network'].upper()
            # amount = vd['amount']
            
            
            # check wallet balance method
            wallet = self.check_wallet_balance(amount=data_plan_price)
            message = f'You have purchased {data.bandwidth} Data from {data.network}'

            # Parameters and flow for the old process
            # request_params = {
            #     'username': settings.PG_USERNAME,
            #     'password': settings.PG_PASSWORD,
            #     'phone': phone_number,
            #     'network_id': network,
            #     'amount': amount,
            # }


            # parameters ,url and request for the new 
            network_id = NETWORK_ID[data.network]

            params = {
                "network": network_id,
                "mobile_number": phone_number,
                "plan": data.data_plan_id,
                "Ported_number": True,
            }

            headers = {
                'Authorization': f'Token {KVDATA_PROVIDER_TOKEN}',
                'Content-Type': 'application/json'
            }

            try:
                # Process the request
                # url = settings.PG_URL
                # response = requests.get(url, params=request_params)
                url = KVDATA_BASE_URL + 'data/'
                response = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(params),
                )
            
                if response.status_code == 201:
                        # check if the API returns a failed status
                        if response.json()['Status'] == 'failed':
                            return Response(
                                data={
                                    'status': 'error',
                                    'message': 'There was an Issue with Processing this request',
                                },
                                status=400,
                            )
                        balances = self.deduct_amount_from_balance(amount=data_plan_price)
                    
                        trans = Transaction.objects.create(
                            user=request.user,
                            detail= message,
                            old_balance=balances[0],
                            new_balance= balances[1],
                            phone_number=phone_number,
                            status='Success',
                            amount= data_plan_price,
                            type= 'Data',
                        )

                        trans_serializer = TransactionSerializer(trans).data

                        return Response(
                                        data={
                                            'status': 'success',
                                            'message': trans_serializer
                                        },
                                        status=200
                                    )
                        
                        # devices = FCMDevice.objects.filter(user=user.id)
                        # devices.send_message(
                        #     message =Message(
                        #         notification=Notification(
                        #             title='Data Purchase Completed',
                        #             body=f'Success🎉, You\'ve purchased {data_bandwidth} for ₦{data_plan_price}'
                        #         ),
                        #         token=FCMDevice.objects.get(user=user.id).device_id,
                        #     ),

                        #     app=settings.FCM_DJANGO_SETTINGS['DEFAULT_FIREBASE_APP']
                        # )

                else:
                    return Response(
                        data={
                            'status': 'error',
                            'message': response.json()
                        },
                        status=400
                    )
            except requests.exceptions.Timeout:
                logger.error('Request to KVDATA API Timed out')

                balances = self.deduct_amount_from_balance(amount=data_plan_price)
                trans_params = {
                    'detail': message,
                    'old_balance':balances[0],
                    'new_balance': balances[1],
                    'phone_number':phone_number,
                    'amount': data_plan_price,
                    'type': 'Data',
                }
                trans_params['status'] = 'Pending'
                self.create_transaction_record(
                    **trans_params
                )
                
                return Response(
                    data ={
                        'status': 'error',
                        'message': 'Transaction Pending',
                    },
                    status=504
                )
            
            except requests.exceptions.RequestException as e:
                logger.error(f'Error in the request to KVDATA API: {str(e)}')
                # trans_params['status'] = 'Pending'
                # self.create_transaction_record(
                #     **trans_params
                # )
                return Response(
                    data ={
                        'status': 'error',
                        'message': f'Service Failure {str(e)}'
                    },
                    status=500
                )
        
        return Response(
            data={
                'status': 'error',
                'details': serializer.errors
            },
            status=400,
            )

        #====================================================



import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

class PurchaseDataView2(WalletCheckMixin ,GenericAPIView):
    serializer_class = DataSerializer
    permission_classes = [IsAuthenticated,]

    def post(self, request, data_plan_uuid, *args, **kwargs):
        try:
            # Retrieve data plan information
            data = Data.objects.get(id=data_plan_uuid)
        except Data.DoesNotExist:
            return  JsonResponse({'status': 'error', 'message': 'This UUID does not exist'}, status=404)

        # Process data plan pricing
        data_plan_price = data.reseller_amount if Profile.objects.get(user=request.user).reseller else data.amount

        # Validate serializer
        # serializer = DataSerializer(data=request.POST)
        # if not serializer.is_valid():
        #     return JsonResponse({'status': 'error', 'details': serializer.errors}, status=400)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
        # Get serialized information
            phone_number = serializer.validated_data['phone_number']
        print(serializer.errors)
        # Check wallet balance against the price of the data plan
        wallet_balance = self.check_wallet_balance(amount=data_plan_price)
        if not wallet_balance:
            return JsonResponse({'status': 'error', 'message': 'Insufficient funds'}, status=400)

        # Construct the request parameters
        network_id = NETWORK_ID[data.network]
        print(serializer.errors)
        print(network_id)
        print(phone_number)
        print(data.data_plan_id)
        params = {
            "network": network_id,
            "mobile_number": phone_number,
            "plan": data.data_plan_id,
            "Ported_number": True,
        }

        headers = {
            'Authorization': f'Token {KVDATA_PROVIDER_TOKEN}',
            'Content-Type': 'application/json'
        }

        # Make the request to KVDATA API
        try:
            response = requests.post(KVDATA_BASE_URL + 'data/', data=json.dumps(params), headers=headers, timeout=20)
            response.raise_for_status()
            print(response.text)
            print(response.body)
            print(response.status_code)
            if response.status_code == 201 and response.json().get('Status') == 'success':
                # Deduct amount from balance
                new_balances = deduct_amount_from_balance(amount=data_plan_price)

                # Create transaction record
                trans = Transaction.objects.create(
                    user=request.user,
                    detail=f'You have purchased {data.bandwidth} Data from {data.network}',
                    old_balance=new_balances[0],
                    new_balance=new_balances[1],
                    phone_number=phone_number,
                    status='Success',
                    amount=data_plan_price,
                    type='Data',
                )

                trans_serializer = TransactionSerializer(trans).data

                # Send success response
                return JsonResponse({'status': 'success', 'message': trans_serializer}, status=200)

            else:
                return JsonResponse({'status': 'error', 'message': response.json()}, status=400)

        except requests.exceptions.Timeout:
            logger.error('Request to KVDATA API Timed out')

            # Create pending transaction record
            trans_params = {
                'detail': f'You have purchased {data.bandwidth} Data from {data.network}',
                'old_balance': wallet_balance[0],
                'new_balance': wallet_balance[1],
                'phone_number': phone_number,
                'amount': data_plan_price,
                'type': 'Data',
            }
            trans_params['status'] = 'Pending'
            create_transaction_record(**trans_params)

            return JsonResponse({'status': 'error', 'message': 'Transaction Pending'}, status=504)

        except requests.exceptions.RequestException as e:
            logger.error(f'Error in the request to KVDATA API: {str(e)}')
            return JsonResponse({'status': 'error', 'message': 'Service Failure'}, status=500)




















    
class PurchaseDataView(ProviderPurchaseMixin, GenericAPIView):
    serializer_class = DataSerializer
    permission_classes = [IsAuthenticated,]

    def post(self, request, data_plan_uuid, *args, **kwargs):
        try:
            data = Data.objects.get(id=data_plan_uuid)
        except (Data.DoesNotExist, ValueError, DjangoValidationError):
            return error_response('This data plan does not exist', status=404)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'message': _first_error(serializer.errors), 'details': serializer.errors}, status=400)

        phone_number = serializer.validated_data['phone_number']
        network_id = NETWORK_ID.get(str(data.network).upper())
        if network_id is None or not data.data_plan_id or not data.is_active:
            return error_response('This data plan is currently unavailable.', status=503)
        blocked = network_block_message(data.network)
        if blocked:
            return error_response(blocked, status=503)

        # reseller price only when one has been set, otherwise a 0.00 reseller price makes the plan free
        data_plan_price = data.amount
        if self.check_profile().reseller and data.reseller_amount and data.reseller_amount > 0:
            data_plan_price = data.reseller_amount

        payload = {
            "network": network_id,
            "phone": phone_number,
            "bypass": False,
            "data_plan": data.data_plan_id,
            "Ported_number": True,
        }
        return self.run_purchase(
            amount=data_plan_price,
            endpoint='data/',
            payload=payload,
            detail=f'You have purchased {data.bandwidth} Data from {data.network}',
            trans_type='Data',
            phone_number=phone_number,
            network=data.network,
            push_label='Data',
        )


class PurchaseElectricityView(ProviderPurchaseMixin, GenericAPIView):
    serializer_class = ElectricBillPaymentSerializer
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'message': _first_error(serializer.errors), 'details': serializer.errors}, status=400)

        vd = serializer.validated_data
        disco_id = ELECTRIC_DISCO_ID.get(vd['disco'])
        if disco_id is None:
            return error_response('This electricity provider is not supported.')

        amount = vd['amount']
        meter_number = str(vd['meter_number'])
        payload = {
            "disco": disco_id,
            "amount": int(amount),
            "meter_number": meter_number,
            "meter_type": vd['meter_type'].lower(),
            "bypass": True,
            "phone": vd['phone'],
        }

        def success_detail(body):
            token = body.get('token') or ''
            if token:
                return (
                    f'You have purchased ₦{amount} {vd["disco"]} for meter {meter_number}. Token: {token}',
                    f'Token: {token}',
                )
            return (
                f'You have paid ₦{amount} {vd["disco"]} for meter {meter_number}',
                _provider_text(body) or 'Payment Successful',
            )

        return self.run_purchase(
            amount=amount,
            endpoint='bill',
            payload=payload,
            detail=f'You have paid ₦{amount} {vd["disco"]} for meter {meter_number}',
            trans_type='Electricity',
            phone_number=vd['phone'],
            network=vd['disco'],
            success_detail=success_detail,
            push_label='Electricity',
        )


class PurchaseCableSubscriptionView(ProviderPurchaseMixin, GenericAPIView):
    serializer_class = CablePaymentSerializer
    permission_classes = [IsAuthenticated, ]
    queryset = CableSubscription.objects.all()

    def post(self, request, cable_uuid, *args, **kwargs):
        try:
            plan = CableSubscription.objects.get(id=cable_uuid)
        except (CableSubscription.DoesNotExist, ValueError, DjangoValidationError):
            return error_response('This cable plan does not exist', status=404)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'message': _first_error(serializer.errors), 'details': serializer.errors}, status=400)

        vd = serializer.validated_data
        provider = str(plan.provider).upper()
        if vd['cable_provider'].upper() != provider:
            return error_response(f'This plan is for {provider}, not {vd["cable_provider"]}.')

        cable_id = CABLE_PROVIDER_ID.get(provider)
        if cable_id is None or not plan.plan_id:
            return error_response('This cable plan is currently unavailable.')

        iuc = str(vd['iuc'])
        payload = {
            "cable": cable_id,
            "cable_plan": str(plan.plan_id),
            "iuc": iuc,
            "bypass": True,
        }
        return self.run_purchase(
            # price always comes from the plan, never from the request
            amount=plan.amount,
            endpoint='cable',
            payload=payload,
            detail=f'You have subscribed {plan.cable_service} (₦{plan.amount}) for IUC {iuc}',
            trans_type='Cable',
            phone_number=iuc,
            network=provider,
            push_label='Cable',
        )


MAX_EXAM_PIN_QUANTITY = 5  # keeps every PIN inside the 300-char receipt fields


class NetworkStatusListView(APIView):
    """Which networks are switched on, so the app can grey out the ones that are off."""
    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        from api.network_control import network_statuses
        return Response({'status': 'success', 'data': network_statuses()})


class ExamPinPriceListView(APIView):
    """Admin-set exam PIN prices, so the app shows what the backend will charge."""
    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        prices = ExamPinPrice.objects.all().order_by('exam')
        return Response([{'exam': p.exam, 'price': p.price} for p in prices])


def _format_exam_pins(body):
    pins = []
    for item in body.get('pins') or []:
        if isinstance(item, dict) and item.get('pin'):
            serial = item.get('serial')
            pins.append(f"PIN: {item['pin']} Serial: {serial}" if serial else f"PIN: {item['pin']}")
        elif isinstance(item, str):
            pins.append(f'PIN: {item}')
    if not pins:
        token = body.get('token') or body.get('pin')
        if token:
            pins.append(f'PIN: {token}')
    return ' | '.join(pins)


class PurchaseExamEpin(ProviderPurchaseMixin, GenericAPIView):
    serializer_class = PurchaseExamEpinSerializer
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'message': _first_error(serializer.errors), 'details': serializer.errors}, status=400)

        vd = serializer.validated_data
        exam_name = vd['exam_name'].strip().upper()
        exam_id = EXAM_RESULT_CHECKER.get(exam_name)
        if exam_id is None:
            return error_response('This exam is not supported.')

        try:
            quantity = int(str(vd['quantity']).strip())
        except ValueError:
            return error_response('Quantity must be a number.')
        if quantity < 1 or quantity > MAX_EXAM_PIN_QUANTITY:
            return error_response(f'Quantity must be between 1 and {MAX_EXAM_PIN_QUANTITY}.')

        # use the admin-set price when there is one; the app's amount is only a fallback
        price = ExamPinPrice.objects.filter(exam=exam_name).first()
        if price is not None:
            amount = Decimal(price.price) * quantity
        else:
            logger.warning('No ExamPinPrice set for %s, using amount sent by the app', exam_name)
            amount = vd['amount']

        payload = {
            "exam": exam_id,
            "quantity": quantity,
        }

        def success_detail(body):
            pins = _format_exam_pins(body)
            if not pins:
                logger.error('Exam purchase succeeded but no PIN in response: %s', body)
                pins = _provider_text(body) or 'PIN not returned, contact support'
            return f'{exam_name} x{quantity}: {pins}', pins

        return self.run_purchase(
            amount=amount,
            endpoint='exam',
            payload=payload,
            detail=f'You have purchased {quantity} {exam_name} PIN(s)',
            trans_type='Exam',
            network=exam_name,
            success_detail=success_detail,
            push_label='Exam PIN',
        )


"""
Section for validating Services Mainly Electricity and Cable.
"""
class BillValidatorMixin(RequestWrapper):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'fail', 'message': _first_error(serializer.errors), 'details': serializer.errors}, status=400)

        data = self.request_data(serializer.validated_data)
        if data is None:
            return Response({'status': 'fail', 'message': 'This provider is not supported.'}, status=400)

        try:
            response = requests.get(
                self.url + self.endpoint,
                params=data,
                headers=_provider_headers(),
                timeout=PROVIDER_TIMEOUT,
            )
            json_data = response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error('247API validation error on %s: %s', self.endpoint, e)
            return Response({'status': 'fail', 'message': SERVICE_UNAVAILABLE_MSG}, status=503)

        if not isinstance(json_data, dict):
            return Response({'status': 'fail', 'message': SERVICE_UNAVAILABLE_MSG}, status=503)

        name = str(json_data.get('name') or '').strip()
        # 247API answers "success" with name "Unable to verify" for numbers that don't exist
        if _provider_status(json_data) != 'success' or not name or name.lower() == 'unable to verify':
            message = json_data.get('message')
            if not message or str(message).lower() == 'unable to verify':
                message = self.not_found_message
            return Response({**json_data, 'status': 'fail', 'message': message}, status=400)

        return Response(json_data)


class ValidateMeterNumberAPI(BillValidatorMixin, GenericAPIView):
    serializer_class = ValidateMeterNumberSerializer
    permission_classes = [IsAuthenticated,]
    url = API_BASE_URL
    endpoint = 'bill/bill-validation'
    provider_token = API_PROVIDER_TOKEN
    not_found_message = 'Unable to verify this meter number. Check the number, meter type and electricity provider.'

    def request_data(self, valid_data):
        disco_id = ELECTRIC_DISCO_ID.get(valid_data['disco'])
        if disco_id is None:
            return None
        return {
            'meter_number': str(valid_data['meter_number']),
            'meter_type': valid_data['meter_type'].lower(),
            'disco': disco_id,
        }

class ValidateCableNumberAPI(BillValidatorMixin, GenericAPIView):
    serializer_class = ValidateCableNumber
    permission_classes = [IsAuthenticated,]
    url = API_BASE_URL
    endpoint = 'cable/cable-validation'
    provider_token = API_PROVIDER_TOKEN
    not_found_message = 'Unable to verify this IUC / smartcard number. Check the number and cable provider.'

    def request_data(self, valid_data):
        cable_id = CABLE_PROVIDER_ID.get(valid_data['cable_provider'].upper())
        if cable_id is None:
            return None
        return {
            'iuc': str(valid_data['iuc']),
            'cable': cable_id,
        }


class ProviderWebhookView(APIView):
    """
    247API webhook: settles transactions left Pending after a timeout.

    247API doesn't sign webhooks and its query endpoint returns 401, so the
    payload can't be verified. A success can only confirm a purchase already
    paid for, so it's applied. A failure is NOT auto-refunded (a forged one would
    hand out free money); it's noted on the transaction for an admin to check
    on the 247API dashboard and refund with admin/fund-account/.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        body = request.data if isinstance(request.data, dict) else {}
        request_id = str(body.get('request-id') or body.get('request_id') or '').strip()
        status = _provider_status(body)
        logger.info('247API webhook: request-id=%s status=%s', request_id, status)

        if not request_id:
            return Response({'status': 'ignored'}, status=200)

        with db_transaction.atomic():
            trans = (
                Transaction.objects.select_for_update()
                .filter(request_id=request_id, status='Pending')
                .first()
            )
            if trans is None:
                return Response({'status': 'ignored'}, status=200)

            provider_text = _clip(_provider_text(body), 300)
            if status in ('success', 'successful'):
                trans.status = 'Success'
                if provider_text:
                    trans.response = provider_text
                trans.save(update_fields=['status', 'response'])
                Wallet.objects.filter(user__user=trans.user).update(
                    total_purchase=Coalesce(F('total_purchase'), Decimal('0')) + trans.amount
                )
                settled = True
            elif status in ('fail', 'failed', 'error'):
                trans.response = _clip(f'PROVIDER REPORTED FAILURE - verify on 247API and refund. {provider_text}', 300)
                trans.save(update_fields=['response'])
                settled = False
            else:
                return Response({'status': 'ignored'}, status=200)

        if settled:
            _send_push(trans.user, f'{trans.type} Purchase Successful', trans.detail)
        else:
            logger.error('247API webhook reported failure for pending transaction %s (request-id %s)', trans.id, request_id)
        return Response({'status': 'received'}, status=200)


'''
Collecting the pricing plans for data plans for a certain network
'''
class DataPriceListAPI(ListAPIView):
    serializer_class = DataPriceSerializer
    # permission_classes = [IsAuthenticated, ]
    lookup_field = 'network'
    queryset = Data.objects.all()

    def get_queryset(self):
        
        return available_plans(Data.objects.filter(network=self.kwargs['network']))

        # return super().get_queryset()