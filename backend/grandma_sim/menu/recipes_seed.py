"""Ingredient prices and recipes for the seed menus.

Shares are by mass and sum to 1.0 per item. Both bakeries use the same base
price list; grandma's pays a premium for better ingredients and The Bakery
buys in bulk, which is how the price gap on the shelf gets a cost gap behind it.
"""

from ..core.enums import Bakery
from .costing import Ingredient, Pantry, Recipe, RecipeBook, RecipeLine
from .seed import build_menus

GRANDMAS_PRICE_FACTOR = 1.3
THE_BAKERY_PRICE_FACTOR = 0.75

BASE_PRICES_PER_KG = {
    "flour": 1.2,
    "bread": 3.0,
    "butter": 11.0,
    "sugar": 1.5,
    "egg": 4.0,
    "milk": 1.3,
    "cream": 7.0,
    "pumpkin": 3.0,
    "granola": 8.0,
    "pecans": 25.0,
    "maple_syrup": 20.0,
    "spice": 40.0,
    "cinnamon": 30.0,
    "water": 0.01,
    "salt": 1.0,
    "lemon": 4.0,
    "dark_chocolate": 18.0,
    "ham": 14.0,
    "gruyere": 28.0,
    "multigrain": 3.0,
    "espresso": 12.0,
    "turkey": 13.0,
    "bacon": 15.0,
    "lettuce": 4.0,
    "mayo": 5.0,
}

RECIPES: dict[str, dict[str, float]] = {
    "fall_parfait": {
        "cream": 0.35, "pumpkin": 0.25, "granola": 0.20,
        "pecans": 0.10, "maple_syrup": 0.08, "spice": 0.02,
    },
    "morning_bun": {
        "flour": 0.45, "butter": 0.20, "sugar": 0.15,
        "milk": 0.10, "egg": 0.08, "cinnamon": 0.02,
    },
    "sourdough_loaf": {"flour": 0.61, "water": 0.37, "salt": 0.02},
    "lemon_tart": {
        "flour": 0.20, "butter": 0.15, "sugar": 0.20,
        "egg": 0.20, "lemon": 0.20, "cream": 0.05,
    },
    "hot_chocolate": {"milk": 0.85, "dark_chocolate": 0.12, "sugar": 0.03},
    "gruyere_croissant": {
        "flour": 0.30, "butter": 0.15, "ham": 0.20,
        "gruyere": 0.20, "milk": 0.10, "egg": 0.05,
    },
    "autumn_parfait": {
        "cream": 0.35, "pumpkin": 0.25, "granola": 0.25,
        "sugar": 0.10, "spice": 0.02, "pecans": 0.03,
    },
    "cinnamon_swirl": {
        "flour": 0.40, "sugar": 0.30, "butter": 0.10,
        "milk": 0.10, "egg": 0.08, "cinnamon": 0.02,
    },
    "multigrain_loaf": {"flour": 0.46, "multigrain": 0.15, "water": 0.37, "salt": 0.02},
    "lemon_square": {
        "flour": 0.20, "butter": 0.15, "sugar": 0.30, "egg": 0.20, "lemon": 0.15,
    },
    "mocha_latte": {
        "milk": 0.80, "espresso": 0.10, "dark_chocolate": 0.05, "sugar": 0.05,
    },
    "turkey_club": {
        "bread": 0.30, "turkey": 0.30, "bacon": 0.15, "lettuce": 0.10, "mayo": 0.15,
    },
}

GRANDMAS_RECIPE_IDS = [
    "fall_parfait", "morning_bun", "sourdough_loaf",
    "lemon_tart", "hot_chocolate", "gruyere_croissant",
]
THE_BAKERY_RECIPE_IDS = [
    "autumn_parfait", "cinnamon_swirl", "multigrain_loaf",
    "lemon_square", "mocha_latte", "turkey_club",
]


def base_pantry() -> Pantry:
    return Pantry().add(
        *(Ingredient(id=i, name=i.replace("_", " ").title(), price_per_kg=p)
          for i, p in BASE_PRICES_PER_KG.items())
    )


def _book(pantry: Pantry, recipe_ids: list[str]) -> RecipeBook:
    # Recipes are written for the seed menu's sweetness, which is the baseline
    # any day-profile sweetness change is scaled from.
    base_sweetness = {
        item.id: item.flavor.sweet_savoury
        for menu in build_menus()
        for item in menu.items
    }
    return RecipeBook(pantry=pantry).add(
        *(
            Recipe(
                item_id=rid,
                lines=[RecipeLine(ingredient_id=i, share=s) for i, s in RECIPES[rid].items()],
                base_sweetness=base_sweetness[rid],
            )
            for rid in recipe_ids
        )
    )


def build_recipe_books() -> tuple[RecipeBook, RecipeBook]:
    """(grandma's, The Bakery) -- same price list, different buying power."""
    base = base_pantry()
    return (
        _book(base.scaled(GRANDMAS_PRICE_FACTOR), GRANDMAS_RECIPE_IDS),
        _book(base.scaled(THE_BAKERY_PRICE_FACTOR), THE_BAKERY_RECIPE_IDS),
    )


def recipe_books_by_bakery() -> dict[Bakery, RecipeBook]:
    grandmas, the_bakery = build_recipe_books()
    return {Bakery.GRANDMAS: grandmas, Bakery.THE_BAKERY: the_bakery}
