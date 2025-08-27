from itertools import product
from re import search
from tracemalloc import Statistic

from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.sites.models import Site
from django.db.models import Q, Sum, Count, F
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, FormView, View, UpdateView, DetailView, CreateView, TemplateView

from apps.forms import AuthForm, ProfileModelForm, ChangePasswordForm, OrderModelForm, ThreadModelForm, \
    WithdrawModelForm, OrderUpdateModelForm
from apps.models import Category, Product, User, Region, District, Order, WishList, Thread, SiteSettings, \
    Withdraw


# Create your views here.
class HomeListView(ListView):
    queryset = Category.objects.all()
    template_name = 'apps/home.html'
    context_object_name = 'categories'

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['products'] = Product.objects.all()
        return data


class AuthFormView(FormView):
    form_class = AuthForm
    success_url = reverse_lazy('home')
    template_name = 'apps/auth/auth-page.html'

    def form_valid(self, form):
        user = form.user
        login(self.request, user)
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)


class LoginView(View):
    def get(self, request):
        logout(self.request)
        return redirect('auth')


class ProductListView(ListView):
    queryset = Product.objects.all()
    template_name = 'apps/product-list.html'
    context_object_name = 'products'

    def get_queryset(self):
        c_slug = self.request.GET.get('category_slug')
        query = super().get_queryset()
        if c_slug:
            query = query.filter(category__slug=c_slug)
        return query

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['categories'] = Category.objects.all()
        data['c_slug'] = self.request.GET.get('category_slug')
        return data


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    queryset = User.objects.all()
    template_name = 'apps/auth/profile.html'
    success_url = reverse_lazy('profile')
    form_class = ProfileModelForm
    pk_url_kwarg = None
    context_object_name = 'user'

    def get_object(self, *args, **kwargs):
        return self.request.user

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(**kwargs)
        data['regions'] = Region.objects.all()
        return data


def district_view(request):
    region_id = request.GET.get('region_id')
    districts = District.objects.filter(region_id=region_id).values('id', 'name')
    data = [{"id": district.get('id'), 'name': district.get('name')} for district in districts]
    return JsonResponse(data, safe=False)


class UserChangePassword(LoginRequiredMixin, FormView):
    form_class = ChangePasswordForm
    template_name = 'apps/auth/profile.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        old_password = form.cleaned_data.get('old_password')
        user = self.request.user
        if not check_password(old_password, user.password):
            messages.error(self.request, _('Password incorrect.'))
            return super().form_valid(form)
        form.update(user)
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)


class SearchProductListView(ListView):
    queryset = Product.objects.all()
    template_name = 'apps/search-product-list.html'
    context_object_name = 'products'

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        query = Product.objects.translated().filter(
            Q(translations__name__icontains=search) |
            Q(translations__description__icontains=search) |
            Q(category__translations__name__icontains=search)
        ).distinct()
        return query


class ProductDetailView(CreateView):
    queryset = Product.objects.all()
    form_class = OrderModelForm
    template_name = 'apps/order/order-form.html'
    context_object_name = 'product'

    def get_context_data(self, *args, **kwargs):
        product_slug = self.kwargs.get('slug')
        data = super().get_context_data(**kwargs)
        data['product'] = Product.objects.get(slug=product_slug)
        return data

    def form_valid(self, form):
        form.instance.total = form.cleaned_data['product'].price
        form.instance.customer = self.request.user  # Вот здесь указываем текущего пользователя как заказчика
        self.object = form.save()
        site = SiteSettings.objects.first()
        return render(self.request, 'apps/order/order-receive.html', context={'order': self.object, 'site': site})


class OrderListView(LoginRequiredMixin, ListView):
    queryset = Order.objects.all()
    template_name = 'apps/order/order-list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        query = super().get_queryset().filter(customer=self.request.user)
        return query


@login_required
def wishlist_view(request, pk):
    query = WishList.objects.filter(user=request.user, product_id=pk)

    if query.exists():
        query.delete()
    else:
        WishList.objects.create(user=request.user, product_id=pk)

    next_url = request.META.get('HTTP_REFERER', '/')
    return redirect(next_url)


class WishListView(ListView):
    queryset = WishList.objects.all()
    template_name = 'apps/auth/wishlist.html'
    context_object_name = 'wishlists'

    def get_queryset(self):
        query = super().get_queryset().filter(user=self.request.user)
        return query


class MarketListView(ListView):
    queryset = Product.objects.all()
    template_name = 'apps/market/market-list.html'
    context_object_name = 'products'

    def get_queryset(self):
        category_slug = self.request.GET.get('category_slug')
        query = super().get_queryset()
        if category_slug == 'top':
            query = query.annotate(order_count=Count('orders')).order_by('-orders')
        elif category_slug:
            query = query.filter(category__slug=category_slug)
        return query

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['categories'] = Category.objects.all()
        data['c_slug'] = self.request.GET.get('category_slug')
        return data


class ThreadCreateView(CreateView):
    queryset = Thread.objects.all()
    template_name = 'apps/market/market-list.html'
    form_class = ThreadModelForm
    success_url = reverse_lazy('thread-list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['categories'] = Category.objects.all()
        data['products'] = Product.objects.all()
        return data

    def form_valid(self, form):
        thread = form.save(commit=False)
        thread.owner = self.request.user
        thread.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)


class ThreadTListView(ListView):
    queryset = Thread.objects.all()
    template_name = 'apps/market/thread-list.html'
    context_object_name = 'threads'

    def get_queryset(self):
        query = super().get_queryset().filter(owner=self.request.user)
        return query


class ThreadDetailView(DetailView):
    queryset = Thread.objects.all()
    template_name = 'apps/order/order-form.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'thread'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        thread = data.get('thread')
        thread.visit_count += 1
        thread.save()
        data['product'] = self.object.product
        return data


class StatisticListView(ListView):
    queryset = Thread.objects.all()
    template_name = 'apps/market/statistics.html'
    context_object_name = 'threads'

    def get_queryset(self):
        query = super().get_queryset().filter(owner=self.request.user).annotate(
            new_count=Count('orders', filter=Q(orders__status=Order.StatusType.NEW)),
            ready_count=Count('orders', filter=Q(orders__status=Order.StatusType.READY_TO_DELIVERY)),
            delivering_count=Count('orders', filter=Q(orders__status=Order.StatusType.DELIVERING)),
            delivered_count=Count('orders', filter=Q(orders__status=Order.StatusType.DELIVERED)),
            not_call_count=Count('orders', filter=Q(orders__status=Order.StatusType.NOT_CALL)),
            canceled_count=Count('orders', filter=Q(orders__status=Order.StatusType.CANCELED)),
            archived_count=Count('orders', filter=Q(orders__status=Order.StatusType.ARCHIVED)),
        ).values(
            'visit_count', 'product__translations__name', 'name',
            'new_count', 'ready_count', 'delivering_count',
            'delivered_count', 'not_call_count', 'canceled_count', 'archived_count'
        )
        return query

    def get_context_data(self, *args, **kwargs):
        tmp = self.get_queryset().aggregate(
            visit_total=Sum('visit_count'),
            new_total=Sum('new_count'),
            ready_total=Sum('ready_count'),
            delivering_total=Sum('delivering_count'),
            delivered_total=Sum('delivered_count'),
            not_call_total=Sum('not_call_count'),
            canceled_total=Sum('canceled_count'),
            archived_total=Sum('archived_count'),
        )
        data = super().get_context_data()
        data.update(tmp)
        return data


class CompetitionListView(ListView):
    queryset = User.objects.all()
    template_name = "apps/market/competition.html"
    context_object_name = "sellers"

    def get_queryset(self):
        query = super().get_queryset().annotate(
            order_count=Count('threads__orders',
            filter=Q(threads__orders__status=Order.StatusType.DELIVERED))).filter(
            order_count__gt=1).values('order_count', 'first_name', 'last_name')

        return query

    def get_context_data(self, *args, **kwargs):
        data =super().get_context_data(*args, **kwargs)
        data['site'] = SiteSettings.objects.first()
        return data


class WithdrawCreateView(LoginRequiredMixin,CreateView):
    queryset = Withdraw.objects.all()
    template_name = 'apps/withdraw/withdraw-form.html'
    form_class = WithdrawModelForm
    success_url = reverse_lazy('withdraw-form')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['withdraws'] = Withdraw.objects.filter(user=self.request.user)
        return context

    def form_valid(self, form):
        user = self.request.user
        user.balance -= form.instance.amount
        user.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)




class OperatorOrderListView(ListView):
    queryset = Order.objects.all()
    template_name ='apps/operator/operator-page.html'
    context_object_name = 'orders'

    def get_queryset(self):
        status = self.request.GET.get('status','new')
        category_id = self.request.GET.get('category_id')
        district_id = self.request.GET.get('district_id')
        query = super().get_queryset()
        Order.objects.filter(operator=self.request.user).update(hold=False)
        if category_id:
            query = Order.objects.filter(product__category_id=category_id)
        if district_id:
            query = Order.objects.filter(district_id=district_id)


        if status!='new':
            query = query.filter(operator=self.request.user,status=status)
        else:
            query = query.filter(status=status)
        return query

    def get_context_data(self,*args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['status']=Order.StatusType.values
        data['categories']=Category.objects.all()
        data['regions']=Region.objects.all()
        category_id = self.request.GET.get('category_id')
        district_id = self.request.GET.get('district_id')
        if category_id:
            data['category_id']=int(category_id)
        if district_id:
            data['district_id']=int(district_id)

        return data




class OrderUpdateView(UpdateView):
    queryset = Order.objects.all()
    template_name = 'apps/operator/order-change.html'
    context_object_name = 'order'
    pk_url_kwarg = 'pk'
    form_class =OrderUpdateModelForm
    success_url = reverse_lazy('operator-orders')

    def get(self,request,*args,**kwargs):
        return_data = super().get(request,*args,**kwargs)
        self.object.hold=True
        self.object.save()
        return return_data
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.object
        kwargs['employee'] = self.request.user # ✅ Обязательно
        kwargs['operator'] = self.request.user

        kwargs['operator'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['regions'] = Region.objects.all()
        return data

class OrderDiagramView(TemplateView):
    template_name = 'apps/market/diagram.html'

def region_order_counts(request):
    regions = Region.objects.annotate(order_count=Count('districts__orders'))

    data = {
        "regions": [region.name for region in regions],
        "numbers": [region.order_count for region in regions]
    }
    return JsonResponse(data)