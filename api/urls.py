from api.other_views.auth_views import CustomResetPassword
from .url_imports import *
from .views import DataNetworkViewAPIView, SingleCableProviderPlan
app_name = 'api'


urlpatterns = [
    # path('api/airtime-plans/', AirtimeAPIView.as_view(), name='airtime_plans'),
    path('cable-subscription-plans/', CableSubscriptionAPIView.as_view(), name='cable_plans'),
    path('display-deposit-records/', DisplayDepositRecordsView.as_view(), name='cable_plans'),
    path('DisplayDepositRecordsPerUserView/<str:id>/', DisplayDepositRecordsPerUserView.as_view(), name='deposit'),
    path('data-network-plans/', DataNetworkViewAPIView.as_view(), name='data_plans'),
    # path('data-network-plan/<str:network>', DataPriceListAPI.as_view(), name='data_plan'),
    path('data-plans/<str:network_provider_name>/', SingleDataNetworkView.as_view(), name='data_plan'),
    path('all-data-plans/', AllDataNetworkView.as_view(), name='data_plan'),
    path('electricity-subscription-plans/', ElectricitySubscriptionAPIView.as_view(), name='electricity_plan'),
    path('cable-plan/<str:provider>/', SingleCableProviderPlan.as_view()),

]

'''
# admin only routes
'''
urlpatterns += [
    # fund account
    path('admin/fund-account/', FundCustomerAccount.as_view(), name='fund-customer-account'),
    path('admin/payment_webhook/', payment_webhook, name='payvessel-payment-done'),
    path('admin/display-deposit-records/', DisplayDepositRecordsView.as_view(), name='display-deposit-records'),
    
    # private url
    path('admin/wallet/', CustomersWalletBalances.as_view(), name='customer-wallet-balances'),
    path('admin/wallet-per-user/', UserWalletBalance.as_view(), name='wallet-balance-per-user'),

    # provider api
    path('admin/provider-balance/', ProviderAPIBalanceView.as_view(), name='provider-balance'),

    # sales tracking
    path('sales-tracking/today/', DailySalesTracking.as_view(), name='daily-sales'),
    path('sales-tracking/yesterday/', YesterdaySalesTracking.as_view(), name='yesterday-sales'),
    path('sales-tracking/this-week/', SalesTrackingForThisWeek.as_view(), name='this-weeks-sales'),
    path('sales-tracking/last-week/', SalesTrackingForLastWeek.as_view(), name='last-weeks-sales'),
    path('sales-tracking/month/', SalesTrackingForThisMonth.as_view(), name='month-sales'),
    path('sales-tracking/last-month/', SalesTrackingForLastMonth.as_view(), name='last-month-sales'),
    path('sales-tracking/range/<str:start_date>/<str:end_date>/', FilterTransactionsByRangeView.as_view(), name='filter-trans-by-date-range'),

    # notifications
    path('admin/notification/announcement/', AnnouncementNotificationView.as_view(), name='announcement-notification'),
]
#UpdateTransactionPinWithPasswordAPIView
# authentication routes
urlpatterns += [
    path('user/create-account/', CreateUserAccountView.as_view(), name='create-account'),
    path('user/login-user/', LoginUser.as_view(), name='create-account'),
    path('user/transaction-pin/', CreateTransactionPinAPIView.as_view(), name='create-pin'),
    path('user/update-transaction-pin/', UpdateTransactionPinWithPasswordAPIView.as_view(), name='update-pin'),
    path('user/logout-user/', LogOut.as_view(), name='logout-account'),
    path('user/create/profile/', CreateProfileAPIView.as_view(), name='profile'),
    path('user/update/profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('user/change-password/', ChangePasswordView.as_view(), name='change-password' ),
    path('password_reset/', CustomResetPassword.as_view(), name='password_reset'),

]

# dashboard routes
urlpatterns += [
    path('dashboard/home/', UserDashboardView.as_view(), name='dashboard-home'),
    path('payment-proof/', PaymentProofView.as_view(), name='payment-proof'),
    path('reserve-acct-for-user/', ReservedAccountCreation.as_view(), name='payment-proof'),
    path('get-all-reserved-account/', GetAllReservedAccount.as_view(), name='all-accts'),
    path('Recent-transactions/', RecentTransactions.as_view(), name='all-accts'),
    path('AnnouncementApiView/', AnnouncementApiView.as_view(), name='all-accts'),

    # single transaction
    path('transaction/<str:trans_uuid>/', SingleTransaction.as_view(), name='transaction-details'),

    # trans for today & yesterday
    path('transactions/today/', TransactionsToday.as_view(), name='transactions-today'),
    path('transactions/yesterday/', TransactionsYesterday.as_view(), name='transactions-yesterday'),
    
    # current & past week
    path('transactions/last-week/', TransactionsLastWeek.as_view(), name='transactions-last-week'),
    path('transactions/this-week/', TransactionsThisWeek.as_view(), name='transactions-this-week'),

    # current & past week
    path('transactions/last-month/', TransactionsLastMonth.as_view(), name='transactions-last-month'),
    path('transactions/this-month/', TransactionsThisMonth.as_view(), name='transactions-this-month'),

    # Trans by range and all transactions
    path('transactions/<str:start_date>/<str:end_date>/', TransactionByRange.as_view(), name='transactions-by-range'),
    path('transactions/all/', AllTransactionRecords.as_view(),),
    path('transactions/ToBeFilteredTransactions/', ToBeFilteredTransactions.as_view(),),

    # query user's customers phone numbers
    path('transactions/phone-numbers/', FilterPhoneNumbersFromTransactions.as_view(), name='customers-phone-numbers'),

    # fcm connector
    path('fcm-connector/',  FCMDeviceInfoConnectorAPI.as_view()),
    path('transactions/wallet-statistic/', WalleStatistic.as_view(), name='wallet-statistic'),

    # get wallet stats

]
#5165884a-e696-47cd-808d-c42b0b23165a
# purchase routes
urlpatterns += [
    path('purchase/airtime/', PurchaseAirtimeView.as_view(), name='purchase-airtime'),
    #path('purchase/airtime1/', DeductTest.as_view(), name='DeductTest'),
    path('purchase/data/<str:data_plan_uuid>/', PurchaseDataView.as_view(), name='purchase-data'),
    #path('purchase/data1/<str:data_plan_uuid>/', DeductData.as_view(), name='deduct-data'),
    path('electric-bill/purchase/', PurchaseElectricityView.as_view()),
    path('cable-subscription/purchase/<str:cable_uuid>/', PurchaseCableSubscriptionView.as_view()),
    path('Data-price-list-API/purchase/<str:network>/', DataPriceListAPI.as_view()),
    path('purchase/exam-epin/',PurchaseExamEpin.as_view()),

    # validate Meter / IUC
    path('electric-bill/validate/', ValidateMeterNumberAPI.as_view()),
    path('cable-subscription/validate/', ValidateCableNumberAPI.as_view()),


]