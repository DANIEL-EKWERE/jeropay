from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

# serializers
from api.other_serializers.admin.wallet_balance_serializer import CustomerWalletBalanceSerializer, UserWalletBalanceSerializer
from api.models import Wallet, Profile

class CustomersWalletBalances(ListAPIView):
    serializer_class = CustomerWalletBalanceSerializer
    permission_classes = [IsAuthenticated,]
    queryset = Wallet.objects.all()
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        for user_data in serializer.data:
            profile_info = user_data['user']
            profile = Profile.objects.get(id=profile_info)
            user_data['user'] = profile.user.username
        return Response(serializer.data)
import requests
# class UserWalletBalance(GenericAPIView):
#     serializer_class = CustomerWalletBalanceSerializer
#     permission_classes = [IsAuthenticated,]
#     queryset = Wallet.objects.all()

#     def get(self, request, *args, **kwargs):

        
#         serializer = self.get_serializer(queryset)
#         user = request.user
#         pro = Profile.objects.get(user=user)
#         wallet = Wallet.objects.get(profile=pro)
#         wallet_balance = wallet.balance
    
#         return Response({'message':'user not found','balance':serializer.data})
#         return Response({
#             'balance':wallet_balance
#         },status=200)



from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class UserWalletBalance(RetrieveAPIView):
    serializer_class = CustomerWalletBalanceSerializer
    permission_classes = [IsAuthenticated,]

    def get_object(self):
        # Retrieve the wallet object for the authenticated user
        profile = Profile.objects.get(user=self.request.user)
        return Wallet.objects.get(user=profile)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
