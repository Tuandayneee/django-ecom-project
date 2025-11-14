## Quick context for AI agents

This is a small Django monolith (Django 5.x) with three primary apps:
- `products` — product models, variants, images, and product pages (`products/models.py`, `products/views.py`, `products/urls.py`).
- `accounts` — user/profile, cart, coupons and auth flows (`accounts/models.py`, `accounts/views.py`, `accounts/urls.py`, `accounts/middleware.py`).
- `home` — simple index page (`home/views.py`).

Key project-level files: `ecom/settings.py` (templates, static, email, DB), `ecom/urls.py` (root routing), `manage.py` (dev commands), `db.sqlite3` (local DB).

Design & important patterns
- UUID primary keys: `base.models.BaseModel` provides `uid` as the primary key and `created_at` timestamp — many models inherit from it.
- Slug-based product URLs: `Product.save()` auto-slugifies `product_name`; product views expect `<slug>/` (see `products/urls.py` and `products/models.py`).
- Variant pricing: `SizeVariant` and `ColorVariant` add integer `price` offsets; `Product.get_product_price_by_size(size)` computes price.
- Cart and coupons are session-aware: carts are stored in `accounts.models.Cart` and `CartItems`; session keys used are `cart_id` (session cart) and `coupon_ids` (list of applied coupon IDs). Look at `accounts/views.py` for merging logic during login and coupon handling.
- Middleware: `accounts.middleware.ClearCouponOnLeaveMiddleware` clears `coupon_ids` when users navigate away from cart-related views. Update safe view names in the middleware if you add checkout/related routes.
- Email activation: `accounts.models` uses a post_save signal to create `Profile` and calls `base.emails.send_account_activation_email` — email settings live in `ecom/settings.py`.

Developer workflows (how to run and test locally)
- Start dev server: `python manage.py runserver` (project uses SQLite; DEBUG=True by default in `ecom/settings.py`).
- Migrations: `python manage.py makemigrations` then `python manage.py migrate`.
- Create admin: `python manage.py createsuperuser`.
- Run Django tests: `python manage.py test` (apps have `tests.py` files).
- Static/media: static files live under `public/static`; settings use `STATICFILES_DIRS` and `STATIC_ROOT`. In DEBUG static files are served by `staticfiles_urlpatterns()` in `ecom/urls.py`.

Common pitfalls / repo-specific gotchas
- Secrets in repo: `SECRET_KEY` and Gmail credentials are hardcoded in `ecom/settings.py`. Treat as sensitive — replace with env vars before deployment.
- Session-based coupon logic: coupons are stored as a list of IDs in `request.session['coupon_ids']`. When modifying coupon behavior, update both `accounts/views.py` (apply/remove) and `accounts/middleware.py` (clearing rules).
- Cart merge on login: `accounts.views.login_page` contains explicit logic to merge a session cart into a user cart. Any change to `Cart`/`CartItems` schema should keep this in mind.
- Time checks: `Coupon.is_valid()` uses `timezone.now()`; keep timezone-aware datetimes when setting `valid_to` in fixtures.

Files to inspect for common edits
- Cart / coupon: `accounts/models.py`, `accounts/views.py`, `accounts/middleware.py`
- Product pricing/variants: `products/models.py`, `products/views.py`
- Templates: `templates/` (see `templates/product/product.html`, `templates/accounts/cart.html`)
- Emails: `base/emails.py` (activation flow)

Small examples (copyable intent)
- To check applied coupons in a request: `request.session.get('coupon_ids', [])` — use IDs and fetch Coupon objects with `Coupon.objects.filter(id__in=ids)`.
- To compute a product price by size: `Product.get_product_price_by_size('M')` (see `products/models.py`).

When changing behavior
- Run `makemigrations` + `migrate` and unit tests. Update middleware `safe_view_names` if you add/rename cart-related routes.

If anything here is incomplete or if you want more examples (tests, common refactors, or a checklist for safe deploy), tell me which area to expand.
