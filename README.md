# QR Cafe Ordering System

Production-oriented QR cafe ordering system built with Flask, SQLAlchemy, Flask-Login, Flask-SocketIO, pay-at-store checkout, admin delivery-app portal links, and PostgreSQL-ready configuration. SQLite is used only as a local fallback when `DATABASE_URL` is empty.

## Features

- Customer menu at `/menu?table=5`
- Store/location selector for Store 1 and Store 2, with separate menus, prices,
  tables, orders, tokens, analytics, and customer contacts per store
- Six active table QR links are seeded by default, and more tables can be added from `/admin/tables`
- Mobile-first sticky category tabs, search, cart, lazy item images, and video banner support
- Photo-style menu image fallbacks with uploadable item photos in admin
- Session/local-storage cart with server-side price validation
- Table-aware customer navigation across menu, cart, checkout, and order status
- Admin login/logout with Flask-Login and Werkzeug password hashing
- Staff profiles for owner, manager, counter, kitchen, and menu-only access
- Live order dashboard with SocketIO updates
- Admin order detail modal, quick kitchen status actions, unseen-order highlighting, and cancellation reasons
- Kitchen display mode at `/admin/kitchen`
- Dashboard buttons open the Zomato and Swiggy partner portals in a new tab
- Analytics page with revenue, peak hours, top items, prep time, and CSV export
- Daily token generation with PostgreSQL advisory locking and SQLite local fallback
- Pay-at-store checkout flow with cash status tracking
- Menu item CRUD, image upload, availability toggles
- Branded table QR poster previews with automatic local QR generation, raw QR download, SVG poster download, and print controls
- Order success screen with token, estimated wait, WhatsApp share link, and return-to-menu action
- Customer order status links require the random order number lookup key instead of numeric IDs alone
- Kitchen sound and desktop alerts for new admin dashboard orders
- Customer checkout remembers name/phone and supports per-item special instructions
- Customer contacts are saved permanently by phone number for opted-in broadcast exports
- Admin settings page with password change, cafe settings, staff profiles, and owner-only customer broadcasts
- Deployment seeding creates missing starter menu/tables without overwriting live admin menu, availability, or table changes
- POS service hook and notification webhook simulation
- CSRF protection, login/order throttling, hardened session cookies, CSP/HSTS-ready
  browser headers, image upload validation, logging, and basic in-memory rate limiting
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

The default cafe setup seeds Store 1 and Store 2. Each store gets its own copy of
the starter menu and six tables, so changing an item price or table in one store
does not change the other. Add more tables from `/admin/tables`; each new table
automatically gets a store-aware menu link, local QR image, and printable poster.
Use `CAFE_TABLE_COUNT` only when you want to change how many tables are seeded by
default per store.

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

## Payment Mode

Customer checkout is configured for pay-at-counter only. Orders are created as
`cash_pending`, shown on the customer/admin bills, and marked `paid` when the
order is completed by admin.

## API Endpoints

- `GET /health`
- `GET /api/v1/health`
- `GET /api/v1/stores`
- `GET /api/v1/menu?store=store-1`
- `POST /api/v1/orders`
- `GET /api/v1/orders/<order_id>`
- `GET /api/v1/admin/orders?store=store-1`
- `PATCH /api/v1/admin/orders/<order_id>/status`
- `GET /api/v1/admin/analytics?store=store-1`
- `GET /api/v1/admin/export/orders.csv?store=store-1`
- `GET /api/v1/admin/export/menu.csv?store=store-1`
- `GET /api/v1/admin/export/customers.csv?marketing_only=1`
- `GET /api/v1/admin/customers?marketing_only=1`
- `POST /api/v1/admin/broadcasts`
- `GET /api/v1/admin/staff`
- `POST /api/v1/admin/staff`
- `PATCH /api/v1/admin/staff/<user_id>`
- `DELETE /api/v1/admin/staff/<user_id>`
- `POST /api/v1/admin/categories`
- `PATCH /api/v1/admin/categories/<category_id>`
- `POST /api/v1/admin/menu-items`
- `PATCH /api/v1/admin/menu-items/<item_id>`
- `DELETE /api/v1/admin/menu-items/<item_id>`
- `POST /api/v1/admin/menu-items/<item_id>/image`
- `GET /api/v1/admin/tables?store=store-1`
- `POST /api/v1/admin/tables`
- `PATCH /api/v1/admin/tables/<table_id>`
- `GET /qr/table/<table_id>.png`

Most customer and admin endpoints accept `store` or `store_id`. If omitted, the
app uses Store 1.

Unsafe API requests require the `X-CSRFToken` header.

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
unset GUNICORN_CMD_ARGS; flask --app run.py init-db && flask --app run.py seed-data && gunicorn --bind 0.0.0.0:${PORT:-10000} --worker-class gunicorn.workers.geventlet.EventletWorker -w 1 wsgi:app
```

Use one worker for Flask-SocketIO unless you add a supported message queue such as Redis.

### Production Checklist

- Set `APP_ENV=production` and `FLASK_CONFIG=production`.
- Set a strong random `SECRET_KEY` with at least 32 characters; the dev fallback is blocked in production.
- Set `DATABASE_URL` to a PostgreSQL database, then run `flask --app run.py init-db` and `flask --app run.py seed-data`.
- `seed-data` is safe to run during deploys: it creates missing starter data but does not reset client-edited menu items or added tables.
- Change `ADMIN_PASSWORD` from `admin12345` to a password with at least 12 characters; the app refuses to start in production with the default password.
- Keep `AUTH_LOGIN_RATE_LIMIT_REQUESTS` and `ORDER_CREATE_RATE_LIMIT_REQUESTS` low in production, set `TRUST_PROXY_HEADERS=true` only when the app is behind Render/Railway/a trusted reverse proxy, and keep `SECURITY_CSP_ENABLED=true`.
- Confirm `CAFE_TABLE_COUNT`, then open `/admin/tables` to download or print the QR for each table.
- Set `SOCKETIO_ASYNC_MODE=eventlet` for Render/Railway-style SocketIO deployment.
- Set either `NOTIFICATION_WEBHOOK_URL` or the WhatsApp Cloud variables before using customer broadcasts in production.

## Image Guidelines

Upload compressed JPG/WebP/PNG files under 5 MB. For menu images, target about 1200 px wide and 70-80 quality for JPG/WebP.

## POS Hook

Set `POS_WEBHOOK_URL` to send order JSON to a POS endpoint. If unset, the POS service logs a mock success.

## Notifications

Set `NOTIFICATION_WEBHOOK_URL` to receive simulated WhatsApp-style JSON notifications for order confirmation and ready status. If unset, notifications are logged.

## WhatsApp Broadcasts

Customer broadcasts send to every opted-in customer from Admin Settings. In local development they run in mock mode unless a provider is configured. For real WhatsApp Cloud delivery, create an approved marketing template with one body variable for the message text, then set:

```env
BROADCAST_SEND_WORKERS=8
WHATSAPP_PHONE_NUMBER_ID=your_meta_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_meta_access_token
WHATSAPP_BROADCAST_TEMPLATE_NAME=your_approved_template_name
WHATSAPP_TEMPLATE_LANGUAGE=en_US
WHATSAPP_DEFAULT_COUNTRY_CODE=91
```

For a webhook-based broadcast test in production, set only `NOTIFICATION_WEBHOOK_URL`. Render users must add it in the Render service environment; local `.env` values are not automatically deployed.

`WHATSAPP_ALLOW_FREEFORM_TEXT=true` is only for active 24-hour WhatsApp chats; normal marketing broadcasts should use an approved template.
