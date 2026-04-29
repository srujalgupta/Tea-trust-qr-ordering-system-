from app.extensions import db

class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255))

    is_available = db.Column(db.Boolean, default=True)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))