# Flask eCommerce Application

This is a simple eCommerce web application built using Flask. The application supports two user types: Admin and Customer. Admins can log in to manage products, while customers can browse products and make purchases.

## Features

- Product image slider on the front page
- Top products section
- Admin dashboard for managing products and viewing statistics
- Customer cart management
- Checkout process with cash on delivery and Bkash payment options
- SQLite database for data storage
- Modern, minimal frontend using Tailwind CSS

## Project Structure

```
flask-ecommerce-app
├── app
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── forms.py
│   ├── static
│   │   ├── css
│   │   │   └── tailwind.css
│   │   └── js
│   │       └── slider.js
│   ├── templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── product_slider.html
│   │   ├── top_products.html
│   │   ├── login.html
│   │   ├── admin_dashboard.html
│   │   ├── upload_product.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   └── payment_form.html
│   └── utils.py
├── instance
│   └── app.db
├── requirements.txt
├── config.py
├── run.py
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd flask-ecommerce-app
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   - The application uses SQLite, and the database file will be created automatically in the `instance` directory.

## Running the Application

To run the application, execute the following command:
```
python run.py
```

The application will be accessible at `http://127.0.0.1:5000`.

## Usage

- **Admin Login**: Access the admin login page to manage products.
- **Product Management**: Admins can upload new products and view product visit statistics.
- **Customer Shopping**: Customers can browse products, add them to their cart, and proceed to checkout.
- **Payment Options**: Choose between cash on delivery or Bkash payment methods during checkout.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License.