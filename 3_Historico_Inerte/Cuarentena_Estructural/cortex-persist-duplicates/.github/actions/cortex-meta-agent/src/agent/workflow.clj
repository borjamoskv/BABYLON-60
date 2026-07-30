(ns agent.workflow
  "Workflow Manipulation Engine — Code-as-Data for GitHub Actions YAML.

   Treats GitHub Actions workflow YAML files as Clojure data structures.
   Read → manipulate → write back. This IS code-as-data applied to CI/CD.

   The workflow definition is simultaneously:
   - A YAML file (serialized form)
   - A Clojure map (manipulable data)
   - An executable specification (GitHub interprets it)

   This is the L7 primitive: the agent can inspect and rewrite its own
   workflow definition at runtime.

   Reality Level: C5-REAL"
  (:require [clj-yaml.core :as yaml]
            [clojure.string :as str]))


;; ─── YAML ↔ Data Transformations ────────────────────────────────


(defn parse-workflow
  "Parse a YAML workflow string into a Clojure map (data → code-as-data)."
  [yaml-str]
  (yaml/parse-string yaml-str))


(defn emit-workflow
  "Emit a Clojure map back to YAML string (code-as-data → data)."
  [workflow-map]
  (yaml/generate-string workflow-map :dumper-options {:flow-style :block}))


;; ─── Workflow Introspection (reflect) ───────────────────────────


(defn list-jobs
  "Extract all job names from a workflow."
  [workflow]
  (keys (:jobs workflow)))


(defn list-steps
  "Extract all steps from a specific job."
  [workflow job-name]
  (get-in workflow [:jobs job-name :steps]))


(defn list-triggers
  "Extract all event triggers from a workflow."
  [workflow]
  (let [on-clause (:on workflow)]
    (cond
      (string? on-clause) [on-clause]
      (vector? on-clause) on-clause
      (map? on-clause)    (keys on-clause)
      :else               [])))


(defn find-steps-by-uses
  "Find all steps using a specific action (e.g., 'actions/checkout@v4')."
  [workflow action-prefix]
  (for [[job-name job-config] (:jobs workflow)
        step                  (:steps job-config)
        :when (and (:uses step)
                   (str/starts-with? (:uses step) action-prefix))]
    (assoc step :_job job-name)))


(defn workflow-stats
  "Compute statistics about a workflow (node count, depth, complexity)."
  [workflow]
  (let [jobs  (:jobs workflow)
        steps (mapcat :steps (vals jobs))]
    {:name       (:name workflow)
     :triggers   (list-triggers workflow)
     :job-count  (count jobs)
     :step-count (count steps)
     :uses-actions (distinct (keep :uses steps))
     :has-matrix? (some #(get-in (val %) [:strategy :matrix]) jobs)
     :has-secrets? (some #(str/includes? (str %) "secrets.") (map str steps))}))


;; ─── Workflow Rewriting (rewrite) ───────────────────────────────


(defn add-step-to-job
  "Add a step to a specific job. Position: :first, :last, or integer index."
  [workflow job-name step & {:keys [position] :or {position :last}}]
  (let [current-steps (get-in workflow [:jobs job-name :steps] [])]
    (assoc-in workflow [:jobs job-name :steps]
              (case position
                :first (into [step] current-steps)
                :last  (conj current-steps step)
                ;; Integer index
                (let [idx (min position (count current-steps))]
                  (into (subvec (vec current-steps) 0 idx)
                        (cons step (subvec (vec current-steps) idx))))))))


(defn remove-step-from-job
  "Remove a step by name from a job."
  [workflow job-name step-name]
  (update-in workflow [:jobs job-name :steps]
             (fn [steps]
               (filterv #(not= (:name %) step-name) steps))))


(defn add-job
  "Add a new job to the workflow."
  [workflow job-name job-config]
  (assoc-in workflow [:jobs job-name] job-config))


(defn remove-job
  "Remove a job from the workflow."
  [workflow job-name]
  (update workflow :jobs dissoc job-name))


(defn set-trigger
  "Add or replace a trigger event."
  [workflow event config]
  (assoc-in workflow [:on event] config))


(defn add-env-to-job
  "Add environment variables to a job."
  [workflow job-name env-map]
  (update-in workflow [:jobs job-name :env] merge env-map))


(defn pin-action-version
  "Pin all uses of an action to a specific version/SHA."
  [workflow action-prefix new-version]
  (let [update-steps (fn [steps]
                       (mapv (fn [step]
                               (if (and (:uses step)
                                        (str/starts-with? (:uses step) action-prefix))
                                 (assoc step :uses (str action-prefix "@" new-version))
                                 step))
                             steps))]
    (update workflow :jobs
            (fn [jobs]
              (into {}
                    (map (fn [[k v]]
                           [k (update v :steps update-steps)])
                         jobs))))))


(defn add-timeout-to-jobs
  "Add timeout-minutes to all jobs that don't have one."
  [workflow timeout-minutes]
  (update workflow :jobs
          (fn [jobs]
            (into {}
                  (map (fn [[k v]]
                         [k (if (:timeout-minutes v)
                              v
                              (assoc v :timeout-minutes timeout-minutes))])
                       jobs)))))


(defn add-concurrency-guard
  "Add concurrency control to prevent duplicate runs."
  [workflow group cancel-in-progress?]
  (assoc workflow :concurrency
         {:group group
          :cancel-in-progress cancel-in-progress?}))


;; ─── Self-Modification Primitives ───────────────────────────────


(defn inject-reflexion-step
  "Inject a reflexion step after every job — the agent monitors itself.

   This is L5 self-healing: after each job, emit telemetry about
   success/failure for the reflexion loop to consume."
  [workflow]
  (let [reflexion-step {:name "🔄 CORTEX Reflexion Checkpoint"
                        :if   "always()"
                        :run  (str/join "\n"
                                ["echo '::group::CORTEX Reflexion'"
                                 "echo \"Job: ${{ github.job }}\""
                                 "echo \"Status: ${{ job.status }}\""
                                 "echo \"Run: ${{ github.run_id }}\""
                                 "echo \"Attempt: ${{ github.run_attempt }}\""
                                 "echo '::endgroup::'"])}]
    (update workflow :jobs
            (fn [jobs]
              (into {}
                    (map (fn [[k v]]
                           [k (update v :steps conj reflexion-step)])
                         jobs))))))


(defn evolve-workflow
  "Apply a sequence of transformations to a workflow (pipeline of rewrites).

   Each transformation is a function [workflow -> workflow].
   This is the Clojure equivalent of the ISA builder's seq() — but for CI/CD.

   Example:
     (evolve-workflow base-wf
       (partial add-timeout-to-jobs 30)
       inject-reflexion-step
       (partial add-concurrency-guard \"${{ github.workflow }}\" true))
  "
  [workflow & transforms]
  (reduce (fn [wf xform] (xform wf)) workflow transforms))
