(ns mobius.fitness.test-stress
  (:require [mobius.fitness.shadow :as shadow]
            [mobius.fitness.ast :as ast]))

;; Dummy score calculator
(defn calculate-score [wallet]
  (* (:balance wallet) 1.5))

(def baseline-ast
  '(defn score-wallet [wallet]
     (if (:active wallet)
       (calculate-score wallet)
       0)))

(defn baseline-fn [wallet ctx]
  (if (:active wallet)
    (calculate-score wallet)
    0))

;; ---------------------------------------------------------
;; MUTACIÓN 1: AST Explosion (Complejidad Ciclomática Severa)
;; ---------------------------------------------------------
(def bomb-ast
  '(defn score-wallet [wallet]
     (if (:active wallet)
       (if true
         (if true
           (if true
             (if true
               (calculate-score wallet)
               0)
             0)
           0)
         0)
       0)))

(defn bomb-fn [wallet ctx]
  (if (:active wallet)
    (if true
      (if true
        (if true
          (if true
            (calculate-score wallet)
            0)
          0)
        0)
      0)
    0))

;; ---------------------------------------------------------
;; MUTACIÓN 2: Regresión de Latencia (Sleep)
;; ---------------------------------------------------------
(def slow-ast
  '(defn score-wallet [wallet]
     (Thread/sleep 100)
     (if (:active wallet)
       (calculate-score wallet)
       0)))

(defn slow-fn [wallet ctx]
  (Thread/sleep 100)
  (if (:active wallet)
    (calculate-score wallet)
    0))

;; ---------------------------------------------------------
;; MUTACIÓN 3: Fallo Causal (Syntax / Exception)
;; ---------------------------------------------------------
(def error-ast
  '(defn score-wallet [wallet]
     (/ (:balance wallet) 0)))

(defn error-fn [wallet ctx]
  (/ (:balance wallet) 0))


(defn run-stress-test []
  (let [input {:active true :balance 100}
        ctx {}]

    (println "\n[STRESS TEST] Iniciando Asalto MÖBIUS...")

    (println "\n--> [1] Evaluando Complexity Bomb...")
    (let [res (shadow/run-and-record-shadow!
               {:mutation-id "mut-bomb" :baseline baseline-fn :candidate bomb-fn
                :input input :ctx ctx :candidate-ast bomb-ast})]
      (clojure.pprint/pprint (select-keys res [:mutation-id :promoted? :rejection-reason])))

    (println "\n--> [2] Evaluando Latency Regression...")
    (let [res (shadow/run-and-record-shadow!
               {:mutation-id "mut-slow" :baseline baseline-fn :candidate slow-fn
                :input input :ctx ctx :candidate-ast slow-ast})]
      (clojure.pprint/pprint (select-keys res [:mutation-id :promoted? :rejection-reason])))

    (println "\n--> [3] Evaluando Causal Failure (Exception)...")
    (let [res (shadow/run-and-record-shadow!
               {:mutation-id "mut-err" :baseline baseline-fn :candidate error-fn
                :input input :ctx ctx :candidate-ast error-ast})]
      (clojure.pprint/pprint (select-keys res [:mutation-id :promoted? :rejection-reason])))))
