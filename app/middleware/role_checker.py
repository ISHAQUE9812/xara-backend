from app.auth.role_middleware import require_admin, require_authenticated_user

allow_admin = require_admin
allow_user = require_authenticated_user
allow_admin_or_user = require_authenticated_user
