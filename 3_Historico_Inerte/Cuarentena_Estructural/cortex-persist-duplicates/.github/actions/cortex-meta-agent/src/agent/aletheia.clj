(ns agent.aletheia
  "██ ALETHEIA — Agente de Gestión del Conocimiento ██

   Cada hecho tiene un nivel de certeza. Cada inferencia lo propaga.
   Cada contradicción se detecta. Cada olvido es consciente.

   El agente epistémico ALETHEIA no almacena 'datos' — almacena CREENCIAS
   con niveles de confianza, fuentes, y cadenas de razonamiento.

   Inspirado en:
   - Dempster-Shafer (teoría de evidencia)
   - Bayesian Networks (propagación de certeza)
   - CORTEX Guards (detección de contradicciones)

   Reality Level: C5-REAL"
  (:require [clojure.string :as str]))

(declare find-contradictions)


;; ─── Belief (La unidad epistémica) ──────────────────────────────


(defn make-belief
  "Crear una creencia con metadatos epistémicos completos."
  [claim & {:keys [confidence source evidence domain]
            :or   {confidence 0.5
                   source     :unknown
                   evidence   []
                   domain     :general}}]
  {:claim      claim
   :confidence (max 0.0 (min 1.0 confidence))
   :source     source
   :evidence   evidence
   :domain     domain
   :created-at (System/currentTimeMillis)
   :updated-at (System/currentTimeMillis)
   :version    1
   :status     :active  ; :active, :contested, :retracted, :superseded
   :challenges []})


;; ─── Knowledge Base ─────────────────────────────────────────────


(defn make-knowledge-base
  "Crear una base de conocimiento epistémica."
  []
  (atom {:beliefs  {}   ; id → belief
         :counter  0
         :rules    []   ; reglas de inferencia
         :history  []})) ; log de cambios


(defn assert-belief!
  "Insertar una creencia en la base de conocimiento.
   Si contradice una creencia existente, marca ambas como :contested."
  [kb belief]
  (let [id (swap! kb (fn [state]
                       (let [new-id (inc (:counter state))]
                         (-> state
                             (assoc :counter new-id)
                             (assoc-in [:beliefs new-id] (assoc belief :id new-id))
                             (update :history conj
                                     {:action :assert
                                      :id     new-id
                                      :claim  (:claim belief)
                                      :time   (System/currentTimeMillis)})))))
        new-id (:counter @kb)]

    ;; Detección de contradicciones
    (let [contradictions (find-contradictions kb new-id)]
      (when (seq contradictions)
        (println (str "⚡ [ALETHEIA] Contradicción detectada: "
                      (:claim belief) " vs "
                      (count contradictions) " creencias existentes"))
        (doseq [c-id contradictions]
          (swap! kb update-in [:beliefs c-id :status] (constantly :contested))
          (swap! kb update-in [:beliefs c-id :challenges] conj new-id))
        (swap! kb assoc-in [:beliefs new-id :status] :contested)))

    new-id))


(defn retract-belief!
  "Retractar una creencia (marcarla como retractada, no borrarla).
   El conocimiento retractado sigue siendo conocimiento — sobre lo que ya no creemos."
  [kb belief-id & {:keys [reason] :or {reason "retracted"}}]
  (swap! kb (fn [state]
              (-> state
                  (assoc-in [:beliefs belief-id :status] :retracted)
                  (update :history conj
                          {:action :retract
                           :id     belief-id
                           :reason reason
                           :time   (System/currentTimeMillis)})))))


(defn update-confidence!
  "Actualizar la confianza de una creencia con nueva evidencia.
   Usa actualización bayesiana simplificada."
  [kb belief-id new-evidence new-confidence-delta]
  (swap! kb (fn [state]
              (let [belief  (get-in state [:beliefs belief-id])
                    old-c   (:confidence belief 0.5)
                    ;; Bayesian-ish update: mover hacia nueva evidencia
                    alpha   0.3
                    new-c   (+ (* (- 1 alpha) old-c)
                              (* alpha (+ old-c new-confidence-delta)))]
                (-> state
                    (assoc-in [:beliefs belief-id :confidence]
                              (max 0.0 (min 1.0 new-c)))
                    (update-in [:beliefs belief-id :evidence] conj new-evidence)
                    (assoc-in [:beliefs belief-id :updated-at] (System/currentTimeMillis))
                    (update-in [:beliefs belief-id :version] inc))))))


;; ─── Contradiction Detection ────────────────────────────────────


(defn find-contradictions
  "Buscar creencias que contradicen una creencia dada.
   Heurística: mismo dominio + claims con negación semántica."
  [kb belief-id]
  (let [state   @kb
        belief  (get-in state [:beliefs belief-id])
        domain  (:domain belief)
        claim   (str/lower-case (str (:claim belief)))]
    (->> (:beliefs state)
         (filter (fn [[id b]]
                   (and (not= id belief-id)
                        (= (:domain b) domain)
                        (= (:status b) :active)
                        ;; Heurística de negación simple
                        (or (str/includes? claim (str "not " (str/lower-case (str (:claim b)))))
                            (str/includes? (str/lower-case (str (:claim b))) (str "not " claim))
                            ;; Misma claim con confianza opuesta
                            (and (= (str/lower-case (str (:claim b)))
                                    claim)
                                 (< (Math/abs (- (:confidence belief)
                                                 (:confidence b))) 0.1))))))
         (map first))))


;; ─── Inference Engine ───────────────────────────────────────────


(defn add-inference-rule!
  "Añadir una regla de inferencia.
   Cada regla: {:if predicate-fn :then conclusion-fn :confidence-transfer float}"
  [kb rule]
  (swap! kb update :rules conj rule))


(defn run-inference!
  "Ejecutar todas las reglas de inferencia sobre las creencias activas.
   Genera nuevas creencias derivadas."
  [kb]
  (let [state  @kb
        active (filter (fn [[_ b]] (= :active (:status b)))
                       (:beliefs state))
        new-beliefs
        (for [rule   (:rules state)
              [_ b]  active
              :when ((:if rule) b)
              :let  [conclusion  ((:then rule) b)
                     transferred (* (:confidence b)
                                    (:confidence-transfer rule 0.8))]]
          (make-belief conclusion
                       :confidence transferred
                       :source     :inference
                       :evidence   [{:derived-from (:id b)
                                     :rule         (:name rule "unnamed")}]
                       :domain     (:domain b)))]

    (doseq [new-b new-beliefs]
      (assert-belief! kb new-b))

    {:inferred (count new-beliefs)}))


;; ─── Forgetting (Olvido consciente) ─────────────────────────────


(defn decay-beliefs!
  "Aplicar decay temporal a todas las creencias.
   Las creencias antiguas pierden confianza gradualmente.
   El olvido NO es un bug — es una feature epistémica."
  [kb & {:keys [decay-rate-per-hour] :or {decay-rate-per-hour 0.01}}]
  (let [now (System/currentTimeMillis)]
    (swap! kb
           (fn [state]
             (update state :beliefs
                     (fn [beliefs]
                       (into {}
                             (map (fn [[id b]]
                                    (let [age-hours (/ (- now (:updated-at b)) 3600000.0)
                                          decay     (Math/exp (- (* decay-rate-per-hour age-hours)))
                                          new-conf  (* (:confidence b) decay)]
                                      [id (assoc b :confidence (max 0.01 new-conf))]))
                                  beliefs))))))))


(defn prune-low-confidence!
  "Retractar creencias con confianza por debajo del umbral.
   Olvido activo: el agente decide qué ya no vale la pena recordar."
  [kb & {:keys [threshold] :or {threshold 0.1}}]
  (let [state     @kb
        to-prune  (->> (:beliefs state)
                       (filter (fn [[_ b]]
                                 (and (= :active (:status b))
                                      (< (:confidence b) threshold))))
                       (map first))]
    (doseq [id to-prune]
      (retract-belief! kb id :reason (str "confidence-below-" threshold)))
    {:pruned (count to-prune)}))


;; ─── Query & Report ─────────────────────────────────────────────


(defn query-beliefs
  "Buscar creencias por dominio y umbral de confianza."
  [kb & {:keys [domain min-confidence status]
         :or   {min-confidence 0.0 status :active}}]
  (->> (:beliefs @kb)
       vals
       (filter (fn [b]
                 (and (= (:status b) status)
                      (>= (:confidence b) min-confidence)
                      (or (nil? domain) (= (:domain b) domain)))))
       (sort-by :confidence >)))


(defn epistemic-report
  "Informe del estado epistémico completo."
  [kb]
  (let [state    @kb
        beliefs  (vals (:beliefs state))
        active   (filter #(= :active (:status %)) beliefs)
        contested (filter #(= :contested (:status %)) beliefs)]
    {:total-beliefs   (count beliefs)
     :active          (count active)
     :contested       (count contested)
     :retracted       (count (filter #(= :retracted (:status %)) beliefs))
     :avg-confidence  (if (seq active)
                        (float (/ (reduce + (map :confidence active))
                                  (count active)))
                        0.0)
     :domains         (distinct (map :domain active))
     :high-confidence (count (filter #(> (:confidence %) 0.8) active))
     :low-confidence  (count (filter #(< (:confidence %) 0.3) active))
     :inference-rules (count (:rules state))}))
