"""Shared vocabularies for the simulation.

Everything is a `str` Enum so these serialise straight to JSON for the
frontend without a custom encoder.
"""

from enum import Enum


class Allergen(str, Enum):
    GLUTEN = "gluten"
    DAIRY = "dairy"
    EGG = "egg"
    TREE_NUT = "tree_nut"
    PEANUT = "peanut"
    SOY = "soy"
    SESAME = "sesame"


class FlavorCategory(str, Enum):
    """Coarse 'what does this taste of' tags, on top of the numeric meters."""

    CHOCOLATE = "chocolate"
    VANILLA = "vanilla"
    CARAMEL = "caramel"
    FRUIT = "fruit"
    BERRY = "berry"
    CITRUS = "citrus"
    NUT = "nut"
    COFFEE = "coffee"
    SPICE = "spice"
    HERBAL = "herbal"
    FLORAL = "floral"
    CHEESE = "cheese"
    SAVOURY = "savoury"


class Daypart(str, Enum):
    """'Occasion' modelled as time of day, per the design notes."""

    EARLY_MORNING = "early_morning"
    MORNING = "morning"
    LUNCH = "lunch"
    AFTERNOON = "afternoon"
    EVENING = "evening"


class ItemCategory(str, Enum):
    PASTRY = "pastry"
    CAKE = "cake"
    DESSERT = "dessert"
    BREAD = "bread"
    SANDWICH = "sandwich"
    DRINK = "drink"


class Bakery(str, Enum):
    """Who sells the item. Used to pit the two menus against each other."""

    GRANDMAS = "grandmas_bakeria"
    THE_BAKERY = "the_bakery"
