(ns agent.l6-metacog
  "██████████ NIVEL 6 — AGENTE METACOGNITIVO ██████████

   MÖBIUS L6: El agente que piensa sobre cómo piensa.

   Framework: Nelson-Narens (1990) Metacognición
   ┌─────────────────────────────────────────────────┐
   │                 META-NIVEL                       │
   │  ┌───────────┐              ┌──────────────┐    │
   │  │ MONITOREO │◄────────────▶│   CONTROL    │    │
   │  │ (bottom-up)│              │  (top-down)  │    │
   │  └─────┬─────┘              └──────┬───────┘    │
   │        │  señales                  │ políticas  │
   │        │  de estado                │ adaptadas  │
   ├────────┼───────────────────────────┼────────────┤
   │        ▼                           ▼            │
   │  ┌─────────────────────────────────────────┐    │
   │  │           NIVEL-OBJETO                   │    │
   │  │  (ejecución de tareas reales)            │    │
   │  └─────────────────────────────────────────┘    │
   └─────────────────────────────────────────────────┘

   En Clojure, la metacognición es natural porque:
   - Las funciones son valores inspeccionables
   - El estado es un átomo observable
   - Los metadatos son ciudadanos de primera clase (^{:meta data})
   - quote/eval permiten inspeccionar código sin ejecutarlo

   Reality Level: C5-REAL"
  (:require [clojure.string :as str]))


;; ─── Self-Model (El agente sabe qué sabe) ──────────────────────


(defn make-self-model
  "Crear el modelo-de-sí-mismo del agente.
   Este modelo es un ÁTOMO — mutable, observable, transaccional.

   El self-model contiene:
   - capabilities: qué PUEDE hacer el agente
   - confidence: confianza calibrada por dominio
   - performance: historial de rendimiento
   - blind-spots: qué NO sabe (meta-ignorancia consciente)
   - active-policies: políticas top-down activas"
  []
  (atom {:capabilities   #{:text-analysis :code-review :data-transform
                           :api-call :file-manipulation}
         :confidence     {:text-analysis   0.85
                          :code-review     0.70
                          :data-transform  0.90
                          :api-call        0.60
                          :file-manipulation 0.75}
         :performance    {:total-tasks     0
                          :successes       0
                          :failures        0
                          :avg-latency-ms  0.0
                          :history         []}
         :blind-spots    #{:visual-reasoning :audio-processing
                           :real-time-streaming :hardware-control}
         :active-policies {:delegation-threshold 0.4
                           :uncertainty-abort    0.2
                           :overconfidence-check true
                           :calibration-window   20}
         :meta-state     {:last-calibration  nil
                          :drift-detected?   false
                          :total-reflections 0}}))


;; ─── Monitoring Signals (Bottom-Up) ─────────────────────────────


(defn- update-performance!
  "Registrar el resultado de una tarea en el historial.
   Señal bottom-up: del nivel-objeto al meta-nivel."
  [self-model task-id success? latency-ms confidence-used]
  (swap! self-model
         (fn [model]
           (let [perf (:performance model)
                 n    (inc (:total-tasks perf))
                 new-avg (/ (+ (* (:avg-latency-ms perf) (:total-tasks perf))
                              latency-ms)
                           (max n 1))]
             (-> model
                 (update-in [:performance :total-tasks] inc)
                 (update-in [:performance (if success? :successes :failures)] inc)
                 (assoc-in  [:performance :avg-latency-ms] new-avg)
                 (update-in [:performance :history]
                            (fn [h] (take 100 (conj h
                                                    {:task-id    task-id
                                                     :success?   success?
                                                     :latency-ms latency-ms
                                                     :confidence confidence-used
                                                     :timestamp  (System/currentTimeMillis)})))))))))


(defn- detect-confidence-drift!
  "Detectar si la confianza del agente está descalibrada.
   Compara la confianza declarada vs el rendimiento real.

   Si el agente dice 'tengo 90% de confianza' pero solo acierta 60%,
   hay OVERCONFIDENCE — el meta-nivel debe corregir."
  [self-model domain]
  (let [model    @self-model
        declared (get-in model [:confidence domain] 0.5)
        history  (filter #(= domain (:domain %))
                         (get-in model [:performance :history]))
        recent   (take 20 history)]
    (when (>= (count recent) 5)
      (let [actual (/ (count (filter :success? recent))
                      (max (count recent) 1))]
        (cond
          ;; Overconfidence: cree que es mejor de lo que es
          (> (- declared actual) 0.2)
          {:drift    :overconfidence
           :declared declared
           :actual   actual
           :delta    (- declared actual)
           :action   :reduce-confidence}

          ;; Underconfidence: es mejor de lo que cree
          (> (- actual declared) 0.2)
          {:drift    :underconfidence
           :declared declared
           :actual   actual
           :delta    (- actual declared)
           :action   :increase-confidence}

          :else nil)))))


(defn- calculate-epistemic-uncertainty
  "Calcular la incertidumbre epistémica para una tarea.
   Combina: confianza del dominio + historial reciente + volatilidad."
  [self-model domain]
  (let [model      @self-model
        confidence (get-in model [:confidence domain] 0.5)
        history    (get-in model [:performance :history])
        recent     (take 10 (filter #(= domain (:domain %)) history))
        volatility (if (< (count recent) 3)
                     0.3  ; alta incertidumbre si poca historia
                     (let [outcomes (map #(if (:success? %) 1.0 0.0) recent)
                           mean     (/ (reduce + outcomes) (count outcomes))
                           variance (/ (reduce + (map #(Math/pow (- % mean) 2) outcomes))
                                       (count outcomes))]
                       (Math/sqrt variance)))]
    {:confidence confidence
     :volatility volatility
     :uncertainty (- 1.0 (* confidence (- 1.0 volatility)))
     :sample-size (count recent)}))


;; ─── Control Signals (Top-Down) ─────────────────────────────────


(defn- should-delegate?
  "Decisión meta-cognitiva: ¿debería el agente delegar esta tarea?
   Si la incertidumbre es alta, es mejor delegar a otro agente o humano."
  [self-model domain]
  (let [model     @self-model
        threshold (get-in model [:active-policies :delegation-threshold])
        epistemic (calculate-epistemic-uncertainty self-model domain)]
    (cond
      ;; Blind spot conocido: siempre delegar
      (contains? (:blind-spots model) domain)
      {:delegate? true
       :reason    (str "'" (name domain) "' es un blind spot conocido")
       :to        :human-or-specialist}

      ;; Incertidumbre alta: delegar
      (> (:uncertainty epistemic) (- 1.0 threshold))
      {:delegate? true
       :reason    (str "Incertidumbre alta: " (format "%.2f" (:uncertainty epistemic)))
       :to        :peer-agent}

      ;; Confianza suficiente: ejecutar
      :else
      {:delegate? false
       :reason    (str "Confianza: " (format "%.2f" (:confidence epistemic)))})))


(defn- calibrate-confidence!
  "Recalibrar la confianza basándose en rendimiento real.
   Señal top-down: el meta-nivel ajusta el nivel-objeto."
  [self-model domain]
  (let [model   @self-model
        history (filter #(= domain (:domain %))
                        (get-in model [:performance :history]))
        recent  (take (get-in model [:active-policies :calibration-window] 20) history)]
    (when (>= (count recent) 5)
      (let [actual-rate (/ (count (filter :success? recent))
                           (max (count recent) 1))]
        ;; Exponential moving average con el rate real
        (swap! self-model
               (fn [m]
                 (let [old-conf (get-in m [:confidence domain] 0.5)
                       alpha    0.3
                       new-conf (+ (* alpha actual-rate) (* (- 1 alpha) old-conf))]
                   (-> m
                       (assoc-in [:confidence domain] new-conf)
                       (assoc-in [:meta-state :last-calibration] (System/currentTimeMillis))
                       (update-in [:meta-state :total-reflections] inc)))))))))


;; ─── The Metacognitive Agent ────────────────────────────────────


(defn metacognitive-execute
  "Ejecutar una tarea con supervisión metacognitiva completa.

   El flujo:
   1. PRE-EVALUACIÓN: ¿Puedo hacer esto? ¿Debería delegarlo?
   2. EJECUCIÓN: Ejecutar con monitoreo de latencia
   3. POST-EVALUACIÓN: Actualizar self-model + recalibrar confianza
   4. META-REFLEXIÓN: Detectar drift y ajustar políticas

   El agente L6 no solo ejecuta — SABE si puede ejecutar,
   y ajusta sus creencias basándose en evidencia."
  [self-model task-fn args & {:keys [domain task-id]
                               :or   {domain  :general
                                      task-id (str (random-uuid))}}]
  (println (str "🧠 [L6-METACOG] Evaluando tarea " task-id " (dominio: " (name domain) ")..."))

  ;; 1. PRE-EVALUACIÓN (meta-level monitoring)
  (let [delegation (should-delegate? self-model domain)
        epistemic  (calculate-epistemic-uncertainty self-model domain)]

    (println (str "  📊 Confianza: " (format "%.2f" (:confidence epistemic))
                  " | Incertidumbre: " (format "%.2f" (:uncertainty epistemic))
                  " | Volatilidad: " (format "%.2f" (:volatility epistemic))))

    (when (:delegate? delegation)
      (println (str "  ⚠️  Señal de delegación: " (:reason delegation)
                    " → " (name (:to delegation)))))

    (if (:delegate? delegation)
      ;; DELEGAR — el agente sabe que NO sabe
      {:verdict    :delegated
       :task-id    task-id
       :domain     domain
       :reason     (:reason delegation)
       :delegate-to (:to delegation)
       :epistemic  epistemic}

      ;; 2. EJECUTAR con monitoreo
      (let [start-ns   (System/nanoTime)
            result     (try
                         {:success? true
                          :value    (apply task-fn args)}
                         (catch Exception e
                           {:success? false
                            :error    (ex-message e)
                            :type     (type e)}))
            latency-ms (/ (- (System/nanoTime) start-ns) 1e6)]

        ;; 3. POST-EVALUACIÓN (bottom-up signal)
        (update-performance! self-model task-id
                             (:success? result) latency-ms
                             (:confidence epistemic))

        ;; 4. META-REFLEXIÓN
        (calibrate-confidence! self-model domain)
        (let [drift (detect-confidence-drift! self-model domain)]
          (when drift
            (println (str "  🔄 DRIFT detectado: " (name (:drift drift))
                          " (declarada=" (format "%.2f" (:declared drift))
                          " vs real=" (format "%.2f" (:actual drift)) ")")))

          (if (:success? result)
            (println (str "  ✅ Completado en " (format "%.1f" latency-ms) "ms"))
            (println (str "  ❌ Fallo: " (:error result))))

          ;; Retornar resultado enriquecido con metadata metacognitiva
          (merge result
                 {:task-id    task-id
                  :domain     domain
                  :latency-ms latency-ms
                  :epistemic  epistemic
                  :drift      drift
                  :meta-state (:meta-state @self-model)}))))))


;; ─── Introspection API ──────────────────────────────────────────


(defn self-report
  "El agente genera un informe sobre sí mismo.
   Esto es metacognición pura: pensando sobre su propio estado."
  [self-model]
  (let [model @self-model
        perf  (:performance model)
        rate  (if (> (:total-tasks perf) 0)
                (/ (:successes perf) (max (:total-tasks perf) 1))
                1.0)]
    {:identity      "MÖBIUS L6 — Metacognitive Agent"
     :capabilities  (:capabilities model)
     :blind-spots   (:blind-spots model)
     :confidence    (:confidence model)
     :success-rate  (float rate)
     :total-tasks   (:total-tasks perf)
     :avg-latency   (:avg-latency-ms perf)
     :reflections   (get-in model [:meta-state :total-reflections])
     :calibrated?   (some? (get-in model [:meta-state :last-calibration]))
     :drift?        (get-in model [:meta-state :drift-detected?])
     :assessment    (cond
                      (> rate 0.9)   "Alto rendimiento. Confianza calibrada."
                      (> rate 0.7)   "Rendimiento aceptable. Monitorear drift."
                      (> rate 0.5)   "Rendimiento degradado. Recalibrar urgente."
                      :else          "Rendimiento crítico. Delegar más tareas.")}))


(defn what-i-dont-know
  "El agente declara explícitamente lo que NO sabe.
   La ignorancia consciente es la forma más alta de metacognición."
  [self-model]
  (let [model @self-model]
    {:known-unknowns   (:blind-spots model)
     :low-confidence   (->> (:confidence model)
                            (filter (fn [[_ v]] (< v 0.5)))
                            (into {}))
     :unknown-unknowns "Por definición, no puedo listar lo que no sé que no sé.
                        Pero puedo monitorear fallos inesperados en dominios
                        que creía dominar — eso revela unknown-unknowns."}))
