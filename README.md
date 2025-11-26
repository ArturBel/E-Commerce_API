# E-Commerce API

## Description
Demo Version of RESTful E-Commerce API with Stripe integration for payment, built with Django and managed via PostgreSQL.

⚠️ **Note**: This project is under active development and may not be stable or feature-complete.

---
## Project structure
```
E-Commerce_API/
├── cart/                   # module for user's cart
├── ecommerce_api/
|   ├── __init__.py
|   ├── asgi.py             # asgi configuration
|   ├── settings.py         # settings of project
|   ├── urls.py             # project's urls
|   └── wsgi.py             # wsgi configuration
├── orders/                 # module for orders and checkout
├── products/               # module for adding and browsing products
├── users/                  # module for user authorization
├── .env                    # secrets are stored here
├── .env.example            # example of how .env should look like
├── .gitignore              # ignored files
├── manage.py               # command line utility
├── requirements.txt        # project requirements
└── README.md               # readme file
```

---
## Main features
- Authorization via JWT tokens
- StripeAPI integration for payment
- Modular structure for scalability
---
## Installation
1) Clone the repository:
```
> git clone https://github.com/ArturBel/E-Commerce_API.git
> cd E-Commerce_API
```

2) Create and activate virtual environment:
```
> python -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
```

3) Create database in Postgres for storage and apply migration.
```
psql> CREATE DATABASE ecommerce OWNER postgres;
> python -m manage.py migrate                           
```

4) Get Stripe's secret keys. Public and Secret keys can be found in your Dashboard. To get Webhook secret, use Stripe CLI:
```
> stripe listen --forward-to localhost:8000/orders/stripe/webhook/
```

5) Create .env file to store secrets, paste there example file and add real values:
```
SECRET_KEY=django-insecure-key
DEBUG=False
DATABASE_NAME=e_commerce_api
DATABASE_USER=postgres
DATABASE_PASSWORD=db_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
STRIPE_PUBLIC_KEY=pk_live_123
STRIPE_SECRET_KEY=sk_live_123
STRIPE_WEBHOOK_SECRET=whsec_123
```

4) Run:
```
> python manage.py runserver
```

---
## Documentation

### Authorization
Register using the 'POST' method:
```
POST /auth/register/
{
	"first_name": "Name",
	"last_name": "Surname",
	"username": "User",
	"email": "user@email.com",
	"password": "password"
}
```

The endpoint should validate the request body and return a `201 Created` status code with newly created user's info and  JWT tokens in JSON format.


After that, login using the 'POST' method:
```
POST auth/login/
{
	"email": "user@email.com",
	"password": "password"
}
```

The following response with `200 OK` status is expected:
```
{
	"msg": "Login successful. Welcome, User!",
	"tokens": {
		"access": "access_token",
		"refresh": "refresh_token"
	}
}
```


In order to edit account details, the following response is used with first name as example:
```
POST auth/edit/   Bearer {your_access_token}
{
	"first_name": "John"
}
```


Users can reset their password via following endpoint:
```
POST /auth/password/
{
	"old_password": "password",
	"new_password": "12345"
}
```

### CRUD operations for product

**For all CRUD operations bearer token is required.**
#### Post a new product
To post a new product, 'POST' method is used:
```
POST /products/post/
{
	"name": "Notebook A4 240 pages",
	"description": "Stylish notebook of 240 A4 pages for sketching",
	"price": "1.5"
}
```

#### Edit product's details
To edit product's information, 'PUT' method and product's id are used:
```
PUT products/product/{int: id}
{
	"stock": 15,
	"price": 1.49
}
```

#### Delete product
To delete product from the database, use 'DELETE' method and product's id:
```
DELETE /products/product/{int: id}
```

#### Getting a product or products
To list all available product, follow this endpoint:
```
GET /products/all/
```


To list all product that authorized user has posted, follow this endpoint:
```
GET /products/my/
```


To get information about specific product, 'GET' method and product's id are used:
```
GET /products/product/{int: id}
```

### Shopping
To add item (product) to the cart, use the following endpoint with item's id and optionally desired quantity:
```
POST /cart/add/{int: id}
{
	"quantity": 2  # default=1
}
```
If quantity is not specified, it will be set to 1 by default.


To edit quantity of added product, use the following endpoint with item's id and specifying quantity:
```
PUT /cart/add/{int: id}
{
	"quantity": 2
}
```


To get user's cart, use 'GET' method:
```
GET /cart/
```


To delete item from the cart, use 'DELETE' method and item's id:
```
DELETE /cart/add/{int: id}
```

### Checkout
To checkout one's cart, the following endpoint is used:
```
POST /orders/checkout
```
New order will be created and its id displayed.


To check order's info, the following endpoint and order's id are used:
```
GET /orders/{int: id}
```


To create payment intent and proceed further with payment, the following endpoint and order's id are used:
```
POST /orders/{int: id}/payment/
```
After payment was made and confirmed, Stripe's dashboard will be updated.

---

## Roadmap
The list of features that are scheduled for the future updates and are actively developed:
- Rate limiting
- Testing scripts
- Admin panel
- Notification service
- Caching
- Advanced product catalog
- Docker & Docker Compose
- CI/CD Pipeline

---
 
## Author

Artur Belotserkovskiy
- Github: https://github.com/ArturBel
- LinkedIn: https://www.linkedin.com/in/artur-belotserkovskiy-346135274/

