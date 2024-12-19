# date
from datetime import datetime, timedelta

# restframework
from rest_framework.permissions import IsAuthenticated, IsAdminUser

# import models
from api.models import Transaction


# import mixins
from .mixins import GenericSalesTrackingMixin

ONE_DAY = timedelta(days=1)
ONE_WEEK = timedelta(days=7)
THIRTY_DAYS = timedelta(days=30)

'''
Today and previous days sales tracking sheet
'''
class DailySalesTracking(GenericSalesTrackingMixin):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def filter_all_trans_in_db(self):
        return Transaction.objects.filter(date_and_time__date=self.todays_date_time())


class YesterdaySalesTracking(GenericSalesTrackingMixin):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def filter_all_trans_in_db(self):
        return Transaction.objects.filter(date_and_time__date=self.todays_date_time() - ONE_DAY)



'''# weekly'''
class SalesTrackingForThisWeek(GenericSalesTrackingMixin):
    # This week
    permission_classes = [IsAuthenticated, IsAdminUser]

    def filter_all_trans_in_db(self):
        return Transaction.objects.filter(date_and_time__range=[
            self.monday(), self.todays_date_time() + ONE_DAY
        ])


class SalesTrackingForLastWeek(GenericSalesTrackingMixin):
    # last week
    permission_classes = [IsAuthenticated, IsAdminUser]

    def filter_all_trans_in_db(self):
        return Transaction.objects.filter(date_and_time__range=[
            self.past_monday(), self.past_monday() + ONE_WEEK 
        ])

'''# monthly'''
class SalesTrackingForThisMonth(GenericSalesTrackingMixin):
    # This month
    permission_classes = [IsAuthenticated, IsAdminUser]

    def filter_all_trans_in_db(self):
        return Transaction.objects.filter(date_and_time__range=[
            self.currenMonthStart(), self.currenMonthEnd() + ONE_DAY
            ],
        )


class SalesTrackingForLastMonth(GenericSalesTrackingMixin):
    # Last month
    permission_classes = [IsAuthenticated, IsAdminUser]

    def filter_all_trans_in_db(self):
        thirty_days_months = [9,4,6,11]
        feb = [2]
        
        if self.month not in thirty_days_months:
            if self.month not in feb:
                THIRTY_DAYS= timedelta(days=31)
            else:
                THIRTY_DAYS = timedelta(days=28)
        else:
            THIRTY_DAYS = timedelta(days=30)
        
        return Transaction.objects.filter(date_and_time__range=[
            self.currenMonthStart() - THIRTY_DAYS, self.currenMonthEnd() - THIRTY_DAYS + ONE_DAY
            ],
        )
    
'''
# Range filter for transactions
'''
class FilterTransactionsByRangeView(GenericSalesTrackingMixin):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def filter_all_trans_in_db(self):
        # get start and end date
        # add the 1 day to the end date
        # convert back to date time
        start_date = self.kwargs['start_date']
        end_date = self.kwargs['end_date']
        end_date_str_to_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        end_date_date_to_str = datetime.strftime(end_date_str_to_date, '%Y-%m-%d')



        return Transaction.objects.filter(date_and_time__range=[
            start_date, end_date_date_to_str
            ],
        )

'''# year'''