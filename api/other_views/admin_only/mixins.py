# import User Model
from django.contrib.auth.models import User
from django.db.models import Sum

# rest frmework
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response


# import custom date periods package
from api.date_package.converterv2 import OtherDateFilters

class UserDataMixin:
    def users_list(self):
        # get all the Users
        users = User.objects.values_list('username')
        return [user[0] for user in users]

class GenericSalesTrackingMixin(OtherDateFilters, UserDataMixin, GenericAPIView):
    def get(self, request, *args, **kwargs):
            return Response(
                data={
                    'total_trans': self.total_trans()[0],
                    'total_trans_count': self.total_trans()[1],
                    'users': self.all_users_numbers()
                }, 
                status = 200
            )
    
    def filter_all_trans_in_db(self):
        None
    
    def total_trans(self):
        # query trans model and get the total count on todays
        # transactions
        trans_model = self.filter_all_trans_in_db()
        total_trans = trans_model.count()

        # get the total sum of airtime and data trans
        airtime = trans_model.filter(type='Airtime').aggregate(Sum('amount'))
        data = trans_model.filter(type='Data').aggregate(Sum('amount'))

        airtime_sum = airtime['amount__sum'] or 0
        data_sum = data['amount__sum'] or 0

        trans_today = {
            'sum': airtime_sum + data_sum,
            'airtime': airtime_sum,
            'data': data_sum,
        }
        return [trans_today, total_trans]

    def all_users_numbers(self, **kwargs):
        sales_list = []
        # view the transactions Sum of each individual and add the user to a Dict(kwargs)
        for user in self.users_list():
            user_model = User.objects.get(username=user)
            # trans = Transaction.objects.filter(user=user_model, date_and_time__date=date.today()).aggregate(Sum('amount'))
            airtime = self.filter_all_trans_in_db().filter(user=user_model, type='Airtime').aggregate(Sum('amount'))
            data = self.filter_all_trans_in_db().filter(user=user_model, type='Data').aggregate(Sum('amount'))
            
            user_details = {
                'name': user,
                'airtime': airtime.get('amount__sum') or 0,
                'data': data.get('amount__sum') or 0
            }
            sales_list.append(user_details)
        return sales_list
    
    
   