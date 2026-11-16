import Lean
import __MOD__
open Lean Elab Command Meta

/-- Teoremas: solo propext y Quot.sound (lo que hoy fijan los #guard_msgs).
    Definiciones: además Classical.choice (entra vía instancias de core en IO/String). -/
def thmAllowed : List Name := [``propext, ``Quot.sound]
def defAllowed : List Name := [``propext, ``Quot.sound, ``Classical.choice]

/-- Cierre transitivo de constantes usadas por `n`. -/
partial def closure (env : Environment) (n : Name) (seen : NameSet := {}) : NameSet := Id.run do
  let mut seen := seen
  let mut stack := #[n]
  while h : stack.size > 0 do
    let c := stack.back
    stack := stack.pop
    if seen.contains c then continue
    seen := seen.insert c
    if let some ci := env.find? c then
      for d in ci.getUsedConstantsAsSet do
        unless seen.contains d do stack := stack.push d
  return seen

#eval show CommandElabM Unit from do
  let env ← getEnv
  let target : Name := `__MOD__
  let mut bad : Array (Name × Name) := #[]
  let mut trustedRuntime : Array (Name × Name) := #[]
  let mut nDecl := 0
  let mut nThm := 0
  for (n, ci) in env.constants.map₁.toList do
    let some idx := env.getModuleIdxFor? n | continue
    let some mod := env.header.moduleNames[idx.toNat]? | continue
    unless mod == target do continue
    nDecl := nDecl + 1
    let isThm := ci matches .thmInfo _
    if isThm then nThm := nThm + 1
    let allowed := if isThm then thmAllowed else defAllowed
    for a in (← liftCoreM <| collectAxioms n) do
      unless allowed.contains a do bad := bad.push (n, a)
    -- Teoremas que mencionan código con implementación de runtime distinta del modelo del kernel
    if isThm then
      for d in (closure env n).toList do
        let some idx' := env.getModuleIdxFor? d | continue
        let some mod' := env.header.moduleNames[idx'.toNat]? | continue
        unless mod' == target do continue
        if (Compiler.getImplementedBy? env d).isSome || isExtern env d then
          trustedRuntime := trustedRuntime.push (n, d)
  if nDecl == 0 then throwError m!"FAIL_AXIOM_AUDIT {target}: 0 declaraciones (filtro roto)"
  unless trustedRuntime.isEmpty do
    logWarning m!"WARN_RUNTIME_GAP {target} ({trustedRuntime.size}): {trustedRuntime.toList.take 10}"
  if bad.isEmpty then
    logInfo m!"PASS_AXIOM_AUDIT {target} decls={nDecl} thms={nThm}"
  else
    throwError m!"FAIL_AXIOM_AUDIT {target} ({bad.size}): {bad.toList.take 20}"
