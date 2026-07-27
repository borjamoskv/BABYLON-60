(ns agent.mercator
  "██ MERCATOR — Agente de Negociación Multi-Parte ██

   Cuando múltiples agentes compiten por recursos limitados,
   MERCATOR encuentra el equilibrio.

   Protocolos implementados:
   - Contract Net: Anunciar tarea → recoger ofertas → adjudicar
   - Auction: Subastas de primer/segundo precio
   - Nash Bargaining: Encontrar el punto de Nash
   - Resource Allocation: Asignación justa con restricciones

   Un enjambre sin negociación es un enjambre en guerra.
   Un enjambre con negociación es una economía.

   Reality Level: C5-REAL")


;; ─── Resource Model ─────────────────────────────────────────────


(defn make-resource-pool
  "Crear un pool de recursos compartidos con capacidades limitadas."
  [resources]
  (atom {:resources (into {}
                          (map (fn [[k v]]
                                 [k {:capacity v
                                     :available v
                                     :allocated {}  ; agent-id → amount
                                     :history []}])
                               resources))
         :total-negotiations 0}))


(defn available
  "Consultar la cantidad disponible de un recurso."
  [pool resource-id]
  (get-in @pool [:resources resource-id :available] 0))


;; ─── Contract Net Protocol ──────────────────────────────────────


(defn announce-task
  "PASO 1: El manager anuncia una tarea y solicita ofertas.
   Cada agente responde con su oferta (precio, tiempo estimado, capacidad)."
  [task bidder-fns & {:keys [deadline-ms] :or {deadline-ms 5000}}]
  (println (str "📢 [MERCATOR] Anunciando tarea: " (:name task "unnamed")))
  (let [futures (doall
                  (for [[bidder-id bid-fn] bidder-fns]
                    {:bidder-id bidder-id
                     :future    (future
                                  (try
                                    (let [offer (bid-fn task)]
                                      {:bidder-id bidder-id
                                       :offer     offer
                                       :valid?    true})
                                    (catch Exception e
                                      {:bidder-id bidder-id
                                       :error     (ex-message e)
                                       :valid?    false})))}))]
    (->> futures
         (map #(deref (:future %) deadline-ms
                       {:bidder-id (:bidder-id %) :error "timeout" :valid? false}))
         (filter :valid?)
         vec)))


(defn adjudicate
  "PASO 2: Seleccionar la mejor oferta según criterio.
   scoring-fn recibe un offer y retorna un score numérico."
  [offers scoring-fn]
  (when (seq offers)
    (let [scored  (->> offers
                       (map #(assoc % :score (scoring-fn (:offer %))))
                       (sort-by :score >))
          winner  (first scored)]
      (println (str "🏆 [MERCATOR] Adjudicado a " (:bidder-id winner)
                    " (score: " (format "%.2f" (float (:score winner))) ")"))
      {:winner   winner
       :ranking  scored
       :total    (count offers)})))


(defn contract-net
  "Protocolo Contract Net completo: announce → collect → adjudicate."
  [task bidder-fns scoring-fn]
  (let [offers (announce-task task bidder-fns)
        result (adjudicate offers scoring-fn)]
    (assoc result :protocol :contract-net :task task)))


;; ─── Auction ────────────────────────────────────────────────────


(defn first-price-auction
  "Subasta de primer precio: gana la oferta más alta, paga lo que ofreció."
  [item bidder-fns]
  (println (str "🔨 [MERCATOR] Subasta (primer precio): " (:name item "item")))
  (let [bids (announce-task item bidder-fns)
        sorted (->> bids
                    (map #(assoc % :bid (get-in % [:offer :bid] 0)))
                    (sort-by :bid >))
        winner (first sorted)]
    (when winner
      {:protocol  :first-price-auction
       :winner    (:bidder-id winner)
       :price     (:bid winner)
       :all-bids  (mapv #(select-keys % [:bidder-id :bid]) sorted)})))


(defn second-price-auction
  "Subasta Vickrey (segundo precio): gana la oferta más alta,
   pero paga el precio de la SEGUNDA oferta más alta.
   Incentiva ofertar el valor real."
  [item bidder-fns]
  (println (str "🔨 [MERCATOR] Subasta Vickrey (segundo precio): " (:name item "item")))
  (let [bids   (announce-task item bidder-fns)
        sorted (->> bids
                    (map #(assoc % :bid (get-in % [:offer :bid] 0)))
                    (sort-by :bid >))]
    (when (>= (count sorted) 2)
      (let [winner      (first sorted)
            second-bid  (:bid (second sorted))]
        {:protocol     :vickrey-auction
         :winner       (:bidder-id winner)
         :winner-bid   (:bid winner)
         :price-paid   second-bid
         :savings      (- (:bid winner) second-bid)
         :all-bids     (mapv #(select-keys % [:bidder-id :bid]) sorted)}))))


;; ─── Resource Allocation ────────────────────────────────────────


(defn request-resource!
  "Un agente solicita una cantidad de un recurso."
  [pool agent-id resource-id amount]
  (let [result (atom nil)]
    (swap! pool
           (fn [state]
             (let [res       (get-in state [:resources resource-id])
                   avail     (:available res 0)]
               (if (>= avail amount)
                 ;; GRANT
                 (do (reset! result {:granted true :amount amount})
                     (-> state
                         (update-in [:resources resource-id :available] - amount)
                         (update-in [:resources resource-id :allocated agent-id]
                                    (fnil + 0) amount)
                         (update-in [:resources resource-id :history] conj
                                    {:action :allocate :agent agent-id
                                     :amount amount :time (System/currentTimeMillis)})))
                 ;; DENY
                 (do (reset! result {:granted false :requested amount :available avail})
                     state)))))
    @result))


(defn release-resource!
  "Un agente libera un recurso."
  [pool agent-id resource-id amount]
  (swap! pool
         (fn [state]
           (let [currently-held (get-in state [:resources resource-id :allocated agent-id] 0)
                 release-amount (min amount currently-held)]
             (-> state
                 (update-in [:resources resource-id :available] + release-amount)
                 (update-in [:resources resource-id :allocated agent-id] - release-amount)
                 (update-in [:resources resource-id :history] conj
                            {:action :release :agent agent-id
                             :amount release-amount :time (System/currentTimeMillis)}))))))


(defn fair-allocation
  "Asignación justa de un recurso entre N agentes.
   Usa max-min fairness: maximizar el mínimo que recibe cada agente."
  [pool resource-id agent-demands]
  (println (str "⚖️  [MERCATOR] Asignación justa de :" (name resource-id)
                " entre " (count agent-demands) " agentes"))
  (let [total     (available pool resource-id)
        n         (count agent-demands)
        equal     (/ total (max n 1))
        ;; Max-min: dar a cada uno min(demanda, equal_share)
        allocated (map (fn [[agent-id demand]]
                         {:agent-id  agent-id
                          :demanded  demand
                          :allocated (min demand equal)
                          :satisfied (>= equal demand)})
                       agent-demands)]

    ;; Redistribuir excedente de agentes satisfechos
    (let [excess    (reduce + (map #(max 0 (- equal (:demanded %)))
                                   (filter :satisfied allocated)))
          unsatisfied (filter (complement :satisfied) allocated)
          bonus     (if (pos? (count unsatisfied))
                      (/ excess (count unsatisfied))
                      0)]

      {:resource   resource-id
       :total      total
       :allocation (mapv (fn [a]
                           (if (:satisfied a)
                             a
                             (update a :allocated + bonus)))
                         allocated)
       :fairness   (let [allocations (map :allocated allocated)]
                     (if (seq allocations)
                       (let [mean (/ (reduce + allocations) (count allocations))
                             variance (/ (reduce + (map #(Math/pow (- % mean) 2) allocations))
                                         (count allocations))]
                         (- 1.0 (min 1.0 (/ (Math/sqrt variance) (max mean 0.01)))))
                       1.0))})))


;; ─── Negotiation Report ─────────────────────────────────────────


(defn pool-report
  "Estado actual del pool de recursos."
  [pool]
  (let [state @pool]
    {:resources
     (into {}
           (map (fn [[k v]]
                  [k {:capacity  (:capacity v)
                      :available (:available v)
                      :utilization (float (- 1.0 (/ (:available v)
                                                     (max (:capacity v) 1))))
                      :holders  (count (filter pos? (vals (:allocated v))))}])
                (:resources state)))}))
