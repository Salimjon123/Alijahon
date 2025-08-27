from django.contrib import admin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.views import HomeListView, AuthFormView, ProductListView, ProfileUpdateView, district_view, \
    UserChangePassword, SearchProductListView, ProductDetailView, OrderListView, wishlist_view, WishListView, \
    MarketListView, ThreadCreateView, ThreadTListView, ThreadDetailView, StatisticListView, CompetitionListView, \
    WithdrawCreateView, OperatorOrderListView, OrderUpdateView, region_order_counts, OrderDiagramView

urlpatterns = [
    path('', HomeListView.as_view(), name='home'),
    path('product-list', ProductListView.as_view(), name='product-list'),
    path('product-detail/<str:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('order-list',OrderListView.as_view(), name='order-list'),
    path('auth', AuthFormView.as_view(), name='auth'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('user/profile', ProfileUpdateView.as_view(), name='profile'),
    path('district-list', district_view, name='district_list'),
    path('change-password', UserChangePassword.as_view(), name='district'),
    path('search', SearchProductListView.as_view(), name='search'),
    path('wishlist/<int:pk>', wishlist_view, name='wishlist'),
    path('wish/list', WishListView.as_view(), name='wish-list'),
    path('market-list/', MarketListView.as_view(), name='market-list'),
    path('thread-form', ThreadCreateView.as_view(), name='thread-form'),
    path('thread-list', ThreadTListView.as_view(), name='thread-list'),
    path('thread/<int:pk>', ThreadDetailView.as_view(), name='thread'),
    path('thread/statistic', StatisticListView.as_view(), name='thread-statistic'),
    path('thread/competition', CompetitionListView.as_view(), name='thread-competition'),
    path('withdraw-form', WithdrawCreateView.as_view(), name='withdraw-form'),
    path('operator/order/list', OperatorOrderListView.as_view(), name='operator-orders'),
    path('operator/order/update/<int:pk>', OrderUpdateView.as_view(), name='order-update'),
    path('order/diagram/', OrderDiagramView.as_view(), name='order_diagram'),
    path('order/diagram/data/', region_order_counts, name='region_order_counts'),


]
