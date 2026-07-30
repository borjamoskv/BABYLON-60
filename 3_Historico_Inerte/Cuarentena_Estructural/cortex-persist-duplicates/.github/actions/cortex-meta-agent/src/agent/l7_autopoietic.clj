(ns agent.l7-autopoietic
  "████████████ NIVEL 7 — AGENTE AUTOPOIÉTICO ████████████

   MÖBIUS L7: El agente que se reescribe a sí mismo.

   En cualquier otro lenguaje, esto es ciencia ficción.
   En Clojure, es una función de 3 líneas.

   ¿Por qué? Porque en Clojure:
   - El código fuente es una lista:       '(defn f [x] (+ x 1))
   - Las listas son datos manipulables:   (assoc-in tree [2] '(* x 2))
   - Los datos se pueden evaluar:         (eval modified-code)
   - Ergo: el agente lee su código, lo modifica, y lo ejecuta.

   ESTO es el Principio de Möbius:
   El código que ejecuta el agente ES los datos que el agente manipula.
   No hay frontera. Una sola superficie continua. ∞

   Autopoiesis (Maturana & Varela, 1972):
   'Un sistema autopoiético es aquel que se produce continuamente
    a sí mismo como unidad en el espacio.'

   El agente L7 no solo se repara (L5) ni solo piensa sobre sí (L6).
   El agente L7 SE REDEFINE: genera nuevas versiones de sus propias
   funciones, las evalúa, y las instala como su nuevo comportamiento.

   Reality Level: C5-REAL"
  (:require [clojure.string :as str]
            [agent.l5-healer :as l5]
            [agent.l6-metacog :as l6]))


;; ─── Gene Pool (El genoma del agente) ───────────────────────────
;;
;; En Clojure, el "genoma" del agente son sus funciones.
;; Las funciones son datos (listas). Los datos son manipulables.
;; Ergo: el genoma es mutable por el propio agente.


(defn make-genome
  "Crear el genoma del agente: un registro de todas sus funciones
   como DATOS (quoted forms) que pueden ser inspeccionadas y modificadas.

   Cada gen es:
   {:name    keyword
    :code    quoted-form (la función como dato)
    :version int
    :lineage [versiones anteriores]
    :fitness float (0.0 - 1.0)}"
  []
  (atom
    {:genes
     {;; Gen: función de scoring
      :scorer
      {:name    :scorer
       :code    '(fn [item]
                  (let [base  (:relevance item 0)
                        boost (if (:verified item) 1.5 1.0)
                        decay (Math/exp (- (* 0.01 (:age-days item 0))))]
                    (* base boost decay)))
       :version 1
       :lineage []
       :fitness 0.5}

      ;; Gen: función de filtrado
      :filter
      {:name    :filter
       :code    '(fn [items threshold]
                  (filter #(> (:score % 0) threshold) items))
       :version 1
       :lineage []
       :fitness 0.5}

      ;; Gen: función de ranking
      :ranker
      {:name    :ranker
       :code    '(fn [items]
                  (->> items
                       (sort-by :score >)
                       (take 10)))
       :version 1
       :lineage []
       :fitness 0.5}

      ;; Gen: función de dispatch
      :dispatcher
      {:name    :dispatcher
       :code    '(fn [task agents]
                  (let [best (first (sort-by :load < agents))]
                    {:assigned-to (:id best)
                     :task        task}))
       :version 1
       :lineage []
       :fitness 0.5}}

     :generation    0
     :total-mutations 0
     :evolution-log  []}))


;; ─── Introspection (El agente lee su propio código) ─────────────


(defn inspect-gene
  "Inspeccionar un gen: el agente LEE su propia función como dato.

   Esto es trivial en Clojure porque las funciones SON datos.
   En Python/Java necesitarías AST parsing. Aquí es (get genes :name)."
  [genome gene-name]
  (get-in @genome [:genes gene-name]))


(defn list-genes
  "Listar todos los genes del agente con sus metadatos."
  [genome]
  (->> (:genes @genome)
       (map (fn [[k v]]
              {:name    k
               :version (:version v)
               :fitness (:fitness v)
               :code-size (count (str (:code v)))}))
       (sort-by :name)))


(defn gene-code
  "Extraer el código de un gen como string legible."
  [genome gene-name]
  (some-> (inspect-gene genome gene-name)
          :code
          pr-str))


;; ─── Mutation (El agente modifica su propio código) ─────────────


(defn mutate-gene!
  "MUTACIÓN: El agente modifica uno de sus propios genes.

   Toma un gen y una función de transformación que recibe el
   código (como dato) y retorna código modificado (como dato).

   Ejemplo:
     ;; Cambiar el decay factor de 0.01 a 0.05
     (mutate-gene! genome :scorer
       (fn [code]
         (clojure.walk/postwalk
           (fn [form]
             (if (= form 0.01) 0.05 form))
           code)))

   Esto es L7 puro: el agente manipula SU PROPIA función como datos."
  [genome gene-name transform-fn & {:keys [reason] :or {reason "autonomous"}}]
  (let [current    (inspect-gene genome gene-name)
        old-code   (:code current)
        new-code   (transform-fn old-code)
        new-version (inc (:version current))]

    (println (str "🧬 [L7] MUTACIÓN: " (name gene-name)
                  " v" (:version current) " → v" new-version
                  " (" reason ")"))

    (swap! genome
           (fn [g]
             (-> g
                 (assoc-in [:genes gene-name :code] new-code)
                 (assoc-in [:genes gene-name :version] new-version)
                 (update-in [:genes gene-name :lineage] conj old-code)
                 (update :total-mutations inc)
                 (update :evolution-log conj
                         {:gene      gene-name
                          :from      (:version current)
                          :to        new-version
                          :reason    reason
                          :timestamp (System/currentTimeMillis)}))))

    ;; Retornar la diff conceptual
    {:gene        gene-name
     :old-version (:version current)
     :new-version new-version
     :old-code    (pr-str old-code)
     :new-code    (pr-str new-code)}))


;; ─── Compilation (De dato a función ejecutable) ─────────────────


(defn compile-gene
  "COMPILAR: Convertir un gen (dato) en una función ejecutable.

   Este es el momento Möbius:
   - El gen es un DATO (una lista Clojure)
   - eval lo convierte en una FUNCIÓN
   - La función ES el comportamiento del agente
   - El agente puede volver a leerla como dato
   - ∞ El loop nunca termina"
  [genome gene-name]
  (let [gene (inspect-gene genome gene-name)
        code (:code gene)]
    (try
      (eval code)
      (catch Exception e
        (println (str "  ❌ Compilation failed for " (name gene-name) ": " (ex-message e)))
        nil))))


(defn compile-all-genes
  "Compilar todo el genoma en un mapa de funciones ejecutables."
  [genome]
  (->> (:genes @genome)
       (map (fn [[k _]] [k (compile-gene genome k)]))
       (filter (fn [[_ v]] (some? v)))
       (into {})))


;; ─── Fitness Evaluation ─────────────────────────────────────────


(defn evaluate-fitness!
  "Evaluar el fitness de un gen ejecutándolo contra casos de test.

   El agente evalúa la CALIDAD de su propio código.
   Esto es metacognición (L6) aplicada a autopoiesis (L7)."
  [genome gene-name test-cases]
  (let [compiled (compile-gene genome gene-name)]
    (if-not compiled
      (do (swap! genome assoc-in [:genes gene-name :fitness] 0.0)
          0.0)

      (let [results  (for [{:keys [input expected]} test-cases]
                       (try
                         (let [actual (apply compiled input)]
                           {:pass? (= actual expected)
                            :input input
                            :expected expected
                            :actual actual})
                         (catch Exception e
                           {:pass? false :error (ex-message e)})))
            fitness  (/ (count (filter :pass? results))
                        (max (count results) 1))]

        (swap! genome assoc-in [:genes gene-name :fitness] (float fitness))

        (println (str "  📊 Fitness de :" (name gene-name)
                      " = " (format "%.2f" (float fitness))
                      " (" (count (filter :pass? results))
                      "/" (count results) " tests)"))
        (float fitness)))))


;; ─── Evolution (El loop autopoiético) ───────────────────────────


(defn evolve-gene!
  "EVOLUCIÓN AUTOPOIÉTICA: El agente intenta mejorar un gen.

   1. Evalúa fitness actual
   2. Si es bajo, aplica una estrategia de mutación
   3. Re-evalúa fitness
   4. Si mejoró, mantiene la mutación
   5. Si empeoró, revierte (rollback)

   Esto es selección natural dentro de un solo agente."
  [genome gene-name test-cases mutation-fn & {:keys [reason] :or {reason "evolution"}}]
  (println (str "🧬 [L7] Evolución de :" (name gene-name) "..."))

  ;; Fitness antes
  (let [fitness-before (evaluate-fitness! genome gene-name test-cases)
        old-gene       (inspect-gene genome gene-name)]

    ;; Mutar
    (mutate-gene! genome gene-name mutation-fn :reason reason)

    ;; Fitness después
    (let [fitness-after (evaluate-fitness! genome gene-name test-cases)]

      (if (> fitness-after fitness-before)
        ;; MEJORA — mantener mutación
        (do
          (println (str "  ✅ Evolución exitosa: "
                        (format "%.2f" fitness-before) " → "
                        (format "%.2f" fitness-after)))
          {:evolved?  true
           :before    fitness-before
           :after     fitness-after
           :gene      gene-name
           :version   (:version (inspect-gene genome gene-name))})

        ;; REGRESIÓN — rollback
        (do
          (println (str "  ↩️  Rollback: fitness no mejoró ("
                        (format "%.2f" fitness-before) " → "
                        (format "%.2f" fitness-after) ")"))
          (swap! genome assoc-in [:genes gene-name] old-gene)
          {:evolved?  false
           :before    fitness-before
           :after     fitness-after
           :gene      gene-name
           :reason    :regression-rollback})))))


;; ─── The Autopoietic Loop ───────────────────────────────────────


(defn autopoietic-cycle!
  "UN CICLO COMPLETO DE AUTOPOIESIS:

   El agente:
   1. OBSERVA su propio rendimiento (L5 monitoring)
   2. PIENSA sobre qué genes tienen bajo fitness (L6 metacognition)
   3. GENERA mutaciones (L7 autopoiesis)
   4. EVALÚA las mutaciones y las mantiene o revierte
   5. INCREMENTA su generación

   Cada ciclo produce un agente ligeramente diferente.
   El agente que termina el ciclo NO es el mismo que lo empezó.
   Se ha producido a sí mismo. Autopoiesis."
  [genome test-suite mutation-strategies]
  (println "")
  (println "╔══════════════════════════════════════════════╗")
  (println "║  ∞ AUTOPOIESIS CYCLE                        ║")
  (println (str "║  Generation: " (format "%-34d" (:generation @genome)) "║"))
  (println "╚══════════════════════════════════════════════╝")
  (println "")

  (let [genes      (keys (:genes @genome))
        results    (for [gene-name genes
                         :let [tests     (get test-suite gene-name [])
                               mutation  (get mutation-strategies gene-name identity)]
                         :when (seq tests)]
                     (evolve-gene! genome gene-name tests mutation
                                   :reason "autopoietic-cycle"))
        evolved    (filter :evolved? results)
        generation (swap! genome update :generation inc)]

    (println "")
    (println (str "═══ Generación " (:generation @genome) " completada ═══"))
    (println (str "  Genes evaluados: " (count results)))
    (println (str "  Evoluciones exitosas: " (count evolved)))
    (println (str "  Mutaciones totales: " (:total-mutations @genome)))

    {:generation  (:generation @genome)
     :evaluated   (count results)
     :evolved     (count evolved)
     :results     (vec results)}))


;; ─── The Unified Agent (L5 + L6 + L7) ──────────────────────────


(defn make-mobius-agent
  "Crear un agente MÖBIUS completo que integra los tres niveles:
   - L5 (Self-Healing): via agent.l5-healer
   - L6 (Metacognition): via agent.l6-metacog
   - L7 (Autopoiesis): via este namespace

   El agente resultante puede:
   - Ejecutar tareas con auto-curación
   - Pensar sobre su propio rendimiento
   - Reescribir su propio código"
  []
  {:genome     (make-genome)
   :self-model (l6/make-self-model)
   :level      :L7-autopoietic
   :identity   "∞ MÖBIUS — Where Code IS Data IS Code"})


(defn execute!
  "Punto de entrada unificado. Ejecuta con las tres capas activas:

   L7 compila el gen → L6 evalúa si puede ejecutar → L5 ejecuta con healing

   Esto es la banda de Möbius completa:
   El código se lee, se evalúa, se ejecuta, se mide, se reescribe, se re-evalúa..."
  [{:keys [genome self-model]} gene-name args
   & {:keys [domain] :or {domain :general}}]
  (println (str "\n∞ [MÖBIUS] Ejecutando :" (name gene-name)
                " (L7→L6→L5)..."))

  ;; L7: Compilar gen a función
  (let [compiled-fn (compile-gene genome gene-name)]
    (if-not compiled-fn
      {:verdict :compilation-error
       :gene    gene-name
       :message "Gen no compilable"}

      ;; L6: Evaluación metacognitiva
      (l6/metacognitive-execute
        self-model
        ;; L5: Ejecutar con self-healing
        (fn [& inner-args]
          (:result
            (l5/self-healing-execute compiled-fn inner-args)))
        args
        :domain domain
        :task-id (str (name gene-name) "-" (System/currentTimeMillis))))))
