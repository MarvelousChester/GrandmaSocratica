"""Starting menus for both bakeries.

Hand-authored so the customer sim has a real spread to choose between.
The shape of the contrast is deliberate: The Bakery is sweeter, cheaper and
smaller-portioned across the board, grandma's is savoury-capable, pricier and
more generous -- so a customer's price sensitivity and sweet tooth actually
pull in different directions.
"""

from .enums import Allergen, Bakery, Daypart, FlavorCategory, ItemCategory
from .flavor import FlavorProfile
from .items import Menu, MenuItem

GRANDMAS_ITEMS = [
    MenuItem(
        id="fall_parfait",
        name="Fall Parfait",
        bakery=Bakery.GRANDMAS,
        category=ItemCategory.DESSERT,
        description="Whipped cream, spiced pumpkin, maple granola, candied pecans.",
        flavor=FlavorProfile(
            sweet_savoury=0.55,
            bitterness=0.08,
            fruitiness=0.45,
            categories={
                FlavorCategory.SPICE,
                FlavorCategory.NUT,
                FlavorCategory.CARAMEL,
                FlavorCategory.FRUIT,
            },
        ),
        price=8.50,
        portion_size_g=340,
        allergens={Allergen.DAIRY, Allergen.GLUTEN, Allergen.TREE_NUT},
        daypart_weights={
            Daypart.EARLY_MORNING: 0.1,
            Daypart.MORNING: 0.4,
            Daypart.LUNCH: 0.7,
            Daypart.AFTERNOON: 1.0,
            Daypart.EVENING: 0.8,
        },
    ),
    MenuItem(
        id="morning_bun",
        name="Morning Bun",
        bakery=Bakery.GRANDMAS,
        category=ItemCategory.PASTRY,
        description="Laminated dough rolled in cinnamon sugar.",
        flavor=FlavorProfile(
            sweet_savoury=0.6,
            bitterness=0.1,
            fruitiness=0.05,
            categories={FlavorCategory.SPICE, FlavorCategory.CARAMEL},
        ),
        price=4.25,
        portion_size_g=110,
        allergens={Allergen.GLUTEN, Allergen.DAIRY, Allergen.EGG},
        daypart_weights={
            Daypart.EARLY_MORNING: 1.0,
            Daypart.MORNING: 0.95,
            Daypart.LUNCH: 0.4,
            Daypart.AFTERNOON: 0.3,
            Daypart.EVENING: 0.1,
        },
    ),
    MenuItem(
        id="sourdough_loaf",
        name="Sourdough Loaf",
        bakery=Bakery.GRANDMAS,
        category=ItemCategory.BREAD,
        description="Three-day starter, baked each morning.",
        flavor=FlavorProfile(sweet_savoury=-0.4, bitterness=0.2, fruitiness=0.05),
        price=7.00,
        portion_size_g=800,
        allergens={Allergen.GLUTEN},
        daypart_weights={
            Daypart.EARLY_MORNING: 0.8,
            Daypart.MORNING: 0.9,
            Daypart.LUNCH: 0.6,
            Daypart.AFTERNOON: 0.5,
            Daypart.EVENING: 0.3,
        },
    ),
    MenuItem(
        id="lemon_tart",
        name="Lemon Tart",
        bakery=Bakery.GRANDMAS,
        category=ItemCategory.DESSERT,
        description="Shortcrust, lemon curd, torched meringue.",
        flavor=FlavorProfile(
            sweet_savoury=0.5,
            bitterness=0.15,
            fruitiness=0.85,
            categories={FlavorCategory.CITRUS, FlavorCategory.FRUIT},
        ),
        price=5.75,
        portion_size_g=140,
        allergens={Allergen.GLUTEN, Allergen.DAIRY, Allergen.EGG},
        daypart_weights={
            Daypart.EARLY_MORNING: 0.1,
            Daypart.MORNING: 0.3,
            Daypart.LUNCH: 0.7,
            Daypart.AFTERNOON: 0.9,
            Daypart.EVENING: 0.8,
        },
    ),
    MenuItem(
        id="hot_chocolate",
        name="Hot Chocolate",
        bakery=Bakery.GRANDMAS,
        category=ItemCategory.DRINK,
        description="Dark chocolate melted into whole milk.",
        flavor=FlavorProfile(
            sweet_savoury=0.7,
            bitterness=0.4,
            fruitiness=0.0,
            categories={FlavorCategory.CHOCOLATE},
        ),
        price=4.50,
        portion_size_g=350,
        allergens={Allergen.DAIRY},
        daypart_weights={
            Daypart.EARLY_MORNING: 0.8,
            Daypart.MORNING: 0.8,
            Daypart.LUNCH: 0.5,
            Daypart.AFTERNOON: 0.7,
            Daypart.EVENING: 0.9,
        },
    ),
    MenuItem(
        id="gruyere_croissant",
        name="Ham & Gruyère Croissant",
        bakery=Bakery.GRANDMAS,
        category=ItemCategory.SANDWICH,
        description="Yesterday's croissants, split and baked with béchamel.",
        flavor=FlavorProfile(
            sweet_savoury=-0.6,
            bitterness=0.1,
            fruitiness=0.0,
            categories={FlavorCategory.CHEESE, FlavorCategory.SAVOURY},
        ),
        price=7.25,
        portion_size_g=160,
        allergens={Allergen.GLUTEN, Allergen.DAIRY, Allergen.EGG},
        daypart_weights={
            Daypart.EARLY_MORNING: 0.4,
            Daypart.MORNING: 0.7,
            Daypart.LUNCH: 1.0,
            Daypart.AFTERNOON: 0.5,
            Daypart.EVENING: 0.2,
        },
    ),
]

THE_BAKERY_ITEMS = [
    MenuItem(
        id="autumn_parfait",
        name="Autumn Parfait",
        bakery=Bakery.THE_BAKERY,
        category=ItemCategory.DESSERT,
        description="Pumpkin spice parfait with granola. Suspiciously familiar.",
        flavor=FlavorProfile(
            sweet_savoury=0.65,
            bitterness=0.06,
            fruitiness=0.38,
            categories={
                FlavorCategory.SPICE,
                FlavorCategory.NUT,
                FlavorCategory.CARAMEL,
                FlavorCategory.FRUIT,
            },
        ),
        price=6.95,
        portion_size_g=290,
        allergens={Allergen.DAIRY, Allergen.GLUTEN, Allergen.TREE_NUT},
        daypart_weights={
            Daypart.EARLY_MORNING: 0.2,
            Daypart.MORNING: 0.5,
            Daypart.LUNCH: 0.8,
            Daypart.AFTERNOON: 1.0,
            Daypart.EVENING: 0.7,
        },
    ),
    MenuItem(
        id="cinnamon_swirl",
        name="Cinnamon Swirl",
        bakery=Bakery.THE_BAKERY,
        category=ItemCategory.PASTRY,
        description="Frosted, shelf-stable, available every day of the year.",
        flavor=FlavorProfile(
            sweet_savoury=0.85,
            bitterness=0.05,
            fruitiness=0.0,
            categories={FlavorCategory.SPICE, FlavorCategory.CARAMEL},
        ),
        price=3.95,
        portion_size_g=130,
        allergens={Allergen.GLUTEN, Allergen.DAIRY, Allergen.SOY},
        daypart_weights={
            Daypart.EARLY_MORNING: 1.0,
            Daypart.MORNING: 1.0,
            Daypart.LUNCH: 0.6,
            Daypart.AFTERNOON: 0.5,
            Daypart.EVENING: 0.3,
        },
    ),
    MenuItem(
        id="multigrain_loaf",
        name="Multigrain Loaf",
        bakery=Bakery.THE_BAKERY,
        category=ItemCategory.BREAD,
        description="Par-baked off-site, finished in store.",
        flavor=FlavorProfile(sweet_savoury=-0.25, bitterness=0.25, fruitiness=0.05),
        price=5.50,
        portion_size_g=700,
        allergens={Allergen.GLUTEN, Allergen.SOY, Allergen.SESAME},
        daypart_weights={
            Daypart.EARLY_MORNING: 0.7,
            Daypart.MORNING: 0.8,
            Daypart.LUNCH: 0.6,
            Daypart.AFTERNOON: 0.5,
            Daypart.EVENING: 0.4,
        },
    ),
    MenuItem(
        id="lemon_square",
        name="Lemon Square",
        bakery=Bakery.THE_BAKERY,
        category=ItemCategory.DESSERT,
        description="Dusted with powdered sugar.",
        flavor=FlavorProfile(
            sweet_savoury=0.75,
            bitterness=0.05,
            fruitiness=0.7,
            categories={FlavorCategory.CITRUS, FlavorCategory.FRUIT},
        ),
        price=3.75,
        portion_size_g=95,
        allergens={Allergen.GLUTEN, Allergen.DAIRY, Allergen.EGG, Allergen.SOY},
        daypart_weights={
            Daypart.EARLY_MORNING: 0.2,
            Daypart.MORNING: 0.4,
            Daypart.LUNCH: 0.8,
            Daypart.AFTERNOON: 0.9,
            Daypart.EVENING: 0.6,
        },
    ),
    MenuItem(
        id="mocha_latte",
        name="Mocha Latte",
        bakery=Bakery.THE_BAKERY,
        category=ItemCategory.DRINK,
        description="Large by default.",
        flavor=FlavorProfile(
            sweet_savoury=0.6,
            bitterness=0.55,
            fruitiness=0.0,
            categories={FlavorCategory.COFFEE, FlavorCategory.CHOCOLATE},
        ),
        price=5.25,
        portion_size_g=470,
        allergens={Allergen.DAIRY},
        daypart_weights={
            Daypart.EARLY_MORNING: 1.0,
            Daypart.MORNING: 1.0,
            Daypart.LUNCH: 0.7,
            Daypart.AFTERNOON: 0.6,
            Daypart.EVENING: 0.3,
        },
    ),
    MenuItem(
        id="turkey_club",
        name="Turkey Club",
        bakery=Bakery.THE_BAKERY,
        category=ItemCategory.SANDWICH,
        description="Pre-wrapped, grab and go.",
        flavor=FlavorProfile(
            sweet_savoury=-0.7,
            bitterness=0.05,
            fruitiness=0.05,
            categories={FlavorCategory.SAVOURY},
        ),
        price=9.50,
        portion_size_g=320,
        allergens={Allergen.GLUTEN, Allergen.EGG, Allergen.SOY},
        daypart_weights={
            Daypart.EARLY_MORNING: 0.1,
            Daypart.MORNING: 0.3,
            Daypart.LUNCH: 1.0,
            Daypart.AFTERNOON: 0.6,
            Daypart.EVENING: 0.4,
        },
    ),
]


def build_menus() -> tuple[Menu, Menu]:
    grandmas = Menu(bakery=Bakery.GRANDMAS).add(
        *(item.model_copy(deep=True) for item in GRANDMAS_ITEMS)
    )
    the_bakery = Menu(bakery=Bakery.THE_BAKERY).add(
        *(item.model_copy(deep=True) for item in THE_BAKERY_ITEMS)
    )
    return grandmas, the_bakery
