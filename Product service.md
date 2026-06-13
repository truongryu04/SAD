# 📦 Product Service Design (Django - Category Tree + Subtype)

---

## 1. Overview

This service manages products in an ecommerce system.

### Key Design Patterns:

* **Domain-Driven Design (DDD)**
* **Table-per-Type (TPT)**
* **Category Tree (Hierarchical Category)**
* **Composition (OneToOneField, NOT inheritance)**

---

## 2. Product Domains

System supports 3 main domains:

| Domain      | Examples                     |
| ----------- | ---------------------------- |
| Book        | textbook, novel              |
| Electronics | mobile, laptop, refrigerator |
| Fashion     | clothes, shoes               |

---

## 3. Architecture Rules (MANDATORY)

The code generator MUST follow:

1. `Product` is the **Aggregate Root**
2. `Category` supports **parent-child hierarchy**
3. Subtypes (`Book`, `Electronics`, `Fashion`):

   * Must be separate tables
   * Must use `OneToOneField`
4. DO NOT use Django model inheritance
5. DO NOT merge subtype fields into Product
6. Each Product MUST belong to ONE Category
7. Category MUST be created before Product
8. Use `product_type` to determine subtype
9. Validate:

   * Category must match Product Type

---

## 4. Data Model

---

### 4.1 Category (Tree Structure)

```python
class Category(models.Model):
    name = models.CharField(max_length=100)

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children'
    )

    PRODUCT_TYPE_CHOICES = [
        ('BOOK', 'Book'),
        ('ELECTRONICS', 'Electronics'),
        ('FASHION', 'Fashion'),
    ]

    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
```

---

### 4.2 Product (Base Model)

```python
class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()
    stock = models.IntegerField()

    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    product_type = models.CharField(max_length=20)
```

---

### 4.3 Book

```python
class Book(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='book'
    )
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20)
```

---

### 4.4 Electronics

```python
class Electronics(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='electronics'
    )
    brand = models.CharField(max_length=100)
    warranty = models.IntegerField()
```

---

### 4.5 Fashion

```python
class Fashion(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='fashion'
    )
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=50)
```

---

## 5. Category Management

### 5.1 Create Category

```http
POST /categories/
```

### Example:

```json
{
  "name": "Electronics",
  "product_type": "ELECTRONICS",
  "parent": null
}
```

---

### 5.2 Create Subcategory

```json
{
  "name": "Laptop",
  "product_type": "ELECTRONICS",
  "parent": 1
}
```

---

### Category Tree Example

```text
Electronics
   ├── Laptop
   ├── Mobile

Fashion
   ├── Men
   ├── Women
```

---

## 6. Product Creation Flow

### API

```http
POST /products/
```

---

### Step-by-step Logic

1. Validate Category exists
2. Validate:

   * `category.product_type == product_type`
3. Create Product
4. Create subtype based on `product_type`

---

### Example Input

```json
{
  "name": "MacBook Pro",
  "price": 3000,
  "stock": 5,
  "category_id": 2,
  "product_type": "ELECTRONICS",
  "brand": "Apple",
  "warranty": 12
}
```

---

### Expected Behavior

* Create Product
* Create Electronics
* Link via OneToOne
* Return full data

---

## 7. Query Logic

### 7.1 Get Products

```http
GET /products/
```

Supports:

* Filter by category
* Filter by product_type
* Search by name
* Pagination

---

### 7.2 Get Products by Category (Include Subcategories)

```http
GET /categories/{id}/products/
```

### Logic:

* Get selected category
* Get all children categories
* Query products with:

```python
Product.objects.filter(category__in=all_subcategories)
```

---

## 8. Query Optimization

MUST use:

```python
Product.objects.select_related(
    'book',
    'electronics',
    'fashion'
)
```

---

## 9. Response Format

```json
{
  "id": 1,
  "name": "MacBook Pro",
  "product_type": "ELECTRONICS",
  "electronics": {
    "brand": "Apple",
    "warranty": 12
  }
}
```

---

## 10. Error Handling

| Case                 | Response |
| -------------------- | -------- |
| Category not found   | 404      |
| Invalid product_type | 400      |
| Category mismatch    | 400      |
| Missing subtype data | 400      |

---

## 11. Constraints (CRITICAL)

The AI MUST NOT:

* ❌ Use Django inheritance
* ❌ Store all fields in Product
* ❌ Skip subtype creation
* ❌ Allow mismatched category & product_type
* ❌ Create Product without Category

---

## 12. Summary

This design provides:

* Scalable product system
* Clear domain separation
* Flexible category hierarchy
* Clean database structure

### Patterns Used:

* Table-per-Type
* Aggregate Root
* Category Tree
* Composition

---
