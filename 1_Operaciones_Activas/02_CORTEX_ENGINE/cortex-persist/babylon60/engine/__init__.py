# CORTEX ENGINE FACADE
# Auto-generated to maintain compatibility after structural mitosis.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core.cortex_engine import AsyncCortexEngine as AsyncCortexEngine
    from .core.cortex_engine import CortexEngine as CortexEngine

_SWARM_MODULES = {
    "agent_mixin",
    "aleph_omega",
    "auth",
    "auth_gateway",
    "autocurative_agent",
    "autopoietic_agent",
    "enrichment_worker",
    "entropy_daemon",
    "exergy_agent",
    "exergy_daemon",
    "legion",
    "legion_vectors",
    "legion_vectors_plan",
    "nemesis_agent",
    "omega_daemon",
    "phoenix_omega",
    "squadrons",
    "swarm_10k",
    "test_autopoietic_agent",
    "trust_registry",
}

_DEFERRED_ATTRIBUTES = {
    "AsyncCortexEngine": ".core.cortex_engine",
    "CortexEngine": ".core.cortex_engine",
}


def __getattr__(name: str):
    if name in _SWARM_MODULES:
        import importlib

        return importlib.import_module(f"cortex.swarm.{name}")
    if name in _DEFERRED_ATTRIBUTES:
        import importlib

        mod = importlib.import_module(_DEFERRED_ATTRIBUTES[name], __name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + list(_SWARM_MODULES) + list(_DEFERRED_ATTRIBUTES.keys()))


from babylon60.extensions.evo import (
    _autocurative_config as _autocurative_config,
)
from babylon60.extensions.evo import (
    _autocurative_helper as _autocurative_helper,
)
from babylon60.extensions.evo import (
    _autocurative_state as _autocurative_state,
)
from babylon60.extensions.evo import (
    _autopoietic_helper as _autopoietic_helper,
)
from babylon60.extensions.evo import (
    _autopoietic_state as _autopoietic_state,
)
from babylon60.extensions.evo import (
    _genome_mutator as _genome_mutator,
)
from babylon60.extensions.evo import (
    _genome_tree_helper as _genome_tree_helper,
)
from babylon60.extensions.evo import (
    _genome_types as _genome_types,
)
from babylon60.extensions.evo import (
    _mutation_projectors as _mutation_projectors,
)
from babylon60.extensions.evo import (
    autopoiesis as autopoiesis,
)
from babylon60.extensions.evo import (
    decalcifier as decalcifier,
)
from babylon60.extensions.evo import (
    evaporator as evaporator,
)
from babylon60.extensions.evo import (
    evolution_metrics as evolution_metrics,
)
from babylon60.extensions.evo import (
    evolution_types as evolution_types,
)
from babylon60.extensions.evo import (
    genome as genome,
)
from babylon60.extensions.evo import (
    growth as growth,
)
from babylon60.extensions.evo import (
    healing_stack as healing_stack,
)
from babylon60.extensions.evo import (
    reaper as reaper,
)
from babylon60.extensions.evo import (
    repair_strategies as repair_strategies,
)

from .core import (
    _engine_connection as _engine_connection,
)
from .core import (
    _engine_delegates as _engine_delegates,
)
from .core import (
    bifurcation_engine as bifurcation_engine,
)
from .core import (
    context_cache as context_cache,
)
from .core import (
    distributed_ledger as distributed_ledger,
)
from .core import (
    embedding_engine as embedding_engine,
)
from .core import (
    engine as engine,
)
from .core import (
    evolution_engine as evolution_engine,
)
from .core import (
    evolution_ledger as evolution_ledger,
)
from .core import (
    fact_store_core as fact_store_core,
)
from .core import (
    memory_mixin as memory_mixin,
)
from .core import (
    mutation_engine as mutation_engine,
)
from .core import (
    physics as physics,
)
from .core import (
    rollback_engine as rollback_engine,
)
from .core import (
    runtime_kernel as runtime_kernel,
)
from .core import (
    snapshots as snapshots,
)
from .core import (
    store_mixin as store_mixin,
)
from .core import (
    store_mutation as store_mutation,
)
from .core import (
    store_quarantine_mixin as store_quarantine_mixin,
)
from .core import (
    store_validation as store_validation,
)
from .core import (
    store_validators as store_validators,
)
from .core import (
    tips as tips,
)
from .core import (
    tuning_store as tuning_store,
)
from .core import (
    ultrathink_physics as ultrathink_physics,
)
from .flow import (
    arbiter_bridge as arbiter_bridge,
)
from .flow import (
    bridge_guard as bridge_guard,
)
from .flow import (
    cascade_router as cascade_router,
)
from .flow import (
    causal_scheduler as causal_scheduler,
)
from .flow import (
    causality as causality,
)
from .flow import (
    causality_models as causality_models,
)
from .flow import (
    checkpoint as checkpoint,
)
from .flow import (
    consensus as consensus,
)
from .flow import (
    encb_router as encb_router,
)
from .flow import (
    execution_ledger as execution_ledger,
)
from .flow import (
    guard_adapters as guard_adapters,
)
from .flow import (
    guard_integration_patch as guard_integration_patch,
)
from .flow import (
    guard_pipeline as guard_pipeline,
)
from .flow import (
    lock as lock,
)
from .flow import (
    rim_latent_blocks as rim_latent_blocks,
)
from .flow import (
    saga_protocol as saga_protocol,
)
from .flow import (
    storage_guard as storage_guard,
)
from .meta import (
    _autopoietic_oracle as _autopoietic_oracle,
)
from .meta import (
    cognitive as cognitive,
)
from .meta import (
    cognitive_arbiter as cognitive_arbiter,
)
from .meta import (
    forgetting_oracle as forgetting_oracle,
)
from .meta import (
    meta_arbiter as meta_arbiter,
)
from .meta import (
    meta_arbiter_kernel as meta_arbiter_kernel,
)
from .meta import (
    meta_arbiter_types as meta_arbiter_types,
)
from .meta import (
    metabolism as metabolism,
)
from .meta import (
    metacognition as metacognition,
)
from .meta import (
    metadata_engine as metadata_engine,
)
from .meta import (
    nemesis as nemesis,
)
from .meta import (
    psychology as psychology,
)
from .meta import (
    right_brain as right_brain,
)
from .meta import (
    sovereign_arbiter as sovereign_arbiter,
)
from .meta import (
    vision_reasoner as vision_reasoner,
)
