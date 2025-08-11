from extensions import db
from app import create_app
from models import Category, Component


def run():
    app = create_app()
    with app.app_context():
        # sample categories
        for name in ["Installation", "Materials", "Labor", "Equipment", "Misc"]:
            db.session.merge(Category(name=name))
        db.session.commit()

        # sample components
        inst = Category.query.filter_by(name="Installation").first()
        mats = Category.query.filter_by(name="Materials").first()

        samples = [
            (inst, "Cooler Unit", 350.0, "piece"),
            (mats, 'Pipe 2"', 4.5, "meter"),
            (mats, "Heater", 120.0, "piece"),
        ]
        for cat, name, price, uom in samples:
            db.session.merge(
                Component(
                    category_id=cat.id, name=name, default_unit_price_usd=price, uom=uom
                )
            )
        db.session.commit()
        print("Seeded.")


if __name__ == "__main__":
    run()
