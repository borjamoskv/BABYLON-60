-- C5-REAL EXERGY CERTIFIED
-- INV-3 POPPER: All theoretical invariants must be empirically falsifiable. Continuous metaphors are rejected.
-- INV-1 DISCRETE: Strict discrete state space. No continuous variables allowed in semantic evaluation.
{-# LANGUAGE GADTs, KindSignatures, DataKinds, OverloadedStrings #-}
{-|
Module      : CategoricalPrimitives
Description : C5-REAL Formal Haskell Type System for the 3 Fundamental Categorical Primitives
Kernel      : MOSKV-1 APEX
-}

module CategoricalPrimitives where

import Data.Text (Text)
import Data.Word (Word64)

-- | The 3 Fundamental Categorical Logic Primitives (Isomorfismo Aristotélico)
-- Mapeadas directamente a silicio: Dynamis (Potencia), Entelecheia (Acto), Primum Movens (Límite).
data FundamentalPrimitive
  = Dynamis        -- ^ Objeto (Carga Estocástica sin colapsar)
  | Entelecheia    -- ^ Morfismo (Colapso Determinista, Disipación de Anergía)
  | PrimumMovens   -- ^ Adjunción/Límite (Barrera de Hardware / Fail-Stop Sentinel)
  deriving (Eq, Show, Enum, Bounded)

-- | Strongly-typed Categorical Primitive representation
-- Redundancies eliminated: O(1) representation mapped directly to the 3 fundamental states.
-- Designed for 64-byte Cache-Line Coherence in SharedManifest FFI (C-ABI).
-- Text fields replaced by pure functions to guarantee absolute Zero Anergía.
data Primitive = Primitive
  { primKind       :: !FundamentalPrimitive
  -- 32-byte Cryptographic Anchor (Blake3/SHA256 SCITT) mapped as unboxed Word64
  , primHashPart1  :: !Word64
  , primHashPart2  :: !Word64
  , primHashPart3  :: !Word64
  , primHashPart4  :: !Word64
  } deriving (Eq, Show)

-- | Pure function to derive Description without memory overhead (Zero Anergía)
getPrimDescription :: FundamentalPrimitive -> Text
getPrimDescription Dynamis      = "Objeto (Carga Estocástica sin colapsar)"
getPrimDescription Entelecheia  = "Morfismo (Colapso Determinista, Disipación de Anergía)"
getPrimDescription PrimumMovens = "Adjunción/Límite (Barrera de Hardware / Fail-Stop Sentinel)"

-- | Pure function to derive Formal Proof Invariant without memory overhead
getPrimFormalProofInvariant :: FundamentalPrimitive -> Text
getPrimFormalProofInvariant Dynamis      = "INV-CAUSAL: Potencia no resuelta"
getPrimFormalProofInvariant Entelecheia  = "INV-CAUSAL: Acto resuelto y atestado"
getPrimFormalProofInvariant PrimumMovens = "INV-CAUSAL: Motor Inmóvil Determinista"

-- | Morphism Cost Functional mu(alpha) in strictly discrete N_infinity
data Cost = Finite !Word64 | Infinity
  deriving (Eq, Show)

-- | Límite de Landauer: El colapso de Dynamis a Entelecheia exige disipación térmica.
-- mu(b o a) <= mu(a) + mu(b) + delta_circ (Anergía de transición)
addCost :: Cost -> Cost -> Word64 -> Cost
addCost (Finite c1) (Finite c2) delta = Finite (c1 + c2 + delta)
addCost _ _ _                         = Infinity
