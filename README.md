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

## Deployment / Push to GitHub and DigitalOcean App Platform

These steps assume you have a GitHub repository and want to deploy the `flask-ecommerce-app` to DigitalOcean App Platform.

1. Prepare your local repo
   - Make sure you have a clean working tree and commit all changes:
     ```powershell
     git add .
     git commit -m "Prepare app for deployment: add Procfile, env example, SEO fixes"
     git push origin main
     ```

2. Environment variables
   - Copy `.env.example` to `.env` for local testing and fill real values.
   - Never commit `.env` to git. Use DigitalOcean App Secrets (or GitHub Secrets for CI) to store production environment variables.

3. Create a GitHub repository and push
   - Create a new repo on GitHub and push your local repo there. Then link the GitHub repo from DigitalOcean.

4. Deploy on DigitalOcean App Platform
   - In the DigitalOcean Control Panel, choose Apps > Create App and connect your GitHub repository.
   - Select the `flask-ecommerce-app` directory as the app source (if you pushed the whole mono-repo, point to that subfolder).
   - Set the build command (usually none; DigitalOcean will detect Python). Ensure `requirements.txt` is present.
   - Set the run command to use Gunicorn (Procfile will be respected):
     `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 3`
   - Add environment variables (SECRET_KEY, DATABASE_URL, BREVO_API_KEY, etc.) in the App Settings -> Components -> Environment Variables.

5. Database
   - For production, use a managed database (Postgres) and set `DATABASE_URL` accordingly. If you keep SQLite, know disk is ephemeral or use persistent volume.

6. Storage
   - For user-uploaded images, use S3 or Spaces (DigitalOcean Spaces) and update `UPLOAD_FOLDER` or integrate S3 in `utils.py`.

7. After deploy
   - Run database migrations on the production DB (via DO console/SSH or a one-off deploy command):
     ```powershell
     flask db upgrade
     ```
   - Visit your app URL and verify pages, sitemap, and robots.

8. Security & secrets
   - Use DigitalOcean App Secrets to store API keys, DB credentials, and never store them in Git.
   - For local development, use `.env` and `python-dotenv` (already used in `run.py`).

If you want, I can prepare a ready-to-push checklist and a small `deploy.md` with exact UI steps and screenshots tailored to DigitalOcean.

## Pinning runtime dependencies (generate requirements.txt)

To ensure production uses the exact same Python packages as your running environment, pin the active virtualenv packages to `requirements.txt` before pushing/deploying. A helper script is provided:

- `scripts/pin_requirements.py` — Python script that runs `pip freeze` using the same interpreter and writes `requirements.txt` (creates a `requirements.txt.bak` backup).
- `scripts/pin_requirements.sh` — Bash wrapper to run `pip freeze` (for Linux/macOS servers).
- `scripts/pin_requirements.ps1` — PowerShell helper for Windows.

Usage example (on your server where the app venv is active):

Linux/macOS (bash):
```bash
cd /home/sobuy/sobuy-app
source venv/bin/activate
python scripts/pin_requirements.py
# review requirements.txt, then commit
git add requirements.txt && git commit -m "chore: pin requirements"
```

Windows PowerShell:
```powershell
Set-Location C:\path\to\flask-ecommerce-app
. .\.venv\Scripts\Activate.ps1
python .\scripts\pin_requirements.py
# review and commit
git add requirements.txt; git commit -m "chore: pin requirements"
```

Do not commit secrets or `.env` files. After pinning, run your deployment steps so the build installs the same packages.