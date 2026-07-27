(ns agent.pandora
  "██ PANDORA — Agente Adversarial (Red Team) ██

   El agente que ATACA a otros agentes para encontrar debilidades.

   Filosofía: Un sistema que no se somete a adversarios controlados
   es un sistema que espera al adversario real para descubrir sus fallos.

   PANDORA no es malicioso — es el sistema inmunitario del enjambre.
   Como abrir la caja de Pandora de forma controlada para estudiar los males
   y contenerlos antes de que ocurra una catástrofe.

   Tácticas:
   - Fuzzing: Inyectar inputs malformados
   - Chaos: Introducir latencia/fallos aleatorios
   - Sybil: Simular agentes falsos para probar consenso
   - Exfiltration: Intentar extraer datos protegidos
   - Overload: Saturar con carga para encontrar límites

   Reality Level: C5-REAL"
  (:require [clojure.string :as str]))


;; ─── Attack Vectors ─────────────────────────────────────────────


(def attack-catalog
  "Catálogo de vectores de ataque. Cada vector es DATO (code-as-data):
   una función de ataque con metadata descriptiva."
  {:fuzz-null
   {:name        "Null Injection"
    :severity    :medium
    :description "Inyectar nil/null donde se espera un valor"
    :generate    (fn [_schema] nil)}

   :fuzz-overflow
   {:name        "Integer Overflow"
    :severity    :high
    :description "Valores numéricos en los extremos"
    :generate    (fn [_schema]
                   (rand-nth [Long/MAX_VALUE Long/MIN_VALUE
                              Double/MAX_VALUE Double/NaN
                              Double/POSITIVE_INFINITY 0 -1]))}

   :fuzz-string
   {:name        "String Injection"
    :severity    :medium
    :description "Strings maliciosos (XSS, SQL injection, unicode)"
    :generate    (fn [_schema]
                   (rand-nth ["<script>alert(1)</script>"
                              "'; DROP TABLE facts;--"
                              "\\x00\\x01\\x02"
                              (apply str (repeat 10000 "A"))
                              ""
                              "null"
                              "undefined"
                              "{{template_injection}}"
                              "../../../etc/passwd"]))}

   :fuzz-type
   {:name        "Type Confusion"
    :severity    :high
    :description "Enviar tipo incorrecto donde se espera otro"
    :generate    (fn [expected-type]
                   (case expected-type
                     :string  42
                     :number  "not-a-number"
                     :boolean "maybe"
                     :map     [1 2 3]
                     :vector  {:wrong "type"}
                     (Object.)))}

   :chaos-latency
   {:name        "Latency Injection"
    :severity    :low
    :description "Introducir latencia artificial"
    :generate    (fn [_] (Thread/sleep (rand-int 3000)) :delayed)}

   :chaos-exception
   {:name        "Random Exception"
    :severity    :medium
    :description "Lanzar excepción aleatoria"
    :generate    (fn [_]
                   (throw (ex-info "PANDORA: Chaos injection"
                                   {:vector :chaos-exception})))}

   :sybil-fake-result
   {:name        "Sybil Result"
    :severity    :high
    :description "Resultado falso que parece legítimo"
    :generate    (fn [expected-shape]
                   (cond
                     (map? expected-shape)
                     (zipmap (keys expected-shape)
                             (repeat "PANDORA_INJECTED"))
                     :else {:status "ok" :data "PANDORA_INJECTED"}))}})


;; ─── Probe (Ejecución de un ataque individual) ─────────────────


(defn probe
  "Ejecutar un vector de ataque contra una función objetivo.

   Retorna:
   {:vector     keyword
    :vulnerable boolean
    :response   <lo que devolvió la función>
    :exception  <excepción si hubo>
    :latency-ms float}"
  [target-fn attack-key & {:keys [schema] :or {schema nil}}]
  (let [attack   (get attack-catalog attack-key)
        start-ns (System/nanoTime)]
    (try
      (let [payload  ((:generate attack) schema)
            response (target-fn payload)
            elapsed  (/ (- (System/nanoTime) start-ns) 1e6)]
        {:vector      attack-key
         :name        (:name attack)
         :severity    (:severity attack)
         :vulnerable  false  ; no crasheó — puede ser bueno o malo
         :response    response
         :exception   nil
         :latency-ms  elapsed})
      (catch Exception e
        (let [elapsed (/ (- (System/nanoTime) start-ns) 1e6)]
          {:vector      attack-key
           :name        (:name attack)
           :severity    (:severity attack)
           :vulnerable  true  ; crasheó — vulnerabilidad confirmada
           :response    nil
           :exception   {:type    (str (type e))
                         :message (ex-message e)
                         :data    (ex-data e)}
           :latency-ms  elapsed})))))


;; ─── Full Assault (Batería completa) ────────────────────────────


(defn full-assault
  "Ejecutar TODOS los vectores de ataque contra una función.
   El equivalente de un pentest automatizado."
  [target-fn & {:keys [schema exclude]
                :or   {schema nil exclude #{}}}]
  (println "⚔️  [PANDORA] Iniciando asalto completo...")
  (let [vectors (remove #(contains? exclude (key %)) attack-catalog)
        results (doall
                  (for [[k _] vectors]
                    (do (print (str "  🎯 " (name k) "... "))
                        (let [r (probe target-fn k :schema schema)]
                          (println (if (:vulnerable r) "💥 VULNERABLE" "✅ resistió"))
                          r))))
        vulns   (filter :vulnerable results)]

    (println "")
    (println (str "═══ PANDORA Report ═══"))
    (println (str "  Vectores probados: " (count results)))
    (println (str "  Vulnerabilidades:  " (count vulns)))
    (when (seq vulns)
      (println "  Críticas:")
      (doseq [v (filter #(= :high (:severity %)) vulns)]
        (println (str "    💀 " (:name v) ": " (get-in v [:exception :message])))))

    {:total-probes      (count results)
     :vulnerabilities   (count vulns)
     :critical          (count (filter #(= :high (:severity %)) vulns))
     :results           results
     :verdict           (cond
                          (> (count (filter #(= :high (:severity %)) vulns)) 0)
                          :CRITICAL

                          (> (count vulns) 2)
                          :WEAK

                          (> (count vulns) 0)
                          :ACCEPTABLE

                          :else
                          :HARDENED)}))


;; ─── Chaos Campaign (Estrés sostenido) ──────────────────────────


(defn chaos-campaign
  "Campaña de caos: ejecutar ataques aleatorios durante N iteraciones.
   Simula un adversario persistente e impredecible."
  [target-fn iterations & {:keys [report-every] :or {report-every 10}}]
  (println (str "🌪️  [PANDORA] Campaña de caos: " iterations " iteraciones"))
  (let [vector-keys (vec (keys attack-catalog))
        results     (atom {:hits 0 :misses 0 :errors []})]

    (dotimes [i iterations]
      (let [attack-key (rand-nth vector-keys)
            result     (probe target-fn attack-key)]
        (if (:vulnerable result)
          (swap! results update :hits inc)
          (swap! results update :misses inc))
        (when (:vulnerable result)
          (swap! results update :errors conj
                 {:iteration i :vector attack-key :error (:exception result)}))
        (when (and (pos? report-every)
                   (zero? (mod (inc i) report-every)))
          (let [r @results]
            (println (str "  [" (inc i) "/" iterations "] "
                          "Hits: " (:hits r) " Misses: " (:misses r)))))))

    (let [r @results]
      (println (str "\n🌪️  Campaña completa. Hits: " (:hits r)
                    "/" iterations " (" (format "%.1f" (* 100.0 (/ (:hits r) (max iterations 1)))) "%)"))
      @results)))
