from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    def has_column(table, col):
        rows = db.session.execute(text(f"PRAGMA table_info('{table}')")).fetchall()
        # PRAGMA table_info returns rows where second column (name) is column name
        return any(r[1] == col for r in rows)

    changes = []
    if not has_column('user', 'phone'):
        db.session.execute(text("ALTER TABLE user ADD COLUMN phone VARCHAR(30)"))
        changes.append('user.phone')

    if not has_column('user', 'address'):
        db.session.execute(text("ALTER TABLE user ADD COLUMN address TEXT"))
        changes.append('user.address')

    # SQLite table name for Order is likely 'order'
    if not has_column('order', 'status'):
        # Use single quotes around table name to be safe
        db.session.execute(text("ALTER TABLE 'order' ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"))
        changes.append('order.status')

    # Add product.status if missing (used to mark active/inactive products)
    if not has_column('product', 'status'):
        db.session.execute(text("ALTER TABLE product ADD COLUMN status VARCHAR(20) DEFAULT 'active'"))
        changes.append('product.status')

    if not has_column('user', 'email'):
        # Add email column (may be null for existing users)
        db.session.execute(text("ALTER TABLE user ADD COLUMN email VARCHAR(120)"))
        changes.append('user.email')

    if changes:
        db.session.commit()
        print('Applied schema changes:', ', '.join(changes))
    else:
        print('No schema changes needed.')
