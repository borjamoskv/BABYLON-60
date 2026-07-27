(ns agent.colmena
  "██ COLMENA — Coordinador de Enjambre Multi-Agente ██

   Orquesta múltiples agentes en paralelo con:
   - Fan-out / Fan-in: distribuir trabajo y recoger resultados
   - Quorum: esperar a que N de M agentes coincidan
   - Tournament: selección competitiva del mejor resultado
   - Pipeline: encadenar agentes en secuencia
   - Broadcast: enviar a todos, recoger de cualquiera

   En Clojure, la concurrencia es nativa:
   - futures para paralelismo
   - atoms para estado compartido
   - agents (Clojure agents) para mutación asíncrona
   - core.async channels para comunicación

   Reality Level: C5-REAL"
  (:require [clojure.string :as str]))


;; ─── Agent Registry ─────────────────────────────────────────────


(defn make-registry
  "Crear un registro de agentes disponibles.
   Cada agente es: {:id string :fn function :capabilities set :load atom}"
  []
  (atom {}))


(defn register-agent!
  "Registrar un agente en el enjambre."
  [registry id agent-fn & {:keys [capabilities] :or {capabilities #{}}}]
  (swap! registry assoc id
         {:id           id
          :fn           agent-fn
          :capabilities capabilities
          :load         (atom 0)
          :completed    (atom 0)
          :failures     (atom 0)}))


(defn unregister-agent!
  "Eliminar un agente del enjambre."
  [registry id]
  (swap! registry dissoc id))


;; ─── Dispatch Patterns ──────────────────────────────────────────


(defn fan-out
  "FAN-OUT: Enviar la misma tarea a TODOS los agentes en paralelo.
   Retorna todos los resultados.

   Útil para: redundancia, verificación cruzada, diversidad de soluciones."
  [registry task & {:keys [timeout-ms] :or {timeout-ms 10000}}]
  (println (str "📡 [COLMENA] Fan-out a " (count @registry) " agentes..."))
  (let [agents  (vals @registry)
        futures (doall
                  (for [ag agents]
                    (let [f (future
                              (try
                                (swap! (:load ag) inc)
                                (let [result ((:fn ag) task)]
                                  (swap! (:completed ag) inc)
                                  (swap! (:load ag) dec)
                                  {:agent-id (:id ag) :result result :success? true})
                                (catch Exception e
                                  (swap! (:failures ag) inc)
                                  (swap! (:load ag) dec)
                                  {:agent-id (:id ag) :error (ex-message e) :success? false})))]
                      {:agent ag :future f})))
        results (doall
                  (for [{:keys [future]} futures]
                    (deref future timeout-ms
                           {:agent-id "?" :error "timeout" :success? false})))]
    {:pattern  :fan-out
     :total    (count results)
     :success  (count (filter :success? results))
     :results  results}))


(defn fan-in
  "FAN-IN: Enviar sub-tareas DIFERENTES a agentes específicos.
   Cada agente recibe una parte del trabajo.

   Útil para: dividir y conquistar, procesamiento paralelo."
  [registry task-assignments & {:keys [timeout-ms] :or {timeout-ms 10000}}]
  (println (str "🔀 [COLMENA] Fan-in: " (count task-assignments) " sub-tareas..."))
  (let [futures (doall
                  (for [{:keys [agent-id task]} task-assignments
                        :let [ag (get @registry agent-id)]
                        :when ag]
                    {:agent-id agent-id
                     :future   (future
                                 (try
                                   {:agent-id agent-id
                                    :result   ((:fn ag) task)
                                    :success? true}
                                   (catch Exception e
                                     {:agent-id agent-id
                                      :error    (ex-message e)
                                      :success? false})))}))]
    {:pattern :fan-in
     :total   (count futures)
     :results (doall (map #(deref (:future %) timeout-ms
                                   {:agent-id (:agent-id %) :error "timeout" :success? false})
                          futures))}))


(defn quorum
  "QUORUM: Enviar a todos, pero solo necesitar que N agentes coincidan.
   Implementa consenso bizantino simplificado.

   Útil para: decisiones críticas, resistencia a agentes defectuosos."
  [registry task required-agreement & {:keys [timeout-ms comparator]
                                        :or   {timeout-ms 10000
                                               comparator =}}]
  (println (str "🗳️  [COLMENA] Quorum: necesarios " required-agreement
                " de " (count @registry) "..."))
  (let [fan-result (fan-out registry task :timeout-ms timeout-ms)
        successes  (filter :success? (:results fan-result))
        ;; Agrupar por resultado (usando el comparator)
        groups     (->> successes
                        (group-by :result)
                        (sort-by #(- (count (val %)))))]

    (if-let [[consensus-value matching] (first groups)]
      (if (>= (count matching) required-agreement)
        {:pattern   :quorum
         :achieved  true
         :consensus consensus-value
         :agreement (count matching)
         :required  required-agreement
         :total     (count successes)}
        {:pattern   :quorum
         :achieved  false
         :best      consensus-value
         :agreement (count matching)
         :required  required-agreement
         :reason    "Insufficient agreement"})

      {:pattern  :quorum
       :achieved false
       :reason   "No successful responses"})))


(defn tournament
  "TOURNAMENT: Todos compiten, gana el mejor resultado según scoring-fn.
   Selección natural aplicada a soluciones.

   Útil para: optimización, encontrar la mejor solución entre alternativas."
  [registry task scoring-fn & {:keys [timeout-ms] :or {timeout-ms 10000}}]
  (println (str "🏆 [COLMENA] Tournament: " (count @registry) " competidores..."))
  (let [fan-result (fan-out registry task :timeout-ms timeout-ms)
        scored     (->> (:results fan-result)
                        (filter :success?)
                        (map (fn [r]
                               (assoc r :score (try (scoring-fn (:result r))
                                                    (catch Exception _ -1.0)))))
                        (sort-by :score >))]

    (println (str "  🥇 Ganador: " (:agent-id (first scored))
                  " (score: " (some-> scored first :score (format "%.2f")) ")"))

    {:pattern    :tournament
     :winner     (first scored)
     :ranking    (mapv #(select-keys % [:agent-id :score]) scored)
     :total      (count scored)}))


(defn pipeline
  "PIPELINE: Encadenar agentes en secuencia. La salida de uno es la entrada del siguiente.

   Útil para: transformación progresiva, refinamiento iterativo."
  [registry agent-ids initial-input]
  (println (str "⛓️  [COLMENA] Pipeline: " (str/join " → " agent-ids)))
  (reduce
    (fn [acc agent-id]
      (if-let [ag (get @registry agent-id)]
        (try
          (let [result ((:fn ag) (:value acc))]
            (println (str "  ✓ " agent-id " completado"))
            (-> acc
                (assoc :value result)
                (update :steps conj {:agent-id agent-id :success? true})))
          (catch Exception e
            (println (str "  ✗ " agent-id " falló: " (ex-message e)))
            (reduced (-> acc
                         (assoc :error (ex-message e) :failed-at agent-id)
                         (update :steps conj {:agent-id agent-id :success? false})))))
        (do
          (println (str "  ⚠ " agent-id " no encontrado"))
          acc)))
    {:value initial-input :steps [] :pattern :pipeline}
    agent-ids))


;; ─── Load Balancing ─────────────────────────────────────────────


(defn least-loaded
  "Seleccionar el agente con menor carga actual."
  [registry & {:keys [capability]}]
  (let [agents (if capability
                 (filter #(contains? (:capabilities (val %)) capability)
                         @registry)
                 @registry)]
    (when (seq agents)
      (let [[id ag] (apply min-key #(deref (:load (val %))) agents)]
        id))))


(defn dispatch-balanced
  "Despachar una tarea al agente menos cargado."
  [registry task & {:keys [capability]}]
  (if-let [agent-id (least-loaded registry :capability capability)]
    (let [ag (get @registry agent-id)]
      (swap! (:load ag) inc)
      (try
        (let [result ((:fn ag) task)]
          (swap! (:completed ag) inc)
          (swap! (:load ag) dec)
          {:agent-id agent-id :result result :success? true})
        (catch Exception e
          (swap! (:failures ag) inc)
          (swap! (:load ag) dec)
          {:agent-id agent-id :error (ex-message e) :success? false})))
    {:error "No agents available" :success? false}))


;; ─── Swarm Report ───────────────────────────────────────────────


(defn swarm-report
  "Estado del enjambre: carga, rendimiento, salud de cada agente."
  [registry]
  (let [agents (vals @registry)]
    {:total-agents  (count agents)
     :agents        (mapv (fn [ag]
                            {:id          (:id ag)
                             :capabilities (:capabilities ag)
                             :load        @(:load ag)
                             :completed   @(:completed ag)
                             :failures    @(:failures ag)
                             :health      (let [total (+ @(:completed ag) @(:failures ag))]
                                            (if (pos? total)
                                              (float (/ @(:completed ag) total))
                                              1.0))})
                          agents)}))
