from django import forms
from django.contrib import admin
from .models import Book, Category, Electronics, Fashion, Product


class ProductForm(forms.ModelForm):
	"""Custom form to manage product type and category with validation"""
	
	class Meta:
		model = Product
		fields = ('name', 'image_url', 'price', 'stock', 'category', 'product_type')
	
	def clean(self):
		cleaned_data = super().clean()
		category = cleaned_data.get('category')
		product_type = cleaned_data.get('product_type')
		
		# Validate category matches product_type
		if category and product_type and category.product_type != product_type:
			raise forms.ValidationError(
				f"Product type '{product_type}' does not match category type '{category.product_type}'. "
				f"Please select a category with matching product type."
			)
		
		if not product_type:
			raise forms.ValidationError("Product type is required.")
		
		return cleaned_data
	
	def save(self, commit=True):
		# Ensure product_type matches category's product_type
		instance = super().save(commit=False)
		if instance.category and instance.category.product_type:
			instance.product_type = instance.category.product_type
		if commit:
			instance.save()
		return instance


class BookInline(admin.StackedInline):
	model = Book
	can_delete = False
	verbose_name = 'Book details'
	fk_name = 'product'
	max_num = 1


class ElectronicsInline(admin.StackedInline):
	model = Electronics
	can_delete = False
	verbose_name = 'Electronics details'
	fk_name = 'product'
	max_num = 1


class FashionInline(admin.StackedInline):
	model = Fashion
	can_delete = False
	verbose_name = 'Fashion details'
	fk_name = 'product'
	max_num = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	form = ProductForm
	list_display = ('id', 'name', 'product_type', 'price', 'stock', 'subtype_summary', 'category')
	list_filter = ('product_type', 'category')
	search_fields = ('name',)
	inlines = (BookInline, ElectronicsInline, FashionInline)
	fieldsets = (
		('Basic Information', {
			'fields': ('name', 'image_url', 'price', 'stock')
		}),
		('Category & Type', {
			'fields': ('category', 'product_type'),
			'description': 'Product type is automatically determined by the selected category.'
		}),
	)

	def subtype_summary(self, obj):
		if obj.product_type == Product.PRODUCT_TYPE_BOOK and hasattr(obj, 'book'):
			return f"Book: {obj.book.author}"
		if obj.product_type == Product.PRODUCT_TYPE_ELECTRONICS and hasattr(obj, 'electronics'):
			return f"Electronics: {obj.electronics.brand or obj.electronics.model_name}"
		if obj.product_type == Product.PRODUCT_TYPE_FASHION and hasattr(obj, 'fashion'):
			return f"Fashion: {obj.fashion.brand} {obj.fashion.size}"
		return '-'

	subtype_summary.short_description = 'Subtype'

	def get_inline_instances(self, request, obj=None):
		# Only show the inline that matches product_type when editing an existing product.
		inlines = []
		for inline in super().get_inline_instances(request, obj):
			inlines.append(inline)
		if obj is not None:
			# Filter to only include the matching inline
			if obj.product_type == Product.PRODUCT_TYPE_BOOK:
				return [i for i in inlines if isinstance(i, BookInline)]
			if obj.product_type == Product.PRODUCT_TYPE_ELECTRONICS:
				return [i for i in inlines if isinstance(i, ElectronicsInline)]
			if obj.product_type == Product.PRODUCT_TYPE_FASHION:
				return [i for i in inlines if isinstance(i, FashionInline)]
		return inlines


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'product_type', 'parent')
	search_fields = ('name',)


admin.site.register(Book)
admin.site.register(Electronics)
admin.site.register(Fashion)
