# QR Cafe Ordering System

Production-oriented QR cafe ordering system built with Flask, SQLAlchemy, Flask-Login, Flask-SocketIO, Razorpay integration, and PostgreSQL-ready configuration. SQLite is used only as a local fallback when `DATABASE_URL` is empty.

## Features

- Customer menu at `/menu?table=5`
- Six active table QR links are seeded by default, for tables 1-6
- Mobile-first sticky category tabs, search, cart, lazy item images, and video banner support
- Photo-style menu image fallbacks with uploadable item photos in admin
- Session/local-storage cart with server-side price validation
- Table-aware customer navigation across menu, cart, checkout, and order status
- Admin login/logout with Flask-Login and Werkzeug password hashing
- Live order dashboard with SocketIO updates
- Admin order detail modal, quick kitchen status actions, unseen-order highlighting, and cancellation reasons
- Kitchen display mode at `/admin/kitchen`
- Analytics page with revenue, peak hours, top items, prep time, and CSV export
- Daily token generation with PostgreSQL advisory locking and SQLite local fallback
- Razorpay test-mode payment flow with HMAC signature verification
- Mock payment fallback when Razorpay keys or package are unavailable
- Cash payment flow
- Menu item CRUD, image upload, availability toggles
- Branded table QR poster previews with raw QR download, SVG poster download, and print controls
- Order success screen with token, estimated wait, WhatsApp share link, and return-to-menu action
- Kitchen sound and desktop alerts for new admin dashboard orders
- Customer checkout remembers name/phone and supports per-item special instructions
- Admin settings page with password change, production checklist, and backup exports
- POS service hook and notification webhook simulation
- CSRF protection, basic in-memory rate limiting, logging, and security headers
- Gunicorn deployment files for Render/Railway

## Local Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
flask --app run.py init-db
flask --app run.py seed-data
python run.py
```

Open:

- Customer menu: `http://127.0.0.1:5000/menu`
- Admin login: `http://127.0.0.1:5000/admin/login`
- Health check: `http://127.0.0.1:5000/health`

Default dev admin from `.env.example`:

- Username: `admin`
- Password: `admin12345`

Change those before real use.

The default cafe setup uses six tables. To change that later, set `CAFE_TABLE_COUNT`
in `.env` and run `flask --app run.py seed-data`.

## PostgreSQL

Set `DATABASE_URL` to a PostgreSQL URL:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DB_NAME
```

Then run:

```powershell
flask --app run.py init-db
flask --app run.py seed-data
```

For migration-based production workflows, install dependencies and use Flask-Migrate:

```powershell
flask --app run.py db init
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade
```

## Razorpay Test Mode

Set:

```env
RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=xxx
RAZORPAY_WEBHOOK_SECRET=xxx
RAZORPAY_FORCE_MOCK=false
```

If keys or the `razorpay` package are missing, the app uses mock mode so local development still works.

Webhook endpoint:

```text
POST /api/v1/payments/razorpay/webhook
```

## API Endpoints

- `GET /health`
- `GET /api/v1/health`
- `GET /api/v1/menu`
- `POST /api/v1/orders`
- `GET /api/v1/orders/<order_id>`
- `POST /api/v1/payments/razorpay/verify`
- `POST /api/v1/payments/razorpay/webhook`
- `GET /api/v1/admin/orders`
- `PATCH /api/v1/admin/orders/<order_id>/status`
- `GET /api/v1/admin/analytics`
- `GET /api/v1/admin/export/orders.csv`
- `GET /api/v1/admin/export/menu.csv`
- `POST /api/v1/admin/categories`
- `PATCH /api/v1/admin/categories/<category_id>`
- `POST /api/v1/admin/menu-items`
- `PATCH /api/v1/admin/menu-items/<item_id>`
- `DELETE /api/v1/admin/menu-items/<item_id>`
- `POST /api/v1/admin/menu-items/<item_id>/image`
- `GET /api/v1/admin/tables`
- `POST /api/v1/admin/tables`
- `PATCH /api/v1/admin/tables/<table_id>`

Unsafe API requests require the `X-CSRFToken` header except the Razorpay webhook.

## Deployment

Use PostgreSQL in production and set:

```env
APP_ENV=production
FLASK_CONFIG=production
SECRET_KEY=<strong-random-value>
DATABASE_URL=<postgres-url>
SOCKETIO_ASYNC_MODE=eventlet
```

Render and Railway can use:

```text
gunicorn --worker-class eventlet -w 1 wsgi:app
```

Use one worker for Flask-SocketIO unless you add a supported message queue such as Redis.

### Production Checklist

- Set `APP_ENV=production` and `FLASK_CONFIG=production`.
- Set a strong random `SECRET_KEY`; the dev fallback is blocked in production.
- Set `DATABASE_URL` to a PostgreSQL database, then run `flask --app run.py init-db` and `flask --app run.py seed-data`.
- Change `ADMIN_PASSWORD` from `admin12345`; the app refuses to start in production with the default password.
- Confirm `CAFE_TABLE_COUNT`, then open `/admin/tables` to download or print the QR for each table.
- Set Razorpay keys and webhook secret before enabling real online payments.
- Set `SOCKETIO_ASYNC_MODE=eventlet` for Render/Railway-style SocketIO deployment.

## Image Guidelines

Upload compressed JPG/WebP/PNG files under 5 MB. For menu images, target about 1200 px wide and 70-80 quality for JPG/WebP.

## POS Hook

Set `POS_WEBHOOK_URL` to send order JSON to a POS endpoint. If unset, the POS service logs a mock success.

## Notifications

Set `NOTIFICATION_WEBHOOK_URL` to receive simulated WhatsApp-style JSON notifications for order confirmation and ready status. If unset, notifications are logged.
