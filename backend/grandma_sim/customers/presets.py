"""A starting population for the sim, hand-tuned to be plausible.

Five segments whose habits pull against the two menus differently: commuters
want cheap coffee early, the lunch crowd wants savoury and filling, students
want sugar on a budget, regulars pay up for grandma's, and the after-work
crowd picks up something for dinner on the way home.
"""

from ..core.enums import Allergen, Bakery, FlavorCategory
from .distributions import Beta, Normal
from .population import PopulationConfig, SegmentConfig

# Rough real-world avoidance rates, shared by every segment.
ALLERGEN_PREVALENCE: dict[Allergen, float] = {
    Allergen.GLUTEN: 0.05,
    Allergen.DAIRY: 0.08,
    Allergen.EGG: 0.02,
    Allergen.TREE_NUT: 0.03,
    Allergen.PEANUT: 0.02,
    Allergen.SOY: 0.01,
    Allergen.SESAME: 0.01,
}


def _affinity(mean: float, sd: float = 0.3) -> Normal:
    return Normal(mean=mean, sd=sd, low=-1.0, high=1.0)


COMMUTER = SegmentConfig(
    name="commuter",
    share=0.31,
    sweet_savoury=Normal(mean=0.2, sd=0.4, low=-1.0, high=1.0),
    bitterness=Beta(a=4.0, b=3.0),
    pickiness=Normal(mean=1.5, sd=0.4, low=0.0),
    category_affinity={FlavorCategory.COFFEE: _affinity(0.6)},
    allergen_prevalence=ALLERGEN_PREVALENCE,
    price_sensitivity=Normal(mean=1.2, sd=0.3, low=0.0),
    portion_preference=Normal(mean=-0.3, sd=0.3, low=-1.0, high=1.0),
    visit_probability=Beta(a=5.0, b=2.0),
    arrival_minute=Normal(mean=7.5 * 60, sd=40),
    arrival_spread=Normal(mean=15, sd=5, low=0.0),
)

LUNCH_WORKER = SegmentConfig(
    name="lunch_worker",
    share=0.27,
    sweet_savoury=Normal(mean=-0.2, sd=0.4, low=-1.0, high=1.0),
    category_affinity={
        FlavorCategory.SAVOURY: _affinity(0.5),
        FlavorCategory.CHEESE: _affinity(0.4),
    },
    allergen_prevalence=ALLERGEN_PREVALENCE,
    price_sensitivity=Normal(mean=1.0, sd=0.3, low=0.0),
    portion_preference=Normal(mean=0.4, sd=0.3, low=-1.0, high=1.0),
    visit_probability=Beta(a=3.0, b=2.0),
    arrival_minute=Normal(mean=12.5 * 60, sd=30),
    arrival_spread=Normal(mean=20, sd=5, low=0.0),
)

STUDENT = SegmentConfig(
    name="student",
    share=0.18,
    sweet_savoury=Normal(mean=0.6, sd=0.3, low=-1.0, high=1.0),
    category_affinity={
        FlavorCategory.CHOCOLATE: _affinity(0.6),
        FlavorCategory.CARAMEL: _affinity(0.3),
    },
    allergen_prevalence=ALLERGEN_PREVALENCE,
    price_sensitivity=Normal(mean=1.8, sd=0.4, low=0.0),
    portion_preference=Normal(mean=0.3, sd=0.3, low=-1.0, high=1.0),
    visit_probability=Beta(a=2.0, b=3.0),
    arrival_minute=Normal(mean=15.5 * 60, sd=90),
    arrival_spread=Normal(mean=45, sd=15, low=0.0),
)

REGULAR = SegmentConfig(
    name="regular",
    share=0.12,
    sweet_savoury=Normal(mean=0.3, sd=0.4, low=-1.0, high=1.0),
    fruitiness=Beta(a=3.0, b=2.0),
    pickiness=Normal(mean=3.0, sd=0.5, low=0.0),
    category_affinity={
        FlavorCategory.FRUIT: _affinity(0.4),
        FlavorCategory.SPICE: _affinity(0.4),
        FlavorCategory.NUT: _affinity(0.3),
    },
    allergen_prevalence=ALLERGEN_PREVALENCE,
    price_sensitivity=Normal(mean=0.4, sd=0.2, low=0.0),
    bakery_bias={Bakery.GRANDMAS: Normal(mean=0.8, sd=0.4)},
    visit_probability=Beta(a=3.0, b=3.0),
    arrival_minute=Normal(mean=10.5 * 60, sd=120),
    arrival_spread=Normal(mean=60, sd=20, low=0.0),
)

AFTER_WORK = SegmentConfig(
    name="after_work",
    share=0.12,
    sweet_savoury=Normal(mean=-0.1, sd=0.4, low=-1.0, high=1.0),
    category_affinity={
        FlavorCategory.SAVOURY: _affinity(0.4),
        FlavorCategory.CHEESE: _affinity(0.3),
    },
    allergen_prevalence=ALLERGEN_PREVALENCE,
    price_sensitivity=Normal(mean=1.0, sd=0.3, low=0.0),
    portion_preference=Normal(mean=0.6, sd=0.3, low=-1.0, high=1.0),
    visit_probability=Beta(a=3.0, b=3.0),
    arrival_minute=Normal(mean=17.75 * 60, sd=40),
    arrival_spread=Normal(mean=25, sd=8, low=0.0),
)


CORE_SEGMENTS: list[SegmentConfig] = [COMMUTER, LUNCH_WORKER, STUDENT, REGULAR, AFTER_WORK]


def _allergens(**overrides: float) -> dict[Allergen, float]:
    """Shared prevalence with per-segment overrides, e.g. `_allergens(dairy=0.9)`."""
    rates = dict(ALLERGEN_PREVALENCE)
    rates.update({Allergen(name): p for name, p in overrides.items()})
    return rates


def _sweet(mean: float, sd: float = 0.4) -> Normal:
    return Normal(mean=mean, sd=sd, low=-1.0, high=1.0)


def _price(mean: float, sd: float = 0.3) -> Normal:
    return Normal(mean=mean, sd=sd, low=0.0)


def _portion(mean: float, sd: float = 0.3) -> Normal:
    return Normal(mean=mean, sd=sd, low=-1.0, high=1.0)


def _pickiness(mean: float, sd: float = 0.5) -> Normal:
    return Normal(mean=mean, sd=sd, low=0.0)


def _arrival(hour: float, sd_minutes: float) -> Normal:
    return Normal(mean=hour * 60, sd=sd_minutes)


# Shares are relative weights (the population normalises them), so these
# extras sit alongside the core five, which sum to 1.0.
EXTRA_SEGMENTS: list[SegmentConfig] = [
    SegmentConfig(
        name="early_shift_nurse",
        share=0.02,
        sweet_savoury=_sweet(0.0),
        bitterness=Beta(a=4.0, b=2.0),
        category_affinity={
            FlavorCategory.COFFEE: _affinity(0.5),
            FlavorCategory.SAVOURY: _affinity(0.3),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(1.0),
        portion_preference=_portion(0.2),
        visit_probability=Beta(a=4.0, b=2.0),
        arrival_minute=_arrival(6.5, 45),
    ),
    SegmentConfig(
        name="remote_worker",
        share=0.03,
        sweet_savoury=_sweet(0.3),
        pickiness=_pickiness(2.0),
        category_affinity={
            FlavorCategory.COFFEE: _affinity(0.5),
            FlavorCategory.NUT: _affinity(0.3),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(0.9),
        portion_preference=_portion(0.0),
        visit_probability=Beta(a=4.0, b=3.0),
        arrival_minute=_arrival(10.0, 60),
    ),
    SegmentConfig(
        name="tourist",
        share=0.03,
        sweet_savoury=_sweet(0.4, 0.5),
        category_affinity={
            FlavorCategory.CARAMEL: _affinity(0.3),
            FlavorCategory.FRUIT: _affinity(0.3),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(0.3),
        portion_preference=_portion(0.2),
        bakery_bias={Bakery.GRANDMAS: Normal(mean=0.4, sd=0.3)},
        visit_probability=Beta(a=1.0, b=6.0),
        arrival_minute=_arrival(11.5, 100),
    ),
    SegmentConfig(
        name="gym_goer",
        share=0.02,
        sweet_savoury=_sweet(-0.3),
        category_affinity={
            FlavorCategory.SAVOURY: _affinity(0.3),
            FlavorCategory.NUT: _affinity(0.4),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(1.1),
        portion_preference=_portion(-0.4),
        visit_probability=Beta(a=4.0, b=3.0),
        arrival_minute=_arrival(8.5, 60),
    ),
    SegmentConfig(
        name="parent_with_toddler",
        share=0.03,
        sweet_savoury=_sweet(0.5),
        category_affinity={
            FlavorCategory.CHOCOLATE: _affinity(0.4),
            FlavorCategory.FRUIT: _affinity(0.3),
        },
        allergen_prevalence=_allergens(dairy=0.12),
        price_sensitivity=_price(1.4),
        portion_preference=_portion(0.1),
        visit_probability=Beta(a=3.0, b=3.0),
        arrival_minute=_arrival(10.0, 50),
    ),
    SegmentConfig(
        name="retiree",
        share=0.03,
        sweet_savoury=_sweet(0.4, 0.3),
        pickiness=_pickiness(2.5),
        category_affinity={
            FlavorCategory.FRUIT: _affinity(0.5),
            FlavorCategory.SPICE: _affinity(0.3),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(0.8),
        portion_preference=_portion(-0.3),
        bakery_bias={Bakery.GRANDMAS: Normal(mean=0.6, sd=0.3)},
        visit_probability=Beta(a=4.0, b=3.0),
        arrival_minute=_arrival(10.0, 60),
    ),
    SegmentConfig(
        name="office_party_buyer",
        share=0.01,
        sweet_savoury=_sweet(0.3),
        category_affinity={
            FlavorCategory.CHOCOLATE: _affinity(0.3),
            FlavorCategory.CHEESE: _affinity(0.2),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(0.5),
        portion_preference=_portion(1.0),
        visit_probability=Beta(a=1.0, b=8.0),
        arrival_minute=_arrival(9.5, 40),
    ),
    SegmentConfig(
        name="dessert_enthusiast",
        share=0.02,
        sweet_savoury=_sweet(0.8, 0.2),
        pickiness=_pickiness(2.5),
        category_affinity={
            FlavorCategory.CHOCOLATE: _affinity(0.5),
            FlavorCategory.CARAMEL: _affinity(0.5),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(0.5),
        portion_preference=_portion(0.5),
        visit_probability=Beta(a=3.0, b=3.0),
        arrival_minute=_arrival(15.0, 90),
    ),
    SegmentConfig(
        name="health_conscious",
        share=0.02,
        sweet_savoury=_sweet(-0.1),
        category_affinity={
            FlavorCategory.FRUIT: _affinity(0.3),
            FlavorCategory.NUT: _affinity(0.4),
        },
        allergen_prevalence=_allergens(gluten=0.15, dairy=0.15),
        price_sensitivity=_price(0.7),
        portion_preference=_portion(-0.5),
        visit_probability=Beta(a=3.0, b=3.0),
        arrival_minute=_arrival(9.0, 60),
    ),
    SegmentConfig(
        name="vegan",
        share=0.02,
        sweet_savoury=_sweet(0.2),
        category_affinity={
            FlavorCategory.FRUIT: _affinity(0.4),
            FlavorCategory.SPICE: _affinity(0.3),
        },
        allergen_prevalence=_allergens(dairy=0.9, egg=0.9),
        price_sensitivity=_price(0.8),
        portion_preference=_portion(0.0),
        visit_probability=Beta(a=3.0, b=4.0),
        arrival_minute=_arrival(11.0, 90),
    ),
    SegmentConfig(
        name="coeliac",
        share=0.01,
        sweet_savoury=_sweet(0.2),
        pickiness=_pickiness(3.5),
        category_affinity={
            FlavorCategory.NUT: _affinity(0.3),
            FlavorCategory.FRUIT: _affinity(0.3),
        },
        allergen_prevalence=_allergens(gluten=0.95),
        price_sensitivity=_price(0.6),
        portion_preference=_portion(0.0),
        visit_probability=Beta(a=3.0, b=4.0),
        arrival_minute=_arrival(10.5, 90),
    ),
    SegmentConfig(
        name="late_night_studier",
        share=0.02,
        sweet_savoury=_sweet(0.5),
        bitterness=Beta(a=4.0, b=2.0),
        category_affinity={
            FlavorCategory.COFFEE: _affinity(0.6),
            FlavorCategory.CHOCOLATE: _affinity(0.4),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(1.7),
        portion_preference=_portion(0.2),
        visit_probability=Beta(a=3.0, b=3.0),
        arrival_minute=_arrival(20.0, 60),
    ),
    SegmentConfig(
        name="weekend_brunch_group",
        share=0.02,
        sweet_savoury=_sweet(0.2, 0.5),
        category_affinity={
            FlavorCategory.SAVOURY: _affinity(0.3),
            FlavorCategory.FRUIT: _affinity(0.3),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(0.5),
        portion_preference=_portion(0.4),
        bakery_bias={Bakery.GRANDMAS: Normal(mean=0.3, sd=0.3)},
        visit_probability=Beta(a=2.0, b=4.0),
        arrival_minute=_arrival(11.0, 45),
    ),
    SegmentConfig(
        name="school_run_parent",
        share=0.03,
        sweet_savoury=_sweet(0.2),
        category_affinity={FlavorCategory.COFFEE: _affinity(0.5)},
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(1.1),
        portion_preference=_portion(-0.2),
        visit_probability=Beta(a=4.0, b=2.0),
        arrival_minute=_arrival(8.75, 25),
        arrival_spread=Normal(mean=10, sd=3, low=0.0),
    ),
    SegmentConfig(
        name="construction_crew",
        share=0.02,
        sweet_savoury=_sweet(-0.4),
        category_affinity={
            FlavorCategory.SAVOURY: _affinity(0.6),
            FlavorCategory.CHEESE: _affinity(0.3),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(1.3),
        portion_preference=_portion(0.8),
        visit_probability=Beta(a=4.0, b=2.0),
        arrival_minute=_arrival(6.75, 30),
    ),
    SegmentConfig(
        name="food_critic",
        share=0.01,
        sweet_savoury=_sweet(0.1, 0.5),
        pickiness=_pickiness(4.0),
        category_affinity={
            FlavorCategory.SPICE: _affinity(0.4),
            FlavorCategory.NUT: _affinity(0.3),
            FlavorCategory.FRUIT: _affinity(0.3),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(0.1),
        portion_preference=_portion(0.0),
        bakery_bias={Bakery.GRANDMAS: Normal(mean=0.2, sd=0.3)},
        visit_probability=Beta(a=2.0, b=5.0),
        arrival_minute=_arrival(12.0, 120),
    ),
    SegmentConfig(
        name="bargain_hunter",
        share=0.02,
        sweet_savoury=_sweet(0.3),
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(2.5, 0.4),
        portion_preference=_portion(0.5),
        visit_probability=Beta(a=3.0, b=3.0),
        arrival_minute=_arrival(17.0, 30),
    ),
    SegmentConfig(
        name="after_school_teen",
        share=0.02,
        sweet_savoury=_sweet(0.7, 0.3),
        category_affinity={
            FlavorCategory.CHOCOLATE: _affinity(0.5),
            FlavorCategory.CARAMEL: _affinity(0.4),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(1.9),
        portion_preference=_portion(0.4),
        visit_probability=Beta(a=3.0, b=3.0),
        arrival_minute=_arrival(15.75, 30),
    ),
    SegmentConfig(
        name="business_meeting_host",
        share=0.01,
        sweet_savoury=_sweet(0.0),
        category_affinity={
            FlavorCategory.COFFEE: _affinity(0.4),
            FlavorCategory.SAVOURY: _affinity(0.3),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(0.3),
        portion_preference=_portion(0.6),
        visit_probability=Beta(a=2.0, b=5.0),
        arrival_minute=_arrival(9.0, 40),
    ),
    SegmentConfig(
        name="loyal_grandmas_fan",
        share=0.03,
        sweet_savoury=_sweet(0.3),
        pickiness=_pickiness(3.5),
        category_affinity={
            FlavorCategory.FRUIT: _affinity(0.3),
            FlavorCategory.SPICE: _affinity(0.4),
        },
        allergen_prevalence=ALLERGEN_PREVALENCE,
        price_sensitivity=_price(0.3),
        portion_preference=_portion(0.1),
        bakery_bias={Bakery.GRANDMAS: Normal(mean=1.2, sd=0.3)},
        visit_probability=Beta(a=5.0, b=2.0),
        arrival_minute=_arrival(10.0, 90),
    ),
]

ALL_SEGMENTS: list[SegmentConfig] = CORE_SEGMENTS + EXTRA_SEGMENTS


def default_population(size: int = 400) -> PopulationConfig:
    return PopulationConfig(size=size, segments=CORE_SEGMENTS)


def extended_population(size: int = 400) -> PopulationConfig:
    """The core five plus the 20 extra segments."""
    return PopulationConfig(size=size, segments=ALL_SEGMENTS)
