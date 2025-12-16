# SHA (Social Health Authority) System

A comprehensive Django-based management system for Kenya's Social Health Authority (SHA), replacing the former NHIF system. This system manages member registration, contributions, healthcare provider networks, claims processing, and payments.

## 👨‍💻 Developer Information

**Developer:** Steve Ongera  
**Email:** steveongera001@gmail.com  
**Phone:** 0112284093  
**Project Type:** Healthcare Management System  
**Technology:** Django + Python

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [User Roles](#user-roles)
- [Key Modules](#key-modules)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

The SHA System is a role-based healthcare management platform that digitizes and automates Kenya's Social Health Authority operations. The system handles:

- **Member Registration & Management** - Principal members and dependents
- **Employer Integration** - Company registration and salary deductions
- **Contribution Tracking** - Monthly contributions at 2.75% of gross salary
- **Healthcare Provider Network** - Facility registration and contract management
- **Benefit Packages** - SHIF, PHCF, and ECCIF coverage
- **Pre-Authorization** - Request and approval workflow for procedures
- **Claims Processing** - Submission, review, approval, and payment
- **Payment Processing** - Direct payments to healthcare providers
- **Eligibility Verification** - Real-time member eligibility checks
- **Reporting & Analytics** - Comprehensive system reports

---

## ✨ Features

### Core Features

- ✅ Role-Based Access Control (7 user roles)
- ✅ Member registration with SHA number generation
- ✅ Employer management and salary deduction tracking
- ✅ Multiple payment methods (M-Pesa, Bank Transfer, USSD)
- ✅ Healthcare provider network management
- ✅ Three-tier benefit packages (SHIF, PHCF, ECCIF)
- ✅ Pre-authorization workflow for specialized procedures
- ✅ Multi-stage claims processing
- ✅ Automated payment processing
- ✅ Eligibility verification system
- ✅ Comprehensive audit logging
- ✅ Notification system
- ✅ Report generation

### Administrative Features

- 📊 Dashboard with analytics
- 🔍 Advanced search and filtering
- 📈 Financial reporting
- 🏥 Provider performance tracking
- 👥 Member enrollment statistics
- 💰 Contribution and claims summaries

---

## 💻 System Requirements

### Prerequisites

- **Python:** 3.9 or higher
- **Django:** 4.2 or higher
- **Database:** PostgreSQL 13+ (recommended) or MySQL 8+
- **OS:** Linux, macOS, or Windows
- **Memory:** Minimum 4GB RAM
- **Storage:** Minimum 10GB available space

### Python Packages

```
Django==4.2.0
djangorestframework==3.14.0
psycopg2-binary==2.9.6
Pillow==10.0.0
django-filter==23.2
django-cors-headers==4.0.0
celery==5.3.0
redis==4.5.5
python-decouple==3.8
gunicorn==20.1.0
whitenoise==6.4.0
```

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/sha-system.git
cd sha-system
```

### Step 2: Create Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create Environment File

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=sha_db
DB_USER=sha_user
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# M-Pesa Integration (for payments)
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback/

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# File Upload Settings
MEDIA_ROOT=media/
MEDIA_URL=/media/
```

---

## 🗄️ Database Setup

### PostgreSQL Setup

```bash
# Login to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE sha_db;
CREATE USER sha_user WITH PASSWORD 'your_password_here';
ALTER ROLE sha_user SET client_encoding TO 'utf8';
ALTER ROLE sha_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE sha_user SET timezone TO 'Africa/Nairobi';
GRANT ALL PRIVILEGES ON DATABASE sha_db TO sha_user;
\q
```

### Run Migrations

```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Create Superuser

```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### Load Initial Data (Optional)

```bash
# Load sample benefit packages
python manage.py loaddata fixtures/benefit_packages.json

# Load sample services
python manage.py loaddata fixtures/benefit_services.json
```

---

## ⚙️ Configuration

### settings.py Configuration

Update your `settings.py`:

```python
# SHA System specific settings
SHA_CONTRIBUTION_RATE = 2.75  # Percentage
SHA_MINIMUM_CONTRIBUTION = 300  # KES

# Upload settings
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# File size limits
MAX_UPLOAD_SIZE = 5242880  # 5MB

# Session settings
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True

# Pagination
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

---

## 🏃 Running the Application

### Development Server

```bash
# Run Django development server
python manage.py runserver

# Access admin panel
# http://localhost:8000/admin/

# Access API
# http://localhost:8000/api/
```

### Run Celery (Background Tasks)

```bash
# Terminal 1 - Start Redis
redis-server

# Terminal 2 - Start Celery Worker
celery -A sha_system worker --loglevel=info

# Terminal 3 - Start Celery Beat (Scheduled Tasks)
celery -A sha_system beat --loglevel=info
```

### Collect Static Files (Production)

```bash
python manage.py collectstatic --noinput
```

---

## 👥 User Roles

The system supports seven distinct roles:

| Role | Description | Key Permissions |
|------|-------------|----------------|
| **ADMIN** | System Administrator | Full system access, user management |
| **SHA_OFFICER** | SHA Government Officer | Member management, policy oversight |
| **EMPLOYER** | Employer/Company | Employee registration, contribution submissions |
| **PROVIDER** | Healthcare Provider | Claim submission, eligibility checks |
| **MEMBER** | Member/Contributor | View contributions, view claims |
| **CLAIMS_OFFICER** | Claims Processing Officer | Review and approve/reject claims |
| **FINANCE_OFFICER** | Finance Officer | Payment processing, financial reports |

---

## 📦 Key Modules

### 1. Member Management

**Models:** `Member`

- Principal and dependent member registration
- SHA number auto-generation (Format: SHA/YYYY/XXXXXX)
- Employment status tracking
- County-based registration
- Government subsidy eligibility

### 2. Employer Management

**Models:** `Employer`

- Company registration with KRA PIN
- Employer code generation (Format: EMP/XXXXXX)
- Bank details for remittance
- Employee roster management

### 3. Contribution Management

**Models:** `Contribution`

- Monthly contribution tracking
- 2.75% salary deduction calculation
- Multiple payment methods
- Transaction reference tracking
- Payment status management

### 4. Healthcare Provider Network

**Models:** `HealthcareProvider`

- 6-level facility classification
- Public, private, and faith-based facilities
- License and contract management
- Facility code generation (Format: FAC/XXXXXX)

### 5. Benefit Packages

**Models:** `BenefitPackage`, `BenefitService`

- SHIF (Social Health Insurance Fund)
- PHCF (Primary Healthcare Fund)
- ECCIF (Emergency, Chronic & Critical Illness Fund)
- Service-level tariffs and co-payments
- Frequency and coverage limits

### 6. Pre-Authorization

**Models:** `PreAuthorization`

- Request submission by healthcare providers
- SHA officer review and approval
- Authorization number generation (Format: AUTH/YYYY/XXXXXX)
- Validity period tracking
- Document management

### 7. Claims Processing

**Models:** `Claim`, `ClaimItem`

- Outpatient, inpatient, and emergency claims
- Claim number generation (Format: CLM/YYYY/XXXXXX)
- Multi-stage workflow: Submitted → Under Review → Approved/Rejected → Paid
- ICD-10 diagnosis coding
- Item-level claim details
- Supporting document management

### 8. Payment Processing

**Models:** `Payment`

- Direct payments to healthcare providers
- Payment reference generation (Format: PAY/YYYY/XXXXXX)
- Bank transfer tracking
- Payment status management
- Transaction reconciliation

### 9. Eligibility Verification

**Models:** `EligibilityCheck`

- Real-time member eligibility verification
- Contribution status checking
- Provider access control
- Audit trail

### 10. Audit & Compliance

**Models:** `AuditLog`

- Comprehensive audit trail
- User action tracking
- IP address logging
- Change history

---

## 🔌 API Endpoints

### Authentication

```
POST   /api/auth/login/           # User login
POST   /api/auth/logout/          # User logout
POST   /api/auth/register/        # User registration
```

### Members

```
GET    /api/members/              # List all members
POST   /api/members/              # Create new member
GET    /api/members/{id}/         # Get member details
PUT    /api/members/{id}/         # Update member
DELETE /api/members/{id}/         # Delete member
GET    /api/members/{id}/dependents/  # Get member dependents
```

### Contributions

```
GET    /api/contributions/        # List contributions
POST   /api/contributions/        # Submit contribution
GET    /api/contributions/{id}/   # Get contribution details
GET    /api/contributions/member/{member_id}/  # Get member contributions
```

### Claims

```
GET    /api/claims/               # List all claims
POST   /api/claims/               # Submit new claim
GET    /api/claims/{id}/          # Get claim details
PUT    /api/claims/{id}/          # Update claim
POST   /api/claims/{id}/approve/  # Approve claim
POST   /api/claims/{id}/reject/   # Reject claim
```

### Pre-Authorizations

```
GET    /api/preauthorizations/    # List pre-authorizations
POST   /api/preauthorizations/    # Submit pre-auth request
GET    /api/preauthorizations/{id}/  # Get pre-auth details
POST   /api/preauthorizations/{id}/approve/  # Approve pre-auth
POST   /api/preauthorizations/{id}/reject/   # Reject pre-auth
```

### Eligibility

```
POST   /api/eligibility/check/    # Check member eligibility
GET    /api/eligibility/history/{member_id}/  # Get eligibility history
```

### Payments

```
GET    /api/payments/             # List all payments
POST   /api/payments/             # Process payment
GET    /api/payments/{id}/        # Get payment details
```

### Reports

```
GET    /api/reports/              # List available reports
POST   /api/reports/generate/     # Generate report
GET    /api/reports/{id}/download/  # Download report
```

---

## 🧪 Testing

### Run Unit Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test sha.tests

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Data

```bash
# Create test data
python manage.py shell
>>> from django.core.management import call_command
>>> call_command('loaddata', 'fixtures/test_data.json')
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure production database
- [ ] Set up Redis for caching
- [ ] Configure Celery for background tasks
- [ ] Set up email service (SMTP)
- [ ] Configure file storage (AWS S3/Azure Blob)
- [ ] Set up monitoring (Sentry)
- [ ] Configure backup strategy
- [ ] Set up firewall rules
- [ ] Enable rate limiting

### Deploy with Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn sha_system.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/sha-system/staticfiles/;
    }

    location /media/ {
        alias /path/to/sha-system/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Docker Deployment

```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "sha_system.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

## 📊 Database Schema Overview

```
Users (Authentication & Roles)
  ├── Members (Principal & Dependents)
  │     ├── Contributions
  │     ├── Claims
  │     ├── Pre-Authorizations
  │     └── Eligibility Checks
  │
  ├── Employers
  │     ├── Members (Employees)
  │     └── Contributions
  │
  └── Healthcare Providers
        ├── Claims
        ├── Pre-Authorizations
        ├── Payments
        └── Eligibility Checks

Benefit Packages
  └── Benefit Services
        ├── Claims Items
        └── Pre-Authorizations

Payments
  └── Claims

Audit Logs (All Activities)
Notifications (User Alerts)
Reports (System Reports)
```

---

## 🔐 Security Considerations

1. **Authentication:** Django's built-in authentication with token support
2. **Authorization:** Role-based access control on all endpoints
3. **Data Encryption:** Use HTTPS in production
4. **Sensitive Data:** Encrypt sensitive fields (bank details, medical records)
5. **Audit Trail:** Comprehensive logging of all actions
6. **Rate Limiting:** Implement API rate limiting
7. **Input Validation:** Strict validation on all user inputs
8. **File Uploads:** Validate file types and sizes
9. **SQL Injection:** Use Django ORM (parameterized queries)
10. **CSRF Protection:** Enabled by default in Django

---

## 📝 Important Notes

### SHA Number Format
- Format: `SHA/YYYY/XXXXXX`
- Example: `SHA/2024/000001`
- Auto-generated on member registration

### Contribution Calculation
- Rate: 2.75% of gross salary
- Minimum: KES 300 per month
- Payment methods: Salary Deduction, M-Pesa, Bank Transfer, USSD

### Claim Processing Workflow
1. **Submitted** - Provider submits claim
2. **Under Review** - Claims officer reviews
3. **Queried** - Additional information needed
4. **Approved** - Claim approved for payment
5. **Rejected** - Claim rejected with reason
6. **Paid** - Payment processed to provider

### Benefit Packages
- **SHIF:** Main outpatient and inpatient coverage
- **PHCF:** Primary and community health services
- **ECCIF:** Emergency, chronic, and critical illness care

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide
- Write unit tests for new features
- Update documentation
- Use meaningful commit messages

---

## 📞 Support & Contact

**Developer:** Steve Ongera  
**Email:** steveongera001@gmail.com  
**Phone:** +254 112 284 093

For bug reports and feature requests, please create an issue on GitHub.

---

## 📜 License

This project is proprietary software developed for Kenya's Social Health Authority (SHA).  
All rights reserved © 2024 Steve Ongera

---

## 🙏 Acknowledgments

- Kenya Social Health Authority (SHA) for system requirements
- Django community for the excellent framework
- Contributors and testers

---

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [SHA Official Website](https://sha.go.ke/)
- [Kenya Health System](https://health.go.ke/)

---

**Last Updated:** December 2024  
**Version:** 1.0.0  
**Status:** Production Ready