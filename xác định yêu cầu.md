Hệ thống ecommerce
Gợi ý API endpoint mẫu cho từng service mới.
Hướng dẫn tích hợp các service này vào hệ thống hiện tại
User Domain
    │
    ├── Auth Service:xác thực đăng nhập
    ├── User Service: quản lý thông tin user
    ├── Role Service: phân quyền
    └── Address Service: quản lý địa chỉ
Product Domain
   |
   |---- Product Service : quản lý sản phẩm
   |---- Category Service : quản lý danh mục
   |---- Attribute Service : thuộc tính sản phẩm
   |---- Inventory Service : tồn kho
   |---- Search Service : tìm kiếm
Commerce Domain
    │
    ├── Cart Service
    ├── Order Service
    ├── Payment Service
    ├── Shipment Service
    ├── Review Service
    └── Recommendation Service

Database:
Auth Service Database - auth_Service_db
    Account
    ---------
    id (PK)
    email
    password_hash
    user_id
    status
    created_at
    updated_at
    RefreshToken
    -------------
    id (PK)
    account_id
    token
    expired_at
    created_at
User Service Database - user_service_db
    User
    ------
    id (PK)
    first_name
    last_name
    phone
    gender
    date_of_birth
    avatar_url
    status
    created_at
    updated_at

    UserProfile
    ------------
    id (PK)
    user_id
    bio
    website
    created_a

Role Service Database
    Role
    ------
    id (PK)
    name
    description
    created_at

    Permission
    -----------
    id (PK)
    name
    description
        
    RolePermission
    ---------------
    role_id
    permission_id

    UserRole
    ---------
    user_id
    role_id
    assigned_at

Address Service Database - : address_service_db
    Address
    ---------
    id (PK)
    user_id
    receiver_name
    phone
    street
    city
    district
    ward
    postal_code
    is_default
    created_at
    updated_at

Category Service Database - category_service_db
    Category - 
    ---------
    id (PK)
    name
    description
    parent_id
    status
    created_at
    updated_at
Product Service Database-product_service_db
    Product 
    ---------
    id (PK)
    name
    description
    category_id
    brand
    base_price
    status
    created_at
    updated_at

    ProductVariant
    ---------------
    id (PK)
    product_id
    sku
    price
    status
    created_at
Attribute Service Database - attribute_service_db
    Attribute
    ----------
    id (PK)
    name
    data_type
    unit
    created_at

    CategoryAttribute
    ------------------
    id (PK)
    category_id
    attribute_id
    is_required
    display_order

    ProductAttributeValue
    ----------------------
    id (PK)
    product_id
    attribute_id
    value

Inventory Service Database - inventory_service_db
    Inventory
    ----------
    id (PK)
    variant_id
    quantity
    reserved_quantity
    updated_at

    StockTransaction
    ----------------
    id (PK)
    variant_id
    change_quantity
    type
    created_at

Cart Service Database - cart__service_db
    Cart
    ------
    id (PK)
    user_id
    created_at
    updated_at
    status

    CartItem
    ---------
    id (PK)
    cart_id
    product_id
    variant_id
    quantity
    price
    added_at

Order Service Database - order_service_db
    Order
    -------
    id (PK)
    user_id
    total_amount
    status(PENDING,CONFIRMED,SHIPPING,DELIVERED,CANCELLED)
    payment_status(UNPAID,PAID,REFUNDED)
    created_at
    updated_at

    OrderItem
    ----------
    id (PK)
    order_id
    product_id
    variant_id
    product_name
    price
    quantity
    subtotal

    OrderHistory
    --------------
    id (PK)
    order_id
    status
    changed_at
Payment Service Database - payment_service_db
    Payment
    --------
    id (PK)
    order_id
    payment_method
    amount
    status(PENDING,SUCCESS,FAILED,REFUNDED)
    created_at
    updated_at

    PaymentTransaction
    -------------------
    id (PK)
    payment_id
    transaction_code
    gateway
    amount
    status
    created_at

    Shipment Service Database -shipment_service_db
    Shipment
    ---------
    id (PK)
    order_id
    carrier
    tracking_number
    status
    shipped_at
    delivered_at
    created_at
    
    ShipmentAddress
    ----------------
    id (PK)
    shipment_id
    receiver_name
    phone
    street
    city
    district
    ward
    postal_code

Review Service Database - review_service_db

    Review
    -------
    id (PK)
    product_id
    user_id
    rating
    comment
    created_at
    updated_at

    ReviewImage
    ------------
    id (PK)
    review_id
    image_url

Recommendation Service Database - recommendation_service_db
    UserBehavior
    --------------
    id (PK)
    user_id
    product_id
    action_type(VIEW,ADD_TO_CART,PURCHASE)
    created_at

    Recommendation
    ---------------
    id (PK)
    user_id
    product_id
    score
    generated_at