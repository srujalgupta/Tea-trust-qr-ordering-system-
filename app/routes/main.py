from flask import Blueprint, render_template, request, send_file, url_for

from app.services.qr_service import make_qr_png
from app.services.table_service import get_table


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def home():
    return render_template("index.html")


@main_bp.get("/qr/table/<int:table_id>.png")
def table_qr(table_id):
    table = get_table(table_id)
    menu_url = url_for("customer.menu", table=table.id, _external=True)
    image = make_qr_png(menu_url, request.args.get("size", 320))
    return send_file(
        image,
        mimetype="image/png",
        download_name=f"{table.qr_slug}.png",
        max_age=300,
    )
