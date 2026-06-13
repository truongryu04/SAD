from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class UserAccount(models.Model):
	ROLE_CUSTOMER = "CUSTOMER"
	ROLE_STAFF = "STAFF"
	ROLE_ADMIN = "ADMIN"
	ROLE_CHOICES = (
		(ROLE_CUSTOMER, "Customer"),
		(ROLE_STAFF, "Staff"),
		(ROLE_ADMIN, "Admin"),
	)

	username = models.CharField(max_length=100, unique=True)
	full_name = models.CharField(max_length=150, blank=True)
	password = models.CharField(max_length=255)
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER, db_index=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def set_password(self, raw_password: str) -> None:
		self.password = make_password(raw_password)

	def verify_password(self, raw_password: str) -> bool:
		return check_password(raw_password, self.password)

	def __str__(self) -> str:
		return self.username


class Cart(models.Model):
	user = models.ForeignKey(
		UserAccount,
		on_delete=models.CASCADE,
		related_name="carts",
	)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"Cart #{self.id} - {self.user.username}"


class CartItem(models.Model):
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
	item_type = models.CharField(max_length=20)
	item_id = models.IntegerField()
	quantity = models.PositiveIntegerField(default=1)

	def __str__(self) -> str:
		return f"{self.item_type}:{self.item_id} x {self.quantity}"


class SearchHistory(models.Model):
	user = models.ForeignKey(
		UserAccount,
		on_delete=models.CASCADE,
		related_name="searches",
		null=True,
		blank=True,
	)
	keyword = models.CharField(max_length=255)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return self.keyword


class Rating(models.Model):
	ITEM_TYPE_LAPTOP = "laptop"
	ITEM_TYPE_MOBILE = "mobile"
	ITEM_TYPE_CHOICES = (
		(ITEM_TYPE_LAPTOP, "Laptop"),
		(ITEM_TYPE_MOBILE, "Mobile"),
	)

	user = models.ForeignKey(
		UserAccount,
		on_delete=models.CASCADE,
		related_name="ratings",
	)
	item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
	item_id = models.IntegerField()
	score = models.PositiveSmallIntegerField()
	review = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["user", "item_type", "item_id"],
				name="unique_rating_per_user_product",
			),
			models.CheckConstraint(
				check=models.Q(score__gte=1) & models.Q(score__lte=5),
				name="rating_score_between_1_and_5",
			),
		]

	def __str__(self) -> str:
		return f"{self.user_id}-{self.item_type}:{self.item_id}={self.score}"


class UserActivity(models.Model):
	ACTION_VIEW_PRODUCT = "VIEW_PRODUCT"
	ACTION_ADD_TO_CART = "ADD_TO_CART"
	ACTION_RATE_PRODUCT = "RATE_PRODUCT"
	ACTION_CHOICES = (
		(ACTION_VIEW_PRODUCT, "View Product"),
		(ACTION_ADD_TO_CART, "Add To Cart"),
		(ACTION_RATE_PRODUCT, "Rate Product"),
	)

	user = models.ForeignKey(
		UserAccount,
		on_delete=models.CASCADE,
		related_name="activities",
	)
	action = models.CharField(max_length=30, choices=ACTION_CHOICES)
	item_type = models.CharField(max_length=20, blank=True)
	item_id = models.IntegerField(null=True, blank=True)
	quantity = models.PositiveIntegerField(default=0)
	rating_score = models.PositiveSmallIntegerField(null=True, blank=True)
	metadata = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"{self.user_id}:{self.action}"
