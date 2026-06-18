from django.shortcuts import render

# Create your views here.
from .models import Airtime, CableSubscription, Data, ElectricitySubscription, Wallet, Profile
from .serializer import CableSubscriptionSerializer, DataSerializer, ElectricitySubscriptionSerializer, WalletSerializer, ProfileSerializer
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.generics.views import ser
# Create your views here.


class HelloView(APIView):
    permission_classes = (IsAuthenticated, )
  
    def get(self, request):
        content = {'message': 'Hello, Micro E-pay'}
        return Response(content)
    
class CableSubscriptionAPIView(generics.ListAPIView):
    queryset = CableSubscription.objects.all()
    serializer_class = CableSubscriptionSerializer

class DataNetworkViewAPIView(generics.ListAPIView):
    queryset = Data.objects.all()
    serializer_class = DataSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['network']
    
class SingleDataNetworkView(generics.GenericAPIView):
    serializer_class = DataSerializer
    # permission_classes = [IsAuthenticated, ]

    def get(self, request, network_provider_name, *args, **kwargs):
        
        network_provider_name = network_provider_name.upper()

        if network_provider_name == 'MTN':
            data_network_provider = Data.objects.filter(network=network_provider_name, plan_type='SME').order_by('amount')
        else:
            data_network_provider = Data.objects.filter(network=network_provider_name).order_by('amount')
        
        # Check if the user is a reseller
        profile = Profile.objects.get(user=request.user)      
        if profile.reseller:
            for data in data_network_provider:
                data.amount = data.reseller_amount
        
        serializer = self.get_serializer(data_network_provider, many=True)
        
        return Response(
            data={
                'status': 'success',
                'data': serializer.data
            }
        )

class AllDataNetworkView(generics.GenericAPIView):
    serializer_class = DataSerializer
    # permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        

        # if network_provider_name == 'MTN':
        #     data_network_provider = Data.objects.filter(network=network_provider_name, plan_type='SME').order_by('amount')
        # else:
        #     data_network_provider = Data.objects.filter(network=network_provider_name).order_by('amount')


        data_network_provider = Data.objects.all().order_by('network')        
        # Check if the user is a reseller
        profile = Profile.objects.get(user=request.user)      
        if profile.reseller:
            for data in data_network_provider:
                data.amount = data.reseller_amount
        
        serializer = self.get_serializer(data_network_provider, many=True)
        
        return Response(
            data={
                'status': 'success',
                'data': serializer.data
            }
        )

class SingleCableProviderPlan(generics.ListAPIView):
    queryset = CableSubscription.objects.all()
    serializer_class = CableSubscriptionSerializer
    lookup_field = 'provider'

    def get_queryset(self):
        return CableSubscription.objects.filter(provider=self.kwargs['provider']).order_by('amount')

    
class ElectricitySubscriptionAPIView(generics.ListAPIView):
    queryset = ElectricitySubscription.objects.all()
    serializer_class = ElectricitySubscriptionSerializer

# class ProfileAPIView(generics.ListAPIView):
#     queryset = Profile.objects.all()
#     serializer_class = ProfileSerializer