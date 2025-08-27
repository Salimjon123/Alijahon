import datetime

from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError

from django.forms import Form, PasswordInput, ModelForm, CharField
import re

from django.utils.translation import gettext as _

from apps.models import User, Order, Thread, SiteSettings, Withdraw


class AuthForm(Form):
    phone_number = CharField(max_length=20)
    password = CharField(max_length=8)

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise ValidationError("Phone number is required.")
        return re.sub(r'\D', '', phone_number)

    def clean(self):
        data = super().clean()
        phone_number = data.get('phone_number')
        password = data.get('password')

        if not phone_number or not password:
            raise ValidationError("Both phone number and password are required.")

        query = User.objects.filter(phone_number=phone_number)
        if query.exists():
            user = query.first()
            if user.check_password(password):
                self.user = user
            else:
                raise ValidationError(_("The password is incorrect."))
        else:
            self.user = self.save()
        return data

    def save(self):
        data = self.cleaned_data
        return User.objects.create_user(
            phone_number=data.get('phone_number'),
            password=data.get('password')
        )


class ProfileModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileModelForm,self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


    class Meta:
        model = User
        fields = 'first_name', 'last_name', 'district','address','telegram_id','about'



class ChangePasswordForm(Form):
    old_password = CharField(max_length=255)
    new_password = CharField(max_length=255)
    confirm_password = CharField(max_length=255)

    def clean_confirm_password(self):
        new_password = self.cleaned_data.get('new_password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if new_password != confirm_password:
            raise ValidationError(_("The password is incorrect."))
        return confirm_password


    def update(self,user):
        new_password = self.cleaned_data.get('new_password')
        user.set_password(new_password)
        user.save()






class OrderModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['thread'].required = False
        self.fields['total'].required = False

    class Meta:
        model = Order
        fields = 'phone_number', 'fullname', 'product','total','thread'

    def clean_phone_number(self):
        product = self.cleaned_data.get('product')
        thread_id = self.data.get('thread')
        thread = Thread.objects.get(pk=thread_id)
        site = SiteSettings.objects.first()
        total_price = product.price
        if thread:
            total_price -= thread.discount + site.discount
        return total_price


    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        return re.sub(r'\D', '', phone_number)



class ThreadModelForm(ModelForm):
    class Meta:
        model = Thread
        fields = 'name', 'product', 'discount'

    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        product = self.cleaned_data.get('product')

        if not product:
            raise ValidationError(_("Product is required."))

        if product.seller_prise < discount:
            raise ValidationError(_("The discount is incorrect."))

        return discount

class WithdrawModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['user'].required = False

    class Meta:
        model = Withdraw
        fields = 'card_number','amount','user'

    def clean_user(self):
        return self.user

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        user = self.user
        if amount > user.balance:
            raise ValidationError(_("You don't have enough money."))
        return amount



class OrderUpdateModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        self.employee = kwargs.pop('employee', None)
        self.operator = kwargs.pop('operator', None)
        super().__init__(*args, **kwargs)
        self.fields['quantity'].required = False
        self.fields['district'].required = False
        self.fields['status'].required = False
        self.fields['comment'].required = False
        self.fields['delivered_date'].required = False
        self.fields['operator'].required = False
    class Meta:
        model = Order
        fields = 'quantity','district','status','comment','delivered_date','operator','deliver'

    def clean_operator(self):
        if self.employee and self.employee.role == User.RoleType.OPERATOR:
            return self.employee
        return None

    def clean_deliver(self):
        if self.employee and self.employee.role == User.RoleType.DELIVER:
            return self.employee
        return None

    def clean_quantity(self):
        order = self.order
        quantity = self.cleaned_data.get('quantity')
        if not quantity:
            quantity = order.quantity
        site = SiteSettings.objects.first()
        order = self.order


        if order.product.quantity < quantity:
            raise ValidationError(_("The quantity is incorrect."))

        if order.thread:
            order.total += order.thread.discount_price * quantity + site.discount_price
        else:
            order.total += order.product.price*quantity+site.discount_price
        order.save()
        return quantity

    def clean_delivered_date(self):
        delivered_date = self.cleaned_data.get('delivered_date')

        if datetime.date.today() > delivered_date :
            raise ValidationError(_("Delivery date is incorrect."))
        return delivered_date











