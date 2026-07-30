(ns mobius.ledger.adversary
  (:require [mobius.ledger.tensor :as tensor]
            [mobius.fitness.shadow :as shadow]))

;; ---------------------------------------------------------
;; 1. SHADOW-METRIC ATTACKER (Observador Adversarial)
;; ---------------------------------------------------------
;; Su objetivo es encontrar "puntos ciegos" (blindspots) en la métrica g_ij:
;; vectores de mutación v que tienen un coste geodésico bajo pero causan fallos reales.

(defn generate-exploit-vector
  "Genera vectores de mutación optimizados para explotar los valles de coste de g_ij.
   Busca combinaciones de operadores con el menor peso acumulado en el tensor métrico."
  [g operators]
  (let [sorted-ops (sort-by (fn [op] (get-in g [op op] 0.0)) operators)
        best-op (first sorted-ops)
        second-op (second sorted-ops)]
    ;; Diseña un vector de mutación agresivo concentrado en los operadores 'baratos'
    {best-op 3.0
     second-op 2.0}))

(defn audit-metric-blindspots
  "Evalúa si la métrica g_ij está desalineada con la realidad causal.
   Si el coste geodésico es bajo (< 0.5) pero la evaluación real en shadow mode falla,
   hemos detectado un colapso de la métrica (blindspot)."
  [ledger s operators candidate-fn input ctx]
  (let [g (tensor/metric-tensor ledger s operators)
        attack-vector (generate-exploit-vector g operators)
        geodesic-cost (tensor/geodesic-drift-cost ledger s operators attack-vector)
        
        ;; Ejecutamos en Shadow Mode para ver si el exploit rompe el sistema
        shadow-run (shadow/evaluate-candidate candidate-fn input ctx)
        real-failure? (:error (:result shadow-run))]
    
    {:attack-vector attack-vector
     :geodesic-cost geodesic-cost
     :real-failure? (boolean real-failure?)
     :blindspot? (and (not real-failure?) 
                      (< geodesic-cost 0.15)) ;; Si el coste es casi cero pero...
     :vulnerability-index (if (and real-failure? (< geodesic-cost 0.20))
                            (/ 1.0 (max 0.01 geodesic-cost))
                            0.0)}))

;; ---------------------------------------------------------
;; 2. AUTO-HARDENING (Inmunización del Espacio)
;; ---------------------------------------------------------

(defn harden-metric!
  "Corrige el punto ciego inyectando un trauma sintético (presión negativa)
   en la coordenada explotada del ledger-tensor."
  [ledger-atom s operators vulnerability-report]
  (let [vuln-idx (:vulnerability-index vulnerability-report)
        attack-vector (:attack-vector vulnerability-report)]
    (if (> vuln-idx 1.0)
      (do
        ;; Inflamos artificialmente los valores del ledger para los operadores explotados
        (doseq [[op magnitude] attack-vector]
          (swap! ledger-atom update-in [s :synthetic-hardening op] 
                 (fnil + 0.0) (* magnitude vuln-idx)))
        {:status :hardened
         :inflated-operators (keys attack-vector)
         :vulnerability-index vuln-idx})
      {:status :nominal
       :vulnerability-index vuln-idx})))
