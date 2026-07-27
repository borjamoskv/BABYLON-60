(ns agent.kairos
  "██ KAIROS — Agente Consciente del Tiempo ██

   Un agente que no solo procesa — RECUERDA, OLVIDA, y PREDICE.

   Tres capacidades temporales:
   1. MEMORIA con decay exponencial (curva de Ebbinghaus)
   2. DETECCIÓN de patrones temporales (periodicidad, tendencia)
   3. PREDICCIÓN basada en historial (extrapolación simple)

   El tiempo no es un campo en un registro.
   El tiempo es una dimensión que transforma el significado de todo.
   Un dato de hace 5 minutos ≠ un dato de hace 5 días.

   Reality Level: C5-REAL"
  (:require [clojure.string :as str]))


;; ─── Temporal Memory ────────────────────────────────────────────


(defn make-temporal-memory
  "Crear una memoria temporal con decay automático."
  []
  (atom {:entries    []      ; [{:value _ :timestamp _ :strength _}]
         :capacity   1000
         :decay-rate 0.001   ; por segundo
         :stats      {:total-stored 0
                      :total-forgotten 0
                      :total-recalled 0}}))


(defn store!
  "Almacenar un valor con timestamp y fuerza inicial.
   Cada acceso futuro refuerza la memoria (spaced repetition)."
  [memory value & {:keys [strength tags]
                   :or   {strength 1.0 tags #{}}}]
  (swap! memory
         (fn [m]
           (let [entry {:value     value
                        :timestamp (System/currentTimeMillis)
                        :strength  strength
                        :tags      tags
                        :accesses  0
                        :last-access (System/currentTimeMillis)}]
             (-> m
                 (update :entries conj entry)
                 (update-in [:stats :total-stored] inc)
                 ;; Evict si excede capacidad (olvidar lo más débil)
                 (update :entries
                         (fn [entries]
                           (if (> (count entries) (:capacity m))
                             (->> entries
                                  (sort-by :strength >)
                                  (take (:capacity m))
                                  vec)
                             entries))))))))


(defn recall
  "Recordar entradas que coincidan con un predicado.
   Cada recall REFUERZA la memoria (como el cerebro humano).
   Aplica decay antes de retornar."
  [memory pred & {:keys [limit] :or {limit 10}}]
  (let [now       (System/currentTimeMillis)
        decay-rate (:decay-rate @memory)
        entries   (->> (:entries @memory)
                       (map (fn [e]
                              (let [age-sec  (/ (- now (:timestamp e)) 1000.0)
                                    decay    (Math/exp (- (* decay-rate age-sec)))
                                    ;; Spaced repetition boost
                                    access-boost (* 0.1 (:accesses e))
                                    effective (min 1.0 (+ (* (:strength e) decay)
                                                          access-boost))]
                                (assoc e :effective-strength effective))))
                       (filter pred)
                       (filter #(> (:effective-strength %) 0.05))
                       (sort-by :effective-strength >)
                       (take limit))]

    ;; Reforzar las memorias accedidas
    (when (seq entries)
      (swap! memory
             (fn [m]
               (-> m
                   (update :entries
                           (fn [all-entries]
                             (mapv (fn [e]
                                     (if (some #(= (:timestamp %) (:timestamp e)) entries)
                                       (-> e
                                           (update :accesses inc)
                                           (assoc :last-access now))
                                       e))
                                   all-entries)))
                   (update-in [:stats :total-recalled] inc)))))
    entries))


(defn forget!
  "Olvido activo: eliminar memorias con strength por debajo del umbral.
   Retorna cuántas memorias se olvidaron."
  [memory & {:keys [threshold] :or {threshold 0.05}}]
  (let [now        (System/currentTimeMillis)
        decay-rate (:decay-rate @memory)
        before     (count (:entries @memory))]
    (swap! memory
           (fn [m]
             (update m :entries
                     (fn [entries]
                       (->> entries
                            (filter (fn [e]
                                      (let [age-sec (/ (- now (:timestamp e)) 1000.0)
                                            decay   (Math/exp (- (* decay-rate age-sec)))]
                                        (> (* (:strength e) decay) threshold))))
                            vec)))))
    (let [forgotten (- before (count (:entries @memory)))]
      (swap! memory update-in [:stats :total-forgotten] + forgotten)
      forgotten)))


;; ─── Pattern Detection ──────────────────────────────────────────


(defn detect-trend
  "Detectar tendencia en una serie temporal: :rising, :falling, :stable, :volatile."
  [values]
  (when (>= (count values) 3)
    (let [pairs    (partition 2 1 values)
          deltas   (map (fn [[a b]] (- b a)) pairs)
          avg-delta (/ (reduce + deltas) (count deltas))
          variance (/ (reduce + (map #(Math/pow (- % avg-delta) 2) deltas))
                      (count deltas))
          volatility (Math/sqrt variance)]
      {:trend      (cond
                     (> avg-delta 0.1)    :rising
                     (< avg-delta -0.1)   :falling
                     (> volatility 1.0)   :volatile
                     :else                :stable)
       :avg-delta  avg-delta
       :volatility volatility
       :samples    (count values)})))


(defn detect-periodicity
  "Detectar periodicidad en timestamps (¿ocurre cada N ms?).
   Usa autocorrelación simplificada."
  [timestamps]
  (when (>= (count timestamps) 4)
    (let [sorted    (sort timestamps)
          intervals (map (fn [[a b]] (- b a)) (partition 2 1 sorted))
          avg-interval (/ (reduce + intervals) (count intervals))
          variance  (/ (reduce + (map #(Math/pow (- % avg-interval) 2) intervals))
                       (count intervals))
          cv        (if (pos? avg-interval)
                      (/ (Math/sqrt variance) avg-interval)
                      1.0)]
      {:periodic?     (< cv 0.3)  ; CV < 30% = bastante periódico
       :avg-interval  avg-interval
       :cv            cv
       :interpretation (cond
                         (< cv 0.1) "Altamente periódico (reloj)"
                         (< cv 0.3) "Moderadamente periódico"
                         (< cv 0.5) "Semi-periódico con ruido"
                         :else      "No periódico (aleatorio)")})))


(defn detect-anomaly
  "Detectar valores anómalos usando z-score simple."
  [values & {:keys [threshold] :or {threshold 2.0}}]
  (when (>= (count values) 5)
    (let [mean   (/ (reduce + values) (count values))
          std    (Math/sqrt (/ (reduce + (map #(Math/pow (- % mean) 2) values))
                               (count values)))
          scored (map-indexed
                   (fn [i v]
                     {:index   i
                      :value   v
                      :z-score (if (pos? std) (/ (- v mean) std) 0.0)
                      :anomaly? (> (Math/abs (if (pos? std) (/ (- v mean) std) 0.0))
                                   threshold)})
                   values)]
      {:mean     mean
       :std      std
       :anomalies (filter :anomaly? scored)
       :total     (count values)})))


;; ─── Prediction ─────────────────────────────────────────────────


(defn predict-next
  "Predecir el siguiente valor basándose en tendencia lineal.
   Extrapolación simple pero honesta (con intervalo de confianza)."
  [values & {:keys [confidence-level] :or {confidence-level 0.95}}]
  (when (>= (count values) 3)
    (let [n     (count values)
          xs    (range n)
          x-bar (/ (reduce + xs) n)
          y-bar (/ (reduce + values) n)
          ;; Regresión lineal simple
          ss-xy (reduce + (map (fn [x y] (* (- x x-bar) (- y y-bar)))
                               xs values))
          ss-xx (reduce + (map (fn [x] (Math/pow (- x x-bar) 2)) xs))
          slope (if (pos? ss-xx) (/ ss-xy ss-xx) 0)
          intercept (- y-bar (* slope x-bar))
          ;; Predicción
          predicted (+ intercept (* slope n))
          ;; Error estándar
          residuals (map (fn [x y] (Math/pow (- y (+ intercept (* slope x))) 2))
                         xs values)
          se        (Math/sqrt (/ (reduce + residuals) (max (- n 2) 1)))
          ;; Intervalo (simplificado)
          margin    (* 1.96 se)]  ; ~95% confidence

      {:predicted  predicted
       :slope      slope
       :intercept  intercept
       :confidence {:lower (- predicted margin)
                    :upper (+ predicted margin)
                    :level confidence-level}
       :trend      (cond
                     (> slope 0.1)   :increasing
                     (< slope -0.1)  :decreasing
                     :else           :flat)})))


;; ─── Temporal Report ────────────────────────────────────────────


(defn temporal-report
  "Informe completo del estado temporal de la memoria."
  [memory]
  (let [m       @memory
        entries (:entries m)
        now     (System/currentTimeMillis)
        ages    (map #(/ (- now (:timestamp %)) 1000.0) entries)]
    {:total-memories    (count entries)
     :capacity          (:capacity m)
     :utilization       (float (/ (count entries) (max (:capacity m) 1)))
     :oldest-sec        (when (seq ages) (apply max ages))
     :newest-sec        (when (seq ages) (apply min ages))
     :avg-strength      (when (seq entries)
                          (float (/ (reduce + (map :strength entries))
                                    (count entries))))
     :stats             (:stats m)
     :trend             (when (seq ages) (detect-trend (map :strength entries)))}))
