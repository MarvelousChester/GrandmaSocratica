"""A starting population for the sim, hand-tuned to be plausible.

Four segments whose habits pull against the two menus differently: commuters
want cheap coffee early, the lunch crowd wants savoury and filling, students
want sugar on a budget, and regulars pay up for grandma's.
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
    share=0.35,
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
    share=0.30,
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
    share=0.20,
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
    share=0.15,
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


def default_population(size: int = 400) -> PopulationConfig:
    return PopulationConfig(
        size=size, segments=[COMMUTER, LUNCH_WORKER, STUDENT, REGULAR]
    )
