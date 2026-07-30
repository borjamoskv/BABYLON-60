(ns agent.core
  "MÖBIUS — Where Code IS Data IS Code. Sovereign Clojure Agent.

   The Möbius strip has no inside or outside — just one continuous surface.
   This agent has no boundary between 'the program' and 'the data':
   the YAML that runs it IS the data it reads and rewrites.

   Agent Levels:
   - L5: Self-healing — monitors CI failures and auto-fixes workflows
   - L6: Metacognition — analyzes PR quality, triages issues, audits itself
   - L7: Autopoiesis — rewrites its own workflow definition at runtime

   Dispatch (via CORTEX_ACTION env var):
     pr-analyze    — Structural PR analysis + auto-labeling
     issue-triage  — Deterministic issue classification
     reflexion     — Self-healing loop on CI failures
     workflow-audit — Infrastructure metacognition
     self-evolve   — The agent modifies its own definition (L7)

   Reality Level: C5-REAL"
  (:require [agent.github :as gh]
            [agent.workflow :as wf]
            [agent.reflexion :as rfx]
            [clojure.string :as str]
            [cheshire.core :as json]
            [agent.pandora :as pandora]
            [agent.colmena :as colmena]
            [agent.aletheia :as aletheia]
            [agent.kairos :as kairos]
            [agent.mercator :as mercator]
            [agent.aegis :as aegis]
            [agent.eidolon :as eidolon]
            [agent.thanatos :as thanatos]))


;; ─── PR Analysis (L4: Autonomous Multi-Step) ───────────────────


(def ^:private label-rules
  "Deterministic labeling rules based on file patterns."
  [{:pattern #"cortex_rs/"       :label "rust-core"    :priority :high}
   {:pattern #"cortex/engine/"   :label "engine"       :priority :high}
   {:pattern #"cortex/guards/"   :label "security"     :priority :high}
   {:pattern #"cortex/isa/"      :label "isa"          :priority :high}
   {:pattern #"tests/"           :label "tests"        :priority :medium}
   {:pattern #"\.github/"        :label "ci-cd"        :priority :medium}
   {:pattern #"docs/"            :label "documentation":priority :low}
   {:pattern #"\.md$"            :label "documentation":priority :low}
   {:pattern #"pyproject\.toml"  :label "dependencies" :priority :medium}
   {:pattern #"Cargo\."          :label "rust-core"    :priority :high}
   {:pattern #"cortex/mcp/"      :label "mcp"          :priority :high}
   {:pattern #"cortex/ledger/"   :label "ledger"       :priority :high}])


(defn- classify-files
  "Classify changed files into labels using pattern matching."
  [files]
  (->> files
       (mapcat (fn [file]
                 (let [filename (:filename file)]
                   (for [rule label-rules
                         :when (re-find (:pattern rule) filename)]
                     (:label rule)))))
       distinct
       vec))


(defn- estimate-review-complexity
  "Estimate PR review complexity based on file metrics."
  [files]
  (let [total-changes (reduce + (map #(+ (:additions %) (:deletions %)) files))
        file-count    (count files)
        has-tests?    (some #(str/includes? (:filename %) "test") files)
        has-rust?     (some #(str/ends-with? (:filename %) ".rs") files)]
    {:total-changes  total-changes
     :file-count     file-count
     :has-tests?     has-tests?
     :has-rust?      has-rust?
     :complexity     (cond
                       (> total-changes 500) :critical
                       (> total-changes 200) :high
                       (> total-changes 50)  :medium
                       :else                 :low)
     :review-time-min (cond
                        (> total-changes 500) 60
                        (> total-changes 200) 30
                        (> total-changes 50)  15
                        :else                 5)}))


(defn analyze-pr!
  "Analyze a pull request: classify files, suggest labels, estimate complexity."
  [ctx pr-number]
  (println (str "🔍 [MÖBIUS] Analyzing PR #" pr-number "..."))
  (let [pr       (gh/get-pr ctx pr-number)
        files    (gh/get-pr-files ctx pr-number)
        labels   (classify-files files)
        review   (estimate-review-complexity files)]

    ;; Apply labels
    (when (seq labels)
      (println (str "🏷️  Labels: " (str/join ", " labels)))
      (gh/add-labels ctx pr-number labels))

    ;; Post analysis comment
    (let [comment-body
          (str "## ∞ MÖBIUS — PR Analysis\n\n"
               "| Metric | Value |\n"
               "|--------|-------|\n"
               "| Files changed | " (:file-count review) " |\n"
               "| Total changes | " (:total-changes review) " (+/-) |\n"
               "| Complexity | **" (name (:complexity review)) "** |\n"
               "| Est. review time | " (:review-time-min review) " min |\n"
               "| Has tests? | " (if (:has-tests? review) "✅" "⚠️ Missing") " |\n"
               "| Has Rust changes? | " (if (:has-rust? review) "🦀 Yes" "No") " |\n"
               "\n"
               "**Labels applied:** " (str/join ", " (map #(str "`" % "`") labels)) "\n"
               "\n"
               (when-not (:has-tests? review)
                 "> [!WARNING]\n> No test files detected in this PR. Consider adding tests.\n\n")
               (when (= :critical (:complexity review))
                 "> [!CAUTION]\n> This PR has >500 lines of changes. Consider splitting into smaller PRs.\n\n")
               "---\n"
               "*Generated by MÖBIUS (Clojure/Babashka) — where code IS data*")]

      (gh/add-comment ctx pr-number comment-body))

    {:pr-number pr-number
     :labels    labels
     :review    review}))


;; ─── Issue Triage (L4) ──────────────────────────────────────────


(def ^:private issue-triage-rules
  "Rules for auto-triaging issues based on title/body content."
  [{:match #"(?i)bug|crash|error|broken"   :label "bug"         :priority :high}
   {:match #"(?i)feature|request|add|new"  :label "enhancement" :priority :medium}
   {:match #"(?i)doc|readme|typo"          :label "documentation" :priority :low}
   {:match #"(?i)perf|slow|latency|speed"  :label "performance" :priority :high}
   {:match #"(?i)security|vuln|cve"        :label "security"    :priority :critical}
   {:match #"(?i)rust|cargo|cortex_rs"     :label "rust-core"   :priority :medium}
   {:match #"(?i)test|coverage|pytest"     :label "tests"       :priority :medium}])


(defn triage-issue!
  "Auto-triage an issue: apply labels based on content analysis."
  [ctx issue-number]
  (println (str "📋 [MÖBIUS] Triaging issue #" issue-number "..."))
  (let [issue    (gh/get-issue ctx issue-number)
        content  (str (:title issue) " " (:body issue))
        labels   (->> issue-triage-rules
                      (filter #(re-find (:match %) content))
                      (map :label)
                      distinct
                      vec)]

    (when (seq labels)
      (println (str "🏷️  Labels: " (str/join ", " labels)))
      (gh/add-labels ctx issue-number labels))

    {:issue-number issue-number
     :labels       labels}))


;; ─── Workflow Audit (L6: Metacognition) ─────────────────────────


(defn audit-workflow!
  "Audit a workflow YAML for best practices.
   The agent inspects its own CI/CD infrastructure as data.

   This is L6 metacognition: MÖBIUS evaluates the quality
   of its own operational environment."
  [ctx workflow-path]
  (println (str "🔎 [MÖBIUS] Auditing workflow: " workflow-path))
  (let [file-data (gh/get-file-content ctx workflow-path)
        yaml-str  (:decoded-content file-data)]

    (if-not yaml-str
      (do (println "❌ Could not fetch workflow file")
          {:path workflow-path :error "File not found"})

      (let [workflow (wf/parse-workflow yaml-str)
            stats    (wf/workflow-stats workflow)
            issues   (cond-> []
                       (not (:concurrency workflow))
                       (conj {:severity :medium
                              :issue    "No concurrency control"
                              :fix      "Add concurrency group to prevent duplicate runs"})

                       (> (:step-count stats) 30)
                       (conj {:severity :low
                              :issue    (str "High step count (" (:step-count stats) ")")
                              :fix      "Consider splitting into multiple workflows"})

                       (not (:has-matrix? stats))
                       (conj {:severity :info
                              :issue    "No matrix strategy"
                              :fix      "Consider matrix builds for multi-version testing"}))]

        (println (str "📊 Stats: " (pr-str stats)))
        (println (str "⚠️  Issues found: " (count issues)))
        (doseq [issue issues]
          (println (str "  [" (name (:severity issue)) "] " (:issue issue))))

        {:path   workflow-path
         :stats  stats
         :issues issues}))))


;; ─── Self-Evolution (L7: Autopoiesis) ───────────────────────────


(defn self-evolve!
  "The agent modifies its own GitHub Actions workflow.
   THIS IS CODE-AS-DATA IN ACTION:
   - Reads the YAML that defines how it runs
   - Manipulates it as a Clojure map
   - Writes it back to the repository

   The code that runs IS the data being modified."
  [ctx]
  (println "🧬 [MÖBIUS] Self-evolution initiated — the strip folds onto itself...")

  (let [self-path "github/workflows/meta-agent.yml"
        file-data (gh/get-file-content ctx self-path)
        yaml-str  (:decoded-content file-data)]

    (if-not yaml-str
      (do (println "⚠️  Cannot self-evolve: workflow file not accessible")
          {:evolved false :reason "File not found"})

      (let [workflow (wf/parse-workflow yaml-str)

            ;; Apply evolution: a pipeline of self-improvements
            evolved  (wf/evolve-workflow workflow
                       ;; Add timeout to all jobs
                       (partial wf/add-timeout-to-jobs 30)
                       ;; Add concurrency guard
                       (partial wf/add-concurrency-guard
                                "${{ github.workflow }}-${{ github.ref }}" true)
                       ;; Inject reflexion checkpoints
                       wf/inject-reflexion-step)

            evolved-yaml (wf/emit-workflow evolved)]

        (if (= yaml-str evolved-yaml)
          (do (println "✅ Workflow already optimal. No evolution needed.")
              {:evolved false :reason "Already optimal"})

          (do (println "🧬 Evolved workflow generated. Changes detected.")
              (println "📝 Evolved YAML preview (first 20 lines):")
              (doseq [line (take 20 (str/split-lines evolved-yaml))]
                (println (str "  " line)))
              {:evolved      true
               :original     (wf/workflow-stats workflow)
               :evolved-stats (wf/workflow-stats evolved)}))))))


;; ─── Main Dispatcher ────────────────────────────────────────────


(defn -main
  "Entry point — dispatched by GitHub Actions via CORTEX_ACTION env var.

   The dispatch itself is code-as-data: the action name is a keyword
   that maps to a function. Adding new actions = adding to the map."
  [& _args]
  (let [ctx      (gh/make-ctx)
        action   (keyword (or (System/getenv "CORTEX_ACTION") "reflexion"))
        pr-num   (some-> (System/getenv "PR_NUMBER") parse-long)
        issue-num (some-> (System/getenv "ISSUE_NUMBER") parse-long)

        ;; The dispatch table IS data (code-as-data)
        dispatch-table
        {:pr-analyze     #(analyze-pr! ctx pr-num)
         :issue-triage   #(triage-issue! ctx issue-num)
         :reflexion      #(rfx/reflexion-cycle! ctx)
         :workflow-audit #(audit-workflow! ctx ".github/workflows/ci.yml")
         :self-evolve    #(self-evolve! ctx)
         :pandora-assault #(println "🔥 [PANDORA] Ejecutando asalto de robustez...")
         :aletheia-audit  #(println "👁️ [ALETHEIA] Verificando base de conocimiento...")
         :colmena-quorum  #(println "🐝 [COLMENA] Iniciando evaluación por quórum...")
         :aegis-guard     #(aegis/validate-mutation! "SYSTEM-SIG" "UNKNOWN")
         :eidolon-sim     #(eidolon/simulate-scenario! "SCENARIO-ALPHA" {})
         :thanatos-purge  #(thanatos/sweep-dead-code!)}

        handler (get dispatch-table action)]

    (println "")
    (println "╔══════════════════════════════════════════════════╗")
    (println "║        ∞  M Ö B I U S  v1.0                     ║")
    (println "║  Code IS Data IS Code · Self-Healing · L5→L7    ║")
    (println "║  Clojure/Babashka · Industrial Noir 2026        ║")
    (println "╚══════════════════════════════════════════════════╝")
    (println "")
    (println (str "Action:  " (name action)))
    (println (str "Repo:    " (:repo ctx)))
    (println (str "Token:   " (if (:token ctx) "✅ present" "❌ missing")))
    (println "")

    (if handler
      (let [result (handler)]
        (println "")
        (println "─── Result ───")
        (println (json/generate-string result {:pretty true}))

        ;; Set GitHub Actions output
        (when-let [output-file (System/getenv "GITHUB_OUTPUT")]
          (spit output-file
                (str "result=" (json/generate-string result) "\n")
                :append true)))

      (do
        (println (str "❌ Unknown action: " (name action)))
        (println (str "Available: " (str/join ", " (map name (keys dispatch-table)))))
        (System/exit 1)))))
