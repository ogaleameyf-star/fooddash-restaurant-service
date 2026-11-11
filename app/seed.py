"""Sample data so the service is usable right after deployment."""
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import MenuItem, Restaurant

SAMPLE = [
    ("Shree Krishna Misal", "Maharashtrian", "Pune", "FC Road, Shivajinagar", [
        ("Misal Pav", "Spicy sprouts curry with pav", "120.00", True),
        ("Sabudana Vada", "Crispy tapioca fritters (2 pcs)", "80.00", True),
        ("Kokum Sharbat", "Chilled kokum cooler", "50.00", True),
    ]),
    ("Biryani Junction", "Hyderabadi", "Pune", "Baner Road, Baner", [
        ("Chicken Dum Biryani", "Slow-cooked basmati with chicken", "280.00", False),
        ("Veg Biryani", "Seasonal vegetables and saffron rice", "220.00", True),
        ("Mirchi ka Salan", "Chilli and peanut gravy", "90.00", True),
    ]),
    ("Napoli Wood Fired", "Italian", "Mumbai", "Bandra West", [
        ("Margherita Pizza", "Tomato, mozzarella, basil", "350.00", True),
        ("Penne Arrabbiata", "Spicy tomato sauce", "320.00", True),
    ]),
]


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Restaurant)):
        return
    for name, cuisine, city, address, menu in SAMPLE:
        r = Restaurant(name=name, cuisine=cuisine, city=city, address=address)
        r.menu_items = [MenuItem(name=n, description=d, price=Decimal(p), is_veg=v)
                        for n, d, p, v in menu]
        db.add(r)
    db.commit()
