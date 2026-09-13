import time
import subprocess
import os

LEAN_TEMPLATE = """
set_option maxRecDepth 1000000
set_option maxHeartbeats 10000000

inductive Action where
  | WriteBegin
  | WriteEnd
  | Read
  deriving Repr, DecidableEq

structure SeqlockEvent where
  thread : Nat
  seq    : Nat
  action : Action
  deriving Repr, DecidableEq

def validateTransition (_currentSeq : Nat) (inWrite : Bool) (event : SeqlockEvent) : Option (Nat × Bool) :=
  match event.action with
  | Action.WriteBegin =>
      if inWrite then none else if event.seq % 2 == 0 then none else some (event.seq, true)
  | Action.WriteEnd =>
      if not inWrite then none else if event.seq % 2 != 0 then none else some (event.seq, false)
  | Action.Read =>
      if inWrite then none else if event.seq % 2 != 0 then none else some (event.seq, inWrite)

def isValidTrace (trace : List SeqlockEvent) (currentSeq : Nat) (inWrite : Bool) : Bool :=
  match trace with
  | [] => true
  | e :: es =>
      match validateTransition currentSeq inWrite e with
      | none => false
      | some (newSeq, newInWrite) => isValidTrace es newSeq newInWrite

def stress_trace : List SeqlockEvent := [
{events}
]

theorem valid_stress_trace : isValidTrace stress_trace 0 false = true := by
  decide
"""

def generate_events(n):
    events = []
    seq = 1
    for i in range(n):
        if i % 2 == 0:
            events.append(f"  {{ thread := 1, seq := {seq}, action := Action.WriteBegin }}")
        else:
            events.append(f"  {{ thread := 1, seq := {seq+1}, action := Action.WriteEnd }}")
            seq += 2
    return ",\n".join(events)

def run_stress_test(n):
    events_str = generate_events(n)
    lean_code = LEAN_TEMPLATE.format(events=events_str)
    
    file_path = f"scripts/c5_demos/BabylonTraceStress_{n}.lean"
    with open(file_path, "w") as f:
        f.write(lean_code)
    
    print(f"[*] Ejecutando test de estrés con N={n} eventos...")
    start_time = time.time()
    result = subprocess.run(["lean", file_path], capture_output=True, text=True)
    end_time = time.time()
    
    duration = end_time - start_time
    if result.returncode == 0:
        print(f"[EXITO] N={n} | Tiempo: {duration:.3f}s")
    else:
        print(f"[FALLO] N={n} | Exit Code: {result.returncode}")
        print(f"Stderr: {result.stderr[:200]}...")
    
    # Cleanup to save space
    if os.path.exists(file_path):
        os.remove(file_path)

if __name__ == "__main__":
    os.makedirs("scripts/c5_demos", exist_ok=True)
    print("--- INICIANDO TEST DE ESTRÉS (AST EXPLOSION) EN LEAN 4 ---")
    for n in [100, 1000, 5000, 10000, 20000]:
        run_stress_test(n)
