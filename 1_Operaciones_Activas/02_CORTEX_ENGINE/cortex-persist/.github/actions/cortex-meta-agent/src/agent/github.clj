(ns agent.github
  "GitHub API client — Sovereign interface to the GitHub REST API.

   All functions take a `ctx` map with:
     :token    — GitHub token (GITHUB_TOKEN)
     :repo     — owner/repo string
     :api-url  — GitHub API base URL (default: https://api.github.com)

   Reality Level: C5-REAL"
  (:require [babashka.http-client :as http]
            [cheshire.core :as json]))


(defn- base-url [{:keys [api-url] :or {api-url "https://api.github.com"}}]
  api-url)


(defn- headers [{:keys [token]}]
  {"Authorization" (str "Bearer " token)
   "Accept"        "application/vnd.github+json"
   "X-GitHub-Api-Version" "2022-11-28"
   "User-Agent"    "CORTEX-Meta-Agent/1.0"})


(defn- api-get
  "GET request to GitHub API. Returns parsed JSON body."
  [ctx path]
  (let [resp (http/get (str (base-url ctx) path)
                       {:headers (headers ctx)
                        :throw false})]
    (when (= 200 (:status resp))
      (json/parse-string (:body resp) true))))


(defn- api-post
  "POST request to GitHub API."
  [ctx path body]
  (let [resp (http/post (str (base-url ctx) path)
                        {:headers (merge (headers ctx)
                                         {"Content-Type" "application/json"})
                         :body    (json/generate-string body)
                         :throw   false})]
    {:status (:status resp)
     :body   (when (:body resp)
               (try (json/parse-string (:body resp) true)
                    (catch Exception _ (:body resp))))}))


(defn- api-patch
  "PATCH request to GitHub API."
  [ctx path body]
  (let [resp (http/patch (str (base-url ctx) path)
                         {:headers (merge (headers ctx)
                                          {"Content-Type" "application/json"})
                          :body    (json/generate-string body)
                          :throw   false})]
    {:status (:status resp)
     :body   (when (:body resp)
               (try (json/parse-string (:body resp) true)
                    (catch Exception _ (:body resp))))}))


;; ─── Pull Request Operations ────────────────────────────────────


(defn get-pr
  "Fetch a pull request by number."
  [ctx pr-number]
  (api-get ctx (str "/repos/" (:repo ctx) "/pulls/" pr-number)))


(defn get-pr-files
  "List files changed in a pull request."
  [ctx pr-number]
  (api-get ctx (str "/repos/" (:repo ctx) "/pulls/" pr-number "/files")))


(defn add-labels
  "Add labels to an issue or pull request."
  [ctx issue-number labels]
  (api-post ctx
            (str "/repos/" (:repo ctx) "/issues/" issue-number "/labels")
            {:labels labels}))


(defn add-comment
  "Add a comment to an issue or pull request."
  [ctx issue-number body]
  (api-post ctx
            (str "/repos/" (:repo ctx) "/issues/" issue-number "/comments")
            {:body body}))


;; ─── Issue Operations ───────────────────────────────────────────


(defn get-issue
  "Fetch an issue by number."
  [ctx issue-number]
  (api-get ctx (str "/repos/" (:repo ctx) "/issues/" issue-number)))


(defn list-issues
  "List open issues."
  [ctx & {:keys [labels state per-page]
          :or   {state "open" per-page 30}}]
  (api-get ctx (str "/repos/" (:repo ctx) "/issues"
                    "?state=" state
                    "&per_page=" per-page
                    (when labels (str "&labels=" labels)))))


(defn assign-issue
  "Assign users to an issue."
  [ctx issue-number assignees]
  (api-post ctx
            (str "/repos/" (:repo ctx) "/issues/" issue-number "/assignees")
            {:assignees assignees}))


;; ─── Workflow Operations ────────────────────────────────────────


(defn list-workflows
  "List all workflow files in the repository."
  [ctx]
  (api-get ctx (str "/repos/" (:repo ctx) "/actions/workflows")))


(defn list-workflow-runs
  "List recent workflow runs."
  [ctx & {:keys [status per-page] :or {per-page 10}}]
  (api-get ctx (str "/repos/" (:repo ctx) "/actions/runs"
                    "?per_page=" per-page
                    (when status (str "&status=" status)))))


(defn get-workflow-run
  "Get details of a specific workflow run."
  [ctx run-id]
  (api-get ctx (str "/repos/" (:repo ctx) "/actions/runs/" run-id)))


;; ─── Repository Operations ──────────────────────────────────────


(defn get-file-content
  "Get file content from the repository (decoded from base64)."
  [ctx path & {:keys [ref] :or {ref "main"}}]
  (let [resp (api-get ctx (str "/repos/" (:repo ctx) "/contents/" path "?ref=" ref))]
    (when resp
      (assoc resp :decoded-content
             (when-let [content (:content resp)]
               (-> content
                   (.replaceAll "\\n" "")
                   (java.util.Base64/getDecoder)
                   (.decode)
                   (String.)))))))


(defn create-or-update-file
  "Create or update a file in the repository."
  [ctx path content message & {:keys [branch sha]}]
  (api-patch ctx
             (str "/repos/" (:repo ctx) "/contents/" path)
             (cond-> {:message message
                      :content (-> content
                                   (.getBytes "UTF-8")
                                   (java.util.Base64/getEncoder)
                                   (.encodeToString))}
               branch (assoc :branch branch)
               sha    (assoc :sha sha))))


;; ─── Context Builder ────────────────────────────────────────────


(defn make-ctx
  "Build a GitHub API context from environment variables."
  []
  {:token   (System/getenv "GITHUB_TOKEN")
   :repo    (System/getenv "GITHUB_REPOSITORY")
   :api-url (or (System/getenv "GITHUB_API_URL") "https://api.github.com")})
