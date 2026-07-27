(ns agent.l5-healer
  "████████ NIVEL 5 — AGENTE AUTO-CURATIVO (SELF-HEALING) ████████

   MÖBIUS L5: El agente que se repara a sí mismo.

   Patrón: REFLEXION LOOP
   ┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐
   │ EXECUTE │────▶│  FAIL    │────▶│ REFLECT  │────▶│ REWRITE │──┐
   └─────────┘     └──────────┘     └──────────┘     └─────────┘  │
        ▲                                                          │
        └──────────────────────────────────────────────────────────┘

   En Clojure, la reflexión es natural:
   - Las funciones son datos (listas)
   - Los errores son datos (maps)
   - Las correcciones son datos (maps que transforman maps)
   - El loop es un reduce sobre intentos

   No hay 'try-catch-log'. Hay 'execute-reflect-evolve'.

   Reality Level: C5-REAL"
  (:require [clojure.string :as str]))


;; ─── Core Types ─────────────────────────────────────────────────


(defn make-reflection
  "Crear una reflexión estructurada a partir de un fallo.
   La reflexión NO es un log — es un DATO que el agente usa para decidir."
  [iteration error context strategy]
  {:iteration  iteration
   :timestamp  (System/currentTimeMillis)
   :error      {:type    (type error)
                :message (ex-message error)
                :data    (ex-data error)}
   :context    context
   :strategy   strategy
   :diagnosis  nil  ; se llena en la fase de diagnóstico
   :fix        nil}) ; se llena en la fase de reescritura


;; ─── Diagnosis Engine (Pattern Matching) ────────────────────────


(def ^:private diagnosis-patterns
  "Base de patrones de diagnóstico. Cada patrón es una función pura:
   error-data → {:diagnosis ... :strategy ...}

   ESTO es code-as-data: las reglas de diagnóstico son datos
   que podrían venir de un fichero, una DB, o ser generadas por LLM."
  [{:id       :timeout
    :match    #(str/includes? (str (:message %)) "timeout")
    :diagnose (constantly {:diagnosis "Operación excedió el presupuesto temporal"
                           :strategy  :add-timeout-guard})}

   {:id       :connection
    :match    #(str/includes? (str (:message %)) "connection")
    :diagnose (constantly {:diagnosis "Fallo de conexión transitorio"
                           :strategy  :retry-with-backoff})}

   {:id       :rate-limit
    :match    #(or (str/includes? (str (:message %)) "429")
                   (str/includes? (str (:message %)) "rate"))
    :diagnose (constantly {:diagnosis "Rate limit alcanzado"
                           :strategy  :throttle})}

   {:id       :permission
    :match    #(str/includes? (str (:message %)) "permission")
    :diagnose (constantly {:diagnosis "Permisos insuficientes"
                           :strategy  :escalate})}

   {:id       :assertion
    :match    #(instance? AssertionError (:type %))
    :diagnose (constantly {:diagnosis "Invariante interno violado"
                           :strategy  :isolate-and-bypass})}])


(defn diagnose
  "Diagnosticar un error contra la base de patrones.
   Retorna el diagnóstico del primer patrón que matchea."
  [error-data]
  (let [matching (first (filter #((:match %) error-data) diagnosis-patterns))]
    (if matching
      ((:diagnose matching) error-data)
      {:diagnosis (str "Error no clasificado: " (:message error-data))
       :strategy  :generic-retry})))


;; ─── Rewrite Strategies ─────────────────────────────────────────


(defn- wrap-with-retry
  "Estrategia: envolver la tarea en reintentos con backoff exponencial."
  [task-fn max-retries]
  (fn [& args]
    (loop [attempt 0
           last-error nil]
      (if (>= attempt max-retries)
        (throw (ex-info "Retries exhausted"
                        {:attempts max-retries :last-error last-error}))
        (try
          (apply task-fn args)
          (catch Exception e
            (let [backoff-ms (* (Math/pow 2 attempt) 100)]
              (Thread/sleep (long backoff-ms))
              (recur (inc attempt) (ex-message e)))))))))


(defn- wrap-with-timeout
  "Estrategia: envolver la tarea con un timeout."
  [task-fn timeout-ms]
  (fn [& args]
    (let [fut (future (apply task-fn args))]
      (or (deref fut timeout-ms nil)
          (do (future-cancel fut)
              (throw (ex-info "Timeout exceeded"
                              {:timeout-ms timeout-ms})))))))


(defn- wrap-with-throttle
  "Estrategia: throttle antes de ejecutar."
  [task-fn delay-ms]
  (fn [& args]
    (Thread/sleep (long delay-ms))
    (apply task-fn args)))


(defn- wrap-with-fallback
  "Estrategia: ejecutar fallback si la función principal falla."
  [task-fn fallback-fn]
  (fn [& args]
    (try
      (apply task-fn args)
      (catch Exception _e
        (apply fallback-fn args)))))


(def ^:private rewrite-strategies
  "Mapa de estrategia → función de reescritura.
   Cada estrategia toma un task-fn y retorna un task-fn modificado.
   ESTO es code-as-data: las estrategias transforman funciones como datos."
  {:retry-with-backoff    #(wrap-with-retry % 3)
   :add-timeout-guard     #(wrap-with-timeout % 5000)
   :throttle              #(wrap-with-throttle % 2000)
   :isolate-and-bypass    #(wrap-with-fallback % (fn [& _] {:status :bypassed}))
   :escalate              identity  ; no-op, requiere intervención humana
   :generic-retry         #(wrap-with-retry % 2)})


(defn apply-rewrite
  "Aplicar una estrategia de reescritura a una función de tarea.
   Retorna una nueva función que incorpora la corrección."
  [task-fn strategy]
  (let [rewriter (get rewrite-strategies strategy identity)]
    (rewriter task-fn)))


;; ─── The Reflexion Loop ─────────────────────────────────────────


(defn reflexion-loop
  "El loop de reflexión completo. Ejecuta una tarea, y si falla:
   1. Captura el error
   2. Diagnostica el patrón
   3. Reescribe la función con la estrategia correcta
   4. Reintenta con la versión mejorada

   Retorna:
   {:verdict     :success | :exhausted
    :result      <resultado de la tarea>
    :iterations  <número de intentos>
    :reflections [<reflexiones acumuladas>]}

   La CLAVE: cada iteración ejecuta una VERSIÓN DIFERENTE de la función.
   El agente no reintenta ciegamente — se transforma entre intentos."
  [task-fn args & {:keys [max-iterations context]
                   :or   {max-iterations 3
                          context        {}}}]
  (loop [current-fn   task-fn
         iteration    0
         reflections  []]
    (if (>= iteration max-iterations)
      ;; EXHAUSTED
      {:verdict     :exhausted
       :result      nil
       :iterations  iteration
       :reflections reflections}

      (try
        ;; EXECUTE
        (let [result (apply current-fn args)]
          ;; SUCCESS
          {:verdict     :success
           :result      result
           :iterations  (inc iteration)
           :reflections reflections})

        (catch Exception error
          ;; REFLECT
          (let [error-data  {:type    (type error)
                             :message (ex-message error)
                             :data    (ex-data error)}
                diagnosis   (diagnose error-data)
                reflection  (-> (make-reflection iteration error context (:strategy diagnosis))
                                (assoc :diagnosis (:diagnosis diagnosis)
                                       :fix       (:strategy diagnosis)))
                ;; REWRITE — crear nueva versión de la función
                evolved-fn  (apply-rewrite current-fn (:strategy diagnosis))]

            (println (str "  ⟳ [L5] Iteración " (inc iteration) "/" max-iterations
                          " — " (:diagnosis diagnosis)
                          " → Estrategia: " (name (:strategy diagnosis))))

            ;; RETRY con la función evolucionada
            (recur evolved-fn
                   (inc iteration)
                   (conj reflections reflection))))))))


;; ─── Convenience API ────────────────────────────────────────────


(defn self-healing-execute
  "API de alto nivel: ejecuta cualquier función con auto-curación.

   Ejemplo:
     (self-healing-execute fetch-data [\"https://api.example.com\"]
       :max-iterations 3
       :context {:operation \"data-fetch\"})

   El agente L5 no necesita saber QUÉ hace la función.
   Solo necesita saber que si falla, debe reflexionar y adaptarse."
  [task-fn args & {:as opts}]
  (println "🩹 [L5-HEALER] Iniciando ejecución con auto-curación...")
  (let [result (reflexion-loop task-fn args opts)]
    (if (= :success (:verdict result))
      (do
        (when (> (:iterations result) 1)
          (println (str "  ✅ Resuelto tras " (:iterations result)
                        " iteraciones y " (count (:reflections result))
                        " reflexiones")))
        result)
      (do
        (println (str "  ❌ Agotado tras " (:iterations result) " iteraciones"))
        (println "  📋 Reflexiones acumuladas:")
        (doseq [r (:reflections result)]
          (println (str "    [" (:iteration r) "] "
                        (:diagnosis r) " → " (name (:fix r)))))
        result))))
