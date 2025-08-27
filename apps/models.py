from django.contrib.auth.hashers import make_password
from django.db.models import Model, CharField, ImageField, DecimalField, TextField, ForeignKey, IntegerField, \
    DateTimeField, CASCADE, URLField, SlugField, SET_NULL, SmallIntegerField, TextChoices, BooleanField, DateField, \
    EmailField
from django.contrib.auth.models import AbstractUser, UserManager
from django.template.defaultfilters import slugify
from parler.models import TranslatableModel, TranslatedFields
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUserManager(UserManager):
    use_in_migrations = True

    def _create_user_object(self, phone_number, password, **extra_fields):

        user = self.model(phone_number=phone_number, **extra_fields)
        user.password = make_password(password)
        return user

    def _create_user(self, phone_number, password, **extra_fields):
        user = self._create_user_object(phone_number, password, **extra_fields)
        user.save(using=self._db)
        return user

    async def _acreate_user(self, phone_number, password, **extra_fields):
        user = self._create_user_object(phone_number, password, **extra_fields)
        await user.asave(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, password, **extra_fields)

    create_user.alters_data = True

    async def acreate_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return await self._acreate_user(phone_number, password, **extra_fields)

    acreate_user.alters_data = True

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone_number, password, **extra_fields)

    create_superuser.alters_data = True

    async def acreate_superuser(
        self, phone_number, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return await self._acreate_user(phone_number, password, **extra_fields)

    acreate_superuser.alters_data = True

class User(AbstractUser):
    class RoleType(TextChoices):
        ADMIN = "admin", "Admin"
        OPERATOR = "operator", "Operator"
        DELIVER = "deliver", "Deliver"
        USER = 'user', 'User'

    phone_number = CharField(max_length=20, unique=True)
    email = EmailField(unique=True, null=True, blank=True)  # ✅ Вернули обратно
    username = None

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    telegram_id = CharField(max_length=50, default='')
    about = TextField(default='')
    address = CharField(default='', max_length=255)
    district = ForeignKey('apps.District', SET_NULL, null=True, blank=True, related_name='users')
    balance = DecimalField(default=0, null=True, blank=True, max_digits=10, decimal_places=0)
    role = CharField(choices=RoleType, max_length=20, default=RoleType.USER)

    def wishlist_products(self):
        return list(self.wishlist.all().values_list('product__pk', flat=True))

class Region(Model):
    name = CharField(max_length=255)

class District(Model):
    name = CharField(max_length=255)
    region = ForeignKey('apps.Region', CASCADE,related_name='districts')

class BaseSlug(TranslatableModel):
    slug = SlugField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        slug = slugify(self.name)
        query = self.__class__.objects.filter(slug=slug)
        while query.exists():
            slug += '-1'

        self.slug = slug
        return super().save(*args, **kwargs)

class Category(BaseSlug):
    icon = URLField()
    translations = TranslatedFields(
        name=models.CharField(verbose_name='name',max_length=255),
    )

class Product(BaseSlug):
    image = ImageField(upload_to="products/")
    translations = TranslatedFields(
        name=models.CharField(verbose_name='name', max_length=255),
        description=models.TextField(verbose_name='description'),
    )
    price = DecimalField(max_digits=9, decimal_places=0)
    quantity = IntegerField(default=1)
    category = ForeignKey("apps.Category", CASCADE, related_name="products")
    create_at = DateTimeField(auto_now_add=True)
    update_at = DateTimeField(auto_now=True)
    seller_prise = DecimalField(max_digits=100, decimal_places=0)
    message_id =CharField( max_length=255)

class Order(Model):
    class StatusType(TextChoices):
        NEW = "new", _("New")
        READY_TO_DELIVERY = "ready_to_delivery", _("Ready To Delivery")
        DELIVERING = "delivering", _("Delivering")
        DELIVERED = "delivered", _("Delivered")
        NOT_CALL = "not_call", _("Not Call")
        CANCELED = "canceled", _("Canceled")
        ARCHIVED = "archived", _("Archived")

    customer = ForeignKey("apps.User", SET_NULL ,null=True, blank=True, related_name="orders")
    product = ForeignKey("apps.Product", SET_NULL,null=True, blank=True, related_name="orders")
    delivered_date = DateField(null=True, blank=True)
    fullname = CharField(max_length=255)
    phone_number = CharField(max_length=20)
    quantity = SmallIntegerField(default=1)
    total = DecimalField(max_digits=9, decimal_places=0)
    created_at = DateTimeField(auto_now_add=True)
    status = CharField(choices=StatusType.choices,default=StatusType.NEW)
    comment = CharField(null=True, blank=True)
    district = ForeignKey('apps.District', SET_NULL, blank=True,null=True,related_name='orders')
    thread = ForeignKey('apps.Thread',SET_NULL,null=True,blank=True, related_name='orders')
    operator = ForeignKey('apps.User',SET_NULL,null=True,blank=True, related_name='operator_orders')
    deliver = ForeignKey('apps.User',SET_NULL,null=True,blank=True, related_name='deliver_orders')
    hold = BooleanField(default=False)


class WishList(Model):
    user = ForeignKey('apps.User', CASCADE, related_name='wishlist')
    product = ForeignKey('apps.Product', CASCADE, related_name='wishlist')

class Thread(Model):
    owner = ForeignKey('apps.User', CASCADE, related_name='threads')
    product = ForeignKey('apps.Product', CASCADE, related_name='threads')
    discount = DecimalField(max_digits=9, decimal_places=0)
    name = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    visit_count = IntegerField(default=0)


    @property
    def discount_price(self):
        return self.product.price - self.discount

class SiteSettings(Model):
    delivery_price = DecimalField(max_digits=9, decimal_places=0)
    competition_thumbnail = ImageField(upload_to="site-settings/")
    discount_price = DecimalField(max_digits=9,decimal_places=0,default=0)

class Withdraw(Model):
    class WithdrawStatus(TextChoices):
        REVIEW = "review", "Review"
        COMPLETED = "completed", "Completed"
        CANCEL = 'cancel', "Cancel"

    amount = DecimalField(max_digits=9, decimal_places=0)
    pay_check = ImageField(upload_to="withdraw/",null=True)
    user = ForeignKey('apps.User', SET_NULL,null=True,blank=True, related_name='withdraws')
    comment = TextField(null=True)
    status = CharField(choices=WithdrawStatus,max_length=50,default=WithdrawStatus.REVIEW)
    card_number = CharField(max_length=20)
    pay_at = DateTimeField(auto_now_add=True)



