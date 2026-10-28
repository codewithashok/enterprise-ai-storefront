"""Seed 30 products with OpenAI embeddings.

Idempotent: re-running upserts by SKU. Usage (from backend/):
    python -m scripts.seed_catalog
"""

import asyncio
from decimal import Decimal

from openai import AsyncOpenAI
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.db.models import Product
from app.db.session import AsyncSessionLocal, engine

# (sku, name, category, price, cost_price, inventory_count, description)
CATALOG: list[tuple[str, str, str, str, str, int, str]] = [
    # Electronics
    ("EL-001", "AeroPods Pro Wireless Earbuds", "Electronics", "149.99", "62.00", 120,
     "Active noise-cancelling true wireless earbuds with 30-hour battery, transparency mode and IPX4 sweat resistance for workouts and commutes."),
    ("EL-002", "Lumen 27\" 4K Monitor", "Electronics", "329.00", "190.00", 35,
     "27-inch IPS 4K UHD display with USB-C 65W power delivery, factory colour calibration and slim bezels for home office and photo editing."),
    ("EL-003", "VoltCharge 20000mAh Power Bank", "Electronics", "49.99", "14.50", 300,
     "Compact portable charger with 22.5W fast charging, two USB-C ports and enough capacity to charge a phone four times while travelling."),
    ("EL-004", "Nimbus Mechanical Keyboard", "Electronics", "119.00", "41.00", 0,
     "Hot-swappable 75% mechanical keyboard with tactile switches, RGB backlight and Bluetooth multi-device pairing for coders and gamers."),
    ("EL-005", "PixelView 1080p Webcam", "Electronics", "69.99", "22.00", 85,
     "Full HD webcam with auto light correction, dual noise-reducing microphones and privacy shutter for clear video calls and streaming."),
    ("EL-006", "SoundCube Smart Speaker", "Electronics", "89.00", "33.00", 60,
     "Room-filling Wi-Fi smart speaker with voice assistant, multi-room audio and rich bass for music, podcasts and smart home control."),
    # Home & Kitchen
    ("HK-001", "BrewMaster Pour-Over Coffee Set", "Home & Kitchen", "54.00", "18.00", 75,
     "Glass pour-over dripper, gooseneck kettle and reusable steel filter for a slow, flavourful morning coffee ritual."),
    ("HK-002", "ChefEdge 8\" Chef's Knife", "Home & Kitchen", "79.00", "21.00", 140,
     "Forged high-carbon German steel chef's knife with full tang and ergonomic handle for precise chopping, slicing and dicing."),
    ("HK-003", "AirCrisp 5L Air Fryer", "Home & Kitchen", "99.99", "38.00", 50,
     "Digital air fryer with 8 presets and a 5-litre basket that cooks crispy fries and chicken with up to 85% less oil."),
    ("HK-004", "CloudRest Memory Foam Pillow", "Home & Kitchen", "45.00", "11.00", 200,
     "Contoured cooling-gel memory foam pillow that supports neck alignment for side and back sleepers and reduces night sweats."),
    ("HK-005", "PureMist Air Purifier", "Home & Kitchen", "139.00", "52.00", 25,
     "True HEPA air purifier for rooms up to 40 square metres that removes dust, pollen, pet dander and smoke with a quiet sleep mode."),
    ("HK-006", "CastIron Classic Skillet 12\"", "Home & Kitchen", "39.00", "12.00", 90,
     "Pre-seasoned cast iron skillet with even heat retention for searing steak, baking cornbread and campfire cooking."),
    # Apparel
    ("AP-001", "StormShell Waterproof Jacket", "Apparel", "189.00", "64.00", 45,
     "Lightweight breathable rain jacket with sealed seams, adjustable hood and packable design for hiking in wet and windy weather."),
    ("AP-002", "Merino Base Layer Crew", "Apparel", "79.00", "24.00", 110,
     "Soft merino wool long-sleeve base layer that regulates temperature, wicks moisture and resists odour on multi-day trips."),
    ("AP-003", "Everyday Stretch Chinos", "Apparel", "65.00", "17.00", 160,
     "Slim-fit cotton stretch chinos that move with you, smart enough for the office and comfortable enough for weekends."),
    ("AP-004", "TrailRunner GTX Shoes", "Apparel", "149.00", "55.00", 0,
     "Waterproof trail running shoes with aggressive grip outsole, rock plate and cushioned midsole for muddy mountain paths."),
    ("AP-005", "Organic Cotton Hoodie", "Apparel", "59.00", "15.00", 220,
     "Heavyweight organic cotton fleece hoodie with relaxed fit and kangaroo pocket for cosy layering on cold days."),
    ("AP-006", "Thermal Down Vest", "Apparel", "119.00", "40.00", 30,
     "Packable 700-fill down vest that traps warmth without bulk, ideal as a mid-layer for winter walks and ski trips."),
    # Sports & Outdoors
    ("SO-001", "Summit 2-Person Tent", "Sports & Outdoors", "229.00", "88.00", 20,
     "Freestanding ultralight backpacking tent with two doors, aluminium poles and full rainfly for three-season camping."),
    ("SO-002", "Glacier 32oz Insulated Bottle", "Sports & Outdoors", "34.99", "8.00", 400,
     "Double-wall vacuum insulated stainless steel bottle that keeps drinks cold for 24 hours or hot for 12 on the trail."),
    ("SO-003", "Ridge 45L Hiking Backpack", "Sports & Outdoors", "159.00", "58.00", 40,
     "Ventilated 45-litre trekking pack with adjustable torso, hip belt pockets and rain cover for weekend hiking trips."),
    ("SO-004", "Polar Sleeping Bag -5°C", "Sports & Outdoors", "129.00", "47.00", 15,
     "Mummy-style synthetic sleeping bag rated to -5°C with draft collar and compression sack for cold-weather camping."),
    ("SO-005", "Carbon Trekking Poles", "Sports & Outdoors", "89.00", "29.00", 70,
     "Collapsible carbon fibre trekking poles with cork grips and quick-lock adjustment that reduce knee strain on descents."),
    ("SO-006", "Headlamp 400 Lumen", "Sports & Outdoors", "29.99", "7.50", 0,
     "Rechargeable LED headlamp with red night mode and 400-lumen beam for night hikes, camping and running in the dark."),
    # Health & Fitness
    ("HF-001", "FlexCore Adjustable Dumbbells", "Health & Fitness", "299.00", "120.00", 18,
     "Space-saving adjustable dumbbell pair from 2 to 24 kg with a quick dial selector for full home gym strength training."),
    ("HF-002", "ZenGrip Yoga Mat", "Health & Fitness", "49.00", "13.00", 180,
     "6mm non-slip natural rubber yoga mat with alignment lines and cushioning for yoga, pilates and floor workouts."),
    ("HF-003", "PulseTrack Fitness Watch", "Health & Fitness", "199.00", "78.00", 55,
     "GPS fitness smartwatch with heart rate, sleep tracking, VO2 max estimates and 10-day battery for runners and cyclists."),
    ("HF-004", "RecoverPro Massage Gun", "Health & Fitness", "129.00", "44.00", 65,
     "Percussion massage gun with five attachments and quiet motor to relieve muscle soreness after training."),
    ("HF-005", "Resistance Band Set", "Health & Fitness", "29.00", "6.00", 250,
     "Set of five latex resistance bands with handles, door anchor and ankle straps for portable full-body workouts."),
    ("HF-006", "Whey Isolate Protein 2kg", "Health & Fitness", "64.00", "26.00", 95,
     "Low-sugar whey protein isolate with 27g protein per serving to support muscle recovery, chocolate flavour."),
]

# Hidden from shoppers/LLM via the alias layer — exercises is_active filtering
DISCONTINUED_SKUS = {"HK-006"}


def embedding_text(name: str, category: str, description: str) -> str:
    return f"{name}. Category: {category}. {description}"


async def embed(texts: list[str]) -> list[list[float]]:
    async with AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value()) as client:
        response = await client.embeddings.create(model=settings.EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]


async def seed() -> None:
    if not settings.OPENAI_API_KEY.get_secret_value():
        raise SystemExit("OPENAI_API_KEY is not set in backend/.env")

    engine.sync_engine.echo = False  # 30 x 1536 floats would flood the terminal

    vectors = await embed([embedding_text(name, cat, desc) for _, name, cat, _, _, _, desc in CATALOG])

    rows = [
        {
            "sku": sku,
            "name": name,
            "category": category,
            "price": Decimal(price),
            "cost_price": Decimal(cost_price),
            "inventory_count": inventory,
            "description": description,
            "embedding": vector,
            "is_active": sku not in DISCONTINUED_SKUS,
            "is_deleted": False,
        }
        for (sku, name, category, price, cost_price, inventory, description), vector in zip(CATALOG, vectors)
    ]

    stmt = insert(Product).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Product.sku],
        set_={
            **{col: stmt.excluded[col] for col in rows[0] if col != "sku"},
            "updated_at": func.now(),
        },
    )

    async with AsyncSessionLocal() as session:
        await session.execute(stmt)
        await session.commit()

    await engine.dispose()
    print(f"Seeded {len(rows)} products ({len(vectors[0])}-dim embeddings via {settings.EMBEDDING_MODEL})")


if __name__ == "__main__":
    asyncio.run(seed())
