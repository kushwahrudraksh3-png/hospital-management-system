# Hospital Management System (HMS)
### Vatsalya Shree Hospital — Enterprise Healthcare ERP & PWA

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0.7-092E20.svg?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-Ready-5A0FC8.svg?logo=pwa&logoColor=white)
![Status](https://img.shields.io/badge/Production-Ready-success)

An enterprise-grade Hospital Management System (HMS) engineered for **Vatsalya Shree Hospital**. This web application digitizes end-to-end clinical and administrative workflows including Patient Registration, Outpatient Department (OPD), Inpatient Department (IPD), Doctor Consultations, Electronic Health Records (EHR), Laboratory Operations, Medical Billing, Financial Analytics, and Super Admin Management.

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. System Features](#2-system-features)
- [3. HMS Workflow Diagram](#3-hms-workflow-diagram)
- [4. Technology Stack](#4-technology-stack)
- [5. Project Structure](#5-project-structure)
- [6. Installation Guide](#6-installation-guide)
- [7. Environment Variables](#7-environment-variables)
- [8. User Roles & Access Matrix](#8-user-roles--access-matrix)
- [9. Application Screenshots](#9-application-screenshots)
- [10. Security Architecture](#10-security-architecture)
- [11. Production Deployment Guide](#11-production-deployment-guide)
- [12. Progressive Web App (PWA) Status](#12-progressive-web-app-pwa-status)
- [13. Future Roadmap](#13-future-roadmap)
- [14. License](#14-license)
- [15. Authors & Credits](#15-authors--credits)

---

## 1. Project Overview

### Purpose & Objectives
The Vatsalya Shree Hospital Management System delivers a unified, real-time platform to streamline healthcare operations, minimize patient wait times, ensure medical record integrity, and prevent revenue leakage.

### Key Objectives
- **Clinical Efficiency**: Seamless transition from Receptionist registration to Doctor queue to Laboratory diagnostics.
- **Role-Based Security**: Multi-tier access control isolating Receptionist, Doctor, Laboratory, and Administrative data boundaries.
- **Robust Financial Tracking**: Automated billing generation for consultations, IPD bed allocations, procedures, and lab investigations.
- **Zero-Downtime Resilience**: Global network status monitor and PWA architecture ensuring data restoration during connection drops.

---

## 2. System Features

###  receptionist Receptionist Module
- **Patient Registration**: New patient onboarding with auto-generated UHID numbers.
- **OPD Queue Management**: Assign patients to available specialty doctors and issue appointment tickets.
- **IPD Admission & Bed Allocation**: Manage bed assignments, ward categories, admission records, and patient transfers.
- **Vitals Recording**: Capture patient height, weight, BP, pulse, temperature, and SpO2.
- **Billing & Receipt Generation**: Generate itemized receipts for OPD visits, IPD deposits, and final discharge settlements.

### 🩺 Doctor Module
- **Live Consultation Queue**: Real-time view of waiting patients with vitals summaries.
- **EHR & Medical History**: Review prior diagnoses, prescription records, and historical lab reports.
- **Prescription Builder**: Fast medical prescription generator supporting dosages, duration, and clinical advice.
- **Lab Investigation Orders**: Directly order laboratory tests during consultations.
- **IPD In-Patient Management**: Monitor admitted patients, daily progress notes, and bed assignments.

### 🔬 Laboratory Module
- **Lab Orders Dashboard**: Live feed of investigation orders received from OPD and IPD departments.
- **Report Result Entry**: Input diagnostic test values, reference ranges, and observations.
- **Report Verification & Printing**: Standardized lab report preview and print generation with hospital branding.
- **Lab Billing & Ledger**: Financial tracking of diagnostic services provided.

### 💳 Billing & Financial Module
- **OPD Consultation Receipts**: Instant receipt printing for initial visits and follow-ups.
- **IPD Itemized Billing**: Daily charge calculations for bed tariffs, nursing, medicines, and surgical procedures.
- **Deposit & Refund Ledger**: Payment receipt tracking for advances and final discharge bill settlements.

### 🛡️ Admin Panel & Analytics
- **Executive Dashboard**: Key Performance Indicators (KPIs) showing daily OPD counts, IPD occupancy, revenue totals, and pending lab tests.
- **IPD & Lab Master Configuration**: Ward rates, bed directories, test tariffs, and department settings.
- **User Management**: Staff account provisioning, password management, and role assignment.
- **Comprehensive Reports**: Financial ledgers, clinical summaries, and date-filtered exports.

### 🔑 Authentication & Account Security
- **Multi-Role Authentication**: Staff login supporting Receptionist, Doctor, Laboratory Technician, and Admin roles.
- **Password Reset & OTP Verification**: Email-based OTP authentication for password recovery.
- **Session Management**: Automated timeout and secure cookie protection.

---

## 3. HMS Workflow Diagram

```
       ┌────────────────────────┐
       │   Patient Arrival      │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Patient Registration   │ (Receptionist)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   OPD / IPD Ticket     │ (Vitals Recorded)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Doctor Consultation    │ (Prescription & EHR)
       └─────┬────────────┬─────┘
             │            │
  (Lab Order)│            │(Treatment Plan)
             ▼            ▼
   ┌──────────────┐  ┌──────────────┐
   │ Lab Module   │  │ IPD Ward     │
   │ (Diagnostics)│  │ (Bed Alloc)  │
   └──────┬───────┘  └──────┬───────┘
          │                 │
          └────────┬────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Billing & Discharge    │ (Receipt Printed)
       └────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.12 | Core backend language |
| **Framework** | Django 6.0.7 | MVC/MVT Web Framework |
| **Database** | PostgreSQL 16 | Relational Enterprise Database |
| **WSGI Server** | Gunicorn 26.0 | Production HTTP Server |
| **Web Server** | Nginx | Reverse Proxy & Static Asset Server |
| **Frontend** | HTML5, CSS3, JS (ES6) | Responsive UI (HMS Light Theme) |
| **CSS Framework** | Bootstrap 5.3.3 | Responsive Layouts & Utilities |
| **Icons** | Bootstrap Icons 1.11.3 | Modern SVG UI Iconography |
| **Environment** | python-decouple 3.8 | Secret Key & Setting Isolation |
| **Image Processing**| Pillow 12.3 | Medical Report & Asset Processing |
| **Excel Export** | openpyxl 3.1 | Financial & Clinical Data Exports |
| **PWA Architecture**| Service Worker + Manifest | Network Detection & Offline Fallback |

---

## 5. Project Structure

```
CMS/
├── accounts/                   # Authentication & User Account Management
│   ├── migrations/             # Database Migrations
│   ├── models.py               # Custom User & Staff Role Models
│   ├── urls.py                 # Auth Routing (Login, Forgot/Reset Password, OTP)
│   └── views.py                # Auth Controller Views
├── receptionist/               # Receptionist & OPD/IPD Registration Module
│   ├── models.py               # Patient Registration, Admissions, Vitals Models
│   ├── urls.py                 # Receptionist Navigation Routes
│   └── views.py                # Registration, Vitals, Billing & Receipt Logic
├── doctor/                     # Doctor Module & Electronic Health Records
│   ├── models.py               # OPD Queue, Prescriptions, History Models
│   ├── urls.py                 # Consultation Routes
│   └── views.py                # Consultation Queue, History & OPD Prescriptions
├── lab/                        # Laboratory Diagnostic Module
│   ├── models.py               # Test Master, Lab Orders, Test Results Models
│   ├── urls.py                 # Laboratory Routes
│   └── views.py                # Lab Dashboard, Result Entry & Report Printing
├── adminpanel/                 # Super Admin Management & Reporting Module
│   ├── models.py               # Master Data Models
│   ├── urls.py                 # Admin Panel Routes
│   └── views.py                # Master Settings, Reports & Staff Management
├── cms/                        # Django Project Core Configuration
│   ├── settings.py             # Global Project Settings & Security Hardening
│   ├── urls.py                 # Master URL Router & Health Check (/ping/)
│   ├── wsgi.py                 # WSGI Entry Point for Gunicorn
│   └── asgi.py                 # Async Entry Point
├── static/                     # Global Static Assets
│   ├── css/                    # Custom Stylesheets (network_handler.css, etc.)
│   ├── js/                     # Client Scripts (network_handler.js, etc.)
│   ├── images/                 # Hospital Logo (vatsalya_child_logo.png)
│   ├── manifest.json           # Web App Manifest for PWA
│   └── service-worker.js       # PWA Service Worker script
├── templates/                  # Modular HTML Templates
│   ├── accounts/               # Auth Layouts & Form Templates
│   ├── receptionist/           # Receptionist Views & Receipts
│   ├── doctor/                 # Doctor Queue & EHR Views
│   ├── lab/                    # Lab Order & Diagnostic Templates
│   ├── adminpanel/             # Master Setup & Report Templates
│   ├── includes/               # Global Network Overlay (`network_handler.html`)
│   └── offline.html            # PWA Offline Fallback Page
├── logs/                       # Server Logs Directory
│   └── django.log              # Error Log Output
├── media/                      # User Uploaded Documents & Media
├── manage.py                   # Django Administrative CLI
├── requirements.txt            # Python Dependencies
└── .env                        # Environment Configuration Variables
```

---

## 6. Installation Guide

### Prerequisites
- Python 3.12+
- PostgreSQL 14+
- Git

### Step-by-Step Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/kushwahrudraksh3-png/hospital-management-system.git
   cd hospital-management-system
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Create a `.env` file in the project root (refer to Section 7).

5. **Execute Database Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create Super Admin Account**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect Static Assets**
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Start Local Development Server**
   ```bash
   python manage.py runserver
   ```
   Access the application at `http://127.0.0.1:8000/`.

---

## 7. Environment Variables

Create a `.env` file in the root directory:

```env
# Django Core
SECRET_KEY=your-production-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# PostgreSQL Database Configuration
DB_NAME=cms_db
DB_USER=cms_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@example.com

# Production Security Switches (Used when DEBUG=False)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
```

---

## 8. User Roles & Access Matrix

| Feature / Module | Super Admin | Receptionist | Doctor | Laboratory |
| :--- | :---: | :---: | :---: | :---: |
| **Patient Registration & Vitals** | ✅ | ✅ | 👁️ (Read Only) | ❌ |
| **OPD / IPD Admissions** | ✅ | ✅ | 👁️ (Read Only) | ❌ |
| **Doctor Queue & EHR** | ✅ | ❌ | ✅ | ❌ |
| **Prescription & Lab Orders** | ✅ | ❌ | ✅ | ❌ |
| **Lab Order Processing & Results** | ✅ | ❌ | 👁️ (Read Only) | ✅ |
| **Billing & Receipts** | ✅ | ✅ | ❌ | 👁️ (Lab Only) |
| **Master Tariff & Bed Setup** | ✅ | ❌ | ❌ | ❌ |
| **User & Staff Management** | ✅ | ❌ | ❌ | ❌ |

---

## 9. Application Screenshots

*(Placeholder sections for UI Screenshots)*

### 1. Login & Staff Portal
![Login Screen](https://via.placeholder.com/800x450.png?text=Login+%26+Authentication+Portal)

### 2. Receptionist OPD & IPD Dashboard
![Receptionist Dashboard](https://via.placeholder.com/800x450.png?text=Receptionist+Dashboard)

### 3. Doctor Consultation & Queue
![Doctor Consultation](https://via.placeholder.com/800x450.png?text=Doctor+Queue+%26+Prescription)

### 4. Laboratory Diagnostic Module
![Lab Module](https://via.placeholder.com/800x450.png?text=Lab+Report+Entry+%26+Printing)

### 5. Medical Billing & Receipts
![Billing Module](https://via.placeholder.com/800x450.png?text=OPD+%26+IPD+Billing+Receipts)

### 6. Admin Panel Analytics
![Admin Panel](https://via.placeholder.com/800x450.png?text=Admin+Panel+Analytics+%26+Reports)

---

## 10. Security Architecture

- **Role-Based Access Control (RBAC)**: Enforced via custom middleware and view decorators ensuring isolation between medical staff roles.
- **CSRF & XSS Protection**: Django `CsrfViewMiddleware` enabled across all forms and AJAX endpoints.
- **Production Hardening**: Conditional enforcement of `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, and `CSRF_COOKIE_SECURE` when `DEBUG=False`.
- **Database Security**: Parameterized ORM queries preventing SQL injection vulnerabilities.
- **Audit Logging**: Error logs written to `logs/django.log` for operational transparency.

---

## 11. Production Deployment Guide

Target Deployment Platform: **Hostinger VPS (Ubuntu 22.04 LTS)**

### Stack Configuration
- **Application Server**: Gunicorn WSGI (`cms.wsgi:application`) managed via `systemd`.
- **Reverse Proxy**: Nginx handling HTTPS termination, static asset compression (`/static/`), and media delivery (`/media/`).
- **Database**: PostgreSQL 16 server with connection pooling (`CONN_MAX_AGE=60`).
- **SSL Certificate**: Certbot Let's Encrypt SSL configuration.

### Deployment Workflow
1. Provision Hostinger Ubuntu VPS and install Nginx & PostgreSQL.
2. Clone repository to `/var/www/cms/` and set `.env` with `DEBUG=False`.
3. Run `python manage.py collectstatic --noinput` and `python manage.py migrate`.
4. Configure systemd unit (`/etc/systemd/system/gunicorn.service`).
5. Configure Nginx site server block (`/etc/nginx/sites-available/cms`).
6. Run `certbot --nginx` to enable HTTPS.

---

## 12. Progressive Web App (PWA) Status

### Already Implemented
- ✅ **Web App Manifest**: `static/manifest.json` configured with standalone display mode and theme colors.
- ✅ **Service Worker**: `static/service-worker.js` active with Network-First caching strategy for dynamic pages and Cache-First for static assets.
- ✅ **Global Network Connection Handler**: Real-time detection for **Case 1 (No Internet)** and **Case 2 (Server Unavailable)**.
- ✅ **Automatic Recovery & Page Restoration**: 10-second automatic ping check returning users to their last active page URL (`localStorage.hms_last_visited_url`).
- ✅ **Offline Fallback Page**: Rendered via `templates/offline.html`.

### Planned PWA Improvements
- ⏳ Native Push Notifications for emergency doctor calls and lab report alerts.
- ⏳ Background sync for offline draft prescription saves.
- ⏳ Dedicated high-resolution icon packages for iOS Home Screen badges.

---

## 13. Future Roadmap

- [ ] **Pharmacy Inventory Module**: Stock tracking and medicine dispensing integration.
- [ ] **Patient Portal**: Web portal for patients to view test reports and book appointments online.
- [ ] **SMS & WhatsApp Alerts**: Automated appointment reminders and lab report notifications.
- [ ] **ICU & OT Tracking**: Specialist scheduling for operation theaters and intensive care units.

---

## 14. License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---

## 15. Authors & Credits

**Vatsalya Shree Hospital Management System**

- **Lead Developer**: Rudraksh Kushwah ([@kushwahrudraksh3-png](https://github.com/kushwahrudraksh3-png))
- **Organization**: Vatsalya Shree Hospital Engineering Team
- **Repository**: [kushwahrudraksh3-png/hospital-management-system](https://github.com/kushwahrudraksh3-png/hospital-management-system)
