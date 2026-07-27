(* proof/coq/Babylon.v *)
(* BABYLON-60 C5-REAL Formal Ontology *)

Require Import QArith.
Require Import String.
Require Import List.

(* 1. Dominio de Tipos (Type Domain) *)
Inductive B60Type : Type :=
  | I64 : B60Type
  | Time : B60Type
  | F60 : B60Type.

(* El tipo F60 se modela matemáticamente como un número Racional Exacto (Q) 
   para garantizar la ausencia de desbordamientos IEEE-754. *)
Definition F60_Val := Q.

(* 2. El Reloj Lógico (Desacoplado del tiempo físico) *)
Record LogicalClock : Type := mkClock {
  tick : nat
}.

(* 3. Grafo Causal (DAG Ledger) *)
Inductive Event : Type :=
  | mkEvent (id : string) (parents : list string) (clk : LogicalClock) (payload : string).

(* 4. Tupla de Estado Global Γ *)
Record State : Type := mkState {
  regs : nat -> option F60_Val;
  ledger : list Event;
  clock : LogicalClock
}.

(* 5. Semántica de Pasos Pequeños (Small-Step Transitions) *)
(* Define CÓMO la máquina avanza de manera determinista. *)
Inductive Step : State -> State -> Prop :=
  | step_assign : forall (s : State) (r : nat) (v : F60_Val),
      Step s (mkState 
                (fun x => if Nat.eqb x r then Some v else (regs s) x) 
                (ledger s) 
                (clock s))
      
  | step_fork : forall (s : State) (child : string),
      (* Invariante: Un FORK siempre avanza el reloj causal *)
      Step s (mkState 
                (regs s) 
                (ledger s) 
                (mkClock (S (tick (clock s))))).
