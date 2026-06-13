from django.db import models, transaction


class Category(models.Model):
    PRODUCT_TYPE_BOOK = 'BOOK'
    PRODUCT_TYPE_ELECTRONICS = 'ELECTRONICS'
    PRODUCT_TYPE_FASHION = 'FASHION'

    PRODUCT_TYPE_CHOICES = [
        (PRODUCT_TYPE_BOOK, 'Book'),
        (PRODUCT_TYPE_ELECTRONICS, 'Electronics'),
        (PRODUCT_TYPE_FASHION, 'Fashion'),
    ]

    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
    )
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.product_type})"


class Product(models.Model):
    PRODUCT_TYPE_BOOK = 'BOOK'
    PRODUCT_TYPE_ELECTRONICS = 'ELECTRONICS'
    PRODUCT_TYPE_FASHION = 'FASHION'

    PRODUCT_TYPE_CHOICES = [
        (PRODUCT_TYPE_BOOK, 'Book'),
        (PRODUCT_TYPE_ELECTRONICS, 'Electronics'),
        (PRODUCT_TYPE_FASHION, 'Fashion'),
    ]

    name = models.CharField(max_length=255)
    image_url = models.URLField(blank=True, default="")
    price = models.FloatField()
    stock = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.product_type})"

    def create_subtype(self, **kwargs):
        """Create the subtype row based on `product_type`.

        Expects subtype-specific fields in kwargs. Uses transaction to ensure atomicity.
        """
        if self.product_type == self.PRODUCT_TYPE_BOOK:
            return Book.objects.create(
                product=self,
                author=kwargs.get('author', ''),
                publisher=kwargs.get('publisher', ''),
                isbn=kwargs.get('isbn', ''),
                publication_date=kwargs.get('publication_date', None),
                language=kwargs.get('language', ''),
            )
        if self.product_type == self.PRODUCT_TYPE_ELECTRONICS:
            return Electronics.objects.create(
                product=self,
                model_name=kwargs.get('model_name', ''),
                brand=kwargs.get('brand', ''),
                warranty=kwargs.get('warranty', 0),
                weight=kwargs.get('weight', 0.0),
                dimensions=kwargs.get('dimensions', ''),
                color=kwargs.get('color', ''),
            )
        if self.product_type == self.PRODUCT_TYPE_FASHION:
            return Fashion.objects.create(
                product=self,
                brand=kwargs.get('brand', ''),
                size=kwargs.get('size', ''),
                color=kwargs.get('color', ''),
                material=kwargs.get('material', ''),
                season=kwargs.get('season', ''),
                gender=kwargs.get('gender', ''),
            )
        raise ValueError('Invalid product_type')

    @classmethod
    def create_with_subtype(cls, *, name, price, stock, category, product_type, image_url="", **subtype_fields):
        with transaction.atomic():
            product = cls.objects.create(
                name=name,
                image_url=image_url or "",
                price=price,
                stock=stock,
                category=category,
                product_type=product_type,
            )
            product.create_subtype(**subtype_fields)
            return product


class Book(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='book')
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20)
    publication_date = models.DateField(null=True, blank=True)
    language = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Book: {self.product.name} by {self.author} ({self.language})"
class Electronics(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='electronics')
    model_name = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    warranty = models.IntegerField(default=0)
    weight = models.FloatField(default=0.0)
    dimensions = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)

    def __str__(self):
        parts = [self.brand or self.model_name]
        return f"Electronics: {self.product.name} ({' - '.join([p for p in parts if p])})"
class Fashion(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='fashion')
    brand = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=10, blank=True)
    color = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    season = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Fashion: {self.product.name} ({self.brand} {self.size})"