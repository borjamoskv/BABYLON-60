{-# LANGUAGE GADTs, KindSignatures, DataKinds, OverloadedStrings #-}
{-|
Module      : CategoricalPrimitives896
Description : C5-REAL Formal Haskell Type System for the 896 Categorical Logic Primitives
Kernel      : MOSKV-1 APEX
-}

module CategoricalPrimitives896 where

import Data.Text (Text)

-- | The 8 Orthogonal Categorical Logic Domains
data DomainId = D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8
  deriving (Eq, Show, Enum, Bounded)

-- | Classification of Primitives
data PrimitiveType
  = Structure
  | LimitsColimits
  | FunctorialAdjunctions
  | MonoidalEnriched
  | CategoricalLogicTopos
  | CollisionObstruction
  | Antipatterns
  | FiberedCompatibilityMetrics
  deriving (Eq, Show)

-- | Strongly-typed Categorical Primitive representation
data Primitive = Primitive
  { primId                  :: !Int
  , primCode                :: !Text
  , primDomain              :: !DomainId
  , primType                :: !PrimitiveType
  , primCategory            :: !Text
  , primDescription         :: !Text
  , primFormalProofInvariant :: !Text
  } deriving (Eq, Show)

-- | Morphism Cost Functional mu(alpha) in N_infinity
data Cost = Finite !Double | Infinity
  deriving (Eq, Show)

-- | Morphism Composition Cost Law: mu(b o a) <= mu(a) + mu(b) + delta_circ
addCost :: Cost -> Cost -> Double -> Cost
addCost (Finite c1) (Finite c2) delta = Finite (c1 + c2 + delta)
addCost _ _ _                         = Infinity
