(ns mobius.fitness.test-shadow
  (:require [mobius.fitness.shadow :as shadow]
            [mobius.fitness.ast :as ast]))

;; Dummy score calculator (efecto puro)
(defn calculate-score [wallet]
  (* (:balance wallet) 1.5))

;; ---------------------------------------------------------
;; 1. ENSAYO POSITIVO: Optimización
;; ---------------------------------------------------------

(def baseline-ast
  '(defn score-wallet [wallet]
     (if (:active wallet)
       (calculate-score wallet)
       0)))

(defn baseline-fn [wallet ctx]
  (if (:active wallet)
    (calculate-score wallet)
    0))

(def candidate-ast
  '(defn score-wallet [wallet]
     (when (:active wallet)
       (calculate-score wallet))))

(defn candidate-fn [wallet ctx]
  (when (:active wallet)
    (calculate-score wallet)))

;; ---------------------------------------------------------
;; 2. ENSAYO NEGATIVO: Mutación Degradante (Complejidad Innecesaria)
;; ---------------------------------------------------------

(def degrading-ast
  '(defn score-wallet [wallet]
     (cond
       (:active wallet) (calculate-score wallet)
       (not (:active wallet)) 0
       :else 0)))

(defn degrading-fn [wallet ctx]
  (cond
    (:active wallet) (calculate-score wallet)
    (not (:active wallet)) 0
    :else 0))


(defn run-tests []
  (let [input {:active true :balance 100}
        ctx {}]

    (println "\n=== ENSAYO 1: Mutación Optimizada (if -> when) ===")
    (let [res (shadow/run-and-record-shadow!
               {:mutation-id "mut-opt-1"
                :baseline baseline-fn
                :candidate candidate-fn
                :input input
                :ctx ctx
                :candidate-ast candidate-ast})]
      (clojure.pprint/pprint
       (select-keys res [:mutation-id :fitness-delta :promoted? :rejection-reason])))

    (println "\n=== ENSAYO 2: Mutación Degradante (cond innecesario) ===")
    (let [res (shadow/run-and-record-shadow!
               {:mutation-id "mut-deg-2"
                :baseline baseline-fn
                :candidate degrading-fn
                :input input
                :ctx ctx
                :candidate-ast degrading-ast})]
      (clojure.pprint/pprint
       (select-keys res [:mutation-id :fitness-delta :promoted? :rejection-reason])))))
