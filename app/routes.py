"""HTTP endpoints. Commands change state; queries only read it."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from . import models, schemas
from .database import get_db

router = APIRouter(prefix="/api/v1")


def _get_restaurant(db: Session, restaurant_id: int) -> models.Restaurant:
    restaurant = db.get(models.Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Restaurant {restaurant_id} not found")
    return restaurant


# ---------------- Restaurants ----------------

@router.post("/restaurants", response_model=schemas.RestaurantOut, status_code=201,
             tags=["restaurants"], summary="Command: register a restaurant")
def create_restaurant(body: schemas.RestaurantCreate, db: Session = Depends(get_db)):
    restaurant = models.Restaurant(**body.model_dump())
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.get("/restaurants", response_model=list[schemas.RestaurantOut],
            tags=["restaurants"], summary="Query: browse/search restaurants")
def list_restaurants(
    city: str | None = None,
    cuisine: str | None = None,
    open_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(models.Restaurant)
    if city:
        stmt = stmt.where(models.Restaurant.city.ilike(city))
    if cuisine:
        stmt = stmt.where(models.Restaurant.cuisine.ilike(cuisine))
    if open_only:
        stmt = stmt.where(models.Restaurant.is_open.is_(True))
    stmt = stmt.order_by(models.Restaurant.id).limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/restaurants/{restaurant_id}", response_model=schemas.RestaurantDetail,
            tags=["restaurants"], summary="Query: restaurant details with menu")
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    stmt = (select(models.Restaurant)
            .options(selectinload(models.Restaurant.menu_items))
            .where(models.Restaurant.id == restaurant_id))
    restaurant = db.scalars(stmt).first()
    if restaurant is None:
        raise HTTPException(404, f"Restaurant {restaurant_id} not found")
    return restaurant


@router.patch("/restaurants/{restaurant_id}/status", response_model=schemas.RestaurantOut,
              tags=["restaurants"], summary="Command: open or close a restaurant")
def update_status(restaurant_id: int, body: schemas.RestaurantStatusUpdate,
                  db: Session = Depends(get_db)):
    restaurant = _get_restaurant(db, restaurant_id)
    restaurant.is_open = body.is_open
    db.commit()
    db.refresh(restaurant)
    return restaurant


# ---------------- Menu ----------------

@router.post("/restaurants/{restaurant_id}/menu-items", response_model=schemas.MenuItemOut,
             status_code=201, tags=["menu"], summary="Command: add a menu item")
def add_menu_item(restaurant_id: int, body: schemas.MenuItemCreate, db: Session = Depends(get_db)):
    _get_restaurant(db, restaurant_id)
    item = models.MenuItem(restaurant_id=restaurant_id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/restaurants/{restaurant_id}/menu", response_model=list[schemas.MenuItemOut],
            tags=["menu"], summary="Query: view a restaurant's menu")
def get_menu(restaurant_id: int, available_only: bool = False, db: Session = Depends(get_db)):
    _get_restaurant(db, restaurant_id)
    stmt = select(models.MenuItem).where(models.MenuItem.restaurant_id == restaurant_id)
    if available_only:
        stmt = stmt.where(models.MenuItem.is_available.is_(True))
    return db.scalars(stmt.order_by(models.MenuItem.id)).all()


@router.patch("/menu-items/{item_id}", response_model=schemas.MenuItemOut,
              tags=["menu"], summary="Command: change price/availability of a menu item")
def update_menu_item(item_id: int, body: schemas.MenuItemUpdate, db: Session = Depends(get_db)):
    item = db.get(models.MenuItem, item_id)
    if item is None:
        raise HTTPException(404, f"Menu item {item_id} not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


# ---------------- Collaboration endpoint for Order Service ----------------

@router.post("/restaurants/{restaurant_id}/validate-order",
             response_model=schemas.ValidateOrderResponse, tags=["collaboration"],
             summary="Query: validate items and price an order (called by Order Service)")
def validate_order(restaurant_id: int, body: schemas.ValidateOrderRequest,
                   db: Session = Depends(get_db)):
    restaurant = _get_restaurant(db, restaurant_id)
    if not restaurant.is_open:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Restaurant '{restaurant.name}' is closed")

    ids = {line.menu_item_id for line in body.items}
    items = {i.id: i for i in db.scalars(select(models.MenuItem).where(models.MenuItem.id.in_(ids)))}

    lines, total, problems = [], Decimal("0"), []
    for line in body.items:
        item = items.get(line.menu_item_id)
        if item is None or item.restaurant_id != restaurant_id:
            problems.append(f"Menu item {line.menu_item_id} does not belong to this restaurant")
            continue
        if not item.is_available:
            problems.append(f"'{item.name}' is currently unavailable")
            continue
        line_total = item.price * line.quantity
        total += line_total
        lines.append(schemas.PricedLine(menu_item_id=item.id, name=item.name,
                                        unit_price=item.price, quantity=line.quantity,
                                        line_total=line_total))
    if problems:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"errors": problems})

    return schemas.ValidateOrderResponse(restaurant_id=restaurant.id,
                                         restaurant_name=restaurant.name,
                                         lines=lines, total_amount=total)
