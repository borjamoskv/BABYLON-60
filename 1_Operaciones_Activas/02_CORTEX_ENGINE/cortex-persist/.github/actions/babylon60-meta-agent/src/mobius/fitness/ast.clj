(ns mobius.fitness.ast)

(def branch-ops
  '#{if when when-not cond case})

(defn ast-depth [form]
  (if (coll? form)
    (inc (apply max 0 (map ast-depth form)))
    0))

(defn branch-count [form]
  (cond
    (seq? form)
    (+ (if (contains? branch-ops (first form)) 1 0)
       (reduce + (map branch-count form)))

    (coll? form)
    (reduce + (map branch-count form))

    :else
    0))

(defn node-count [form]
  (if (coll? form)
    (inc (reduce + (map node-count form)))
    1))

(defn recursive-calls [form target-fn]
    (cond
        (seq? form)
        (+ (if (= (first form) target-fn) 1 0)
           (if (= (first form) 'recur) 1 0)
           (reduce + (map #(recursive-calls % target-fn) form)))
        (coll? form)
        (reduce + (map #(recursive-calls % target-fn) form))
        :else
        0))

(defn complexity [form target-fn]
  (let [depth (ast-depth form)
        branches (branch-count form)
        recursion (recursive-calls form target-fn)]
    (+ branches
       recursion
       (* depth 0.5))))

(defn ast-complexity-report [form target-fn]
    {:ast-depth (ast-depth form)
     :branches (branch-count form)
     :recursive-calls (recursive-calls form target-fn)
     :node-count (node-count form)
     :complexity (complexity form target-fn)})

(defn fitness-score
  [{:keys [w-causal
           w-speed
           c-ast
           e-tokens
           r-stability]}]
  (if (or (zero? (+ c-ast e-tokens)) (zero? r-stability))
      0
      (/ (* w-causal w-speed r-stability)
         (+ c-ast e-tokens))))

(defn survival?
  [baseline score]
  (if (zero? baseline)
      true
      (> (/ score baseline) 1.15)))
