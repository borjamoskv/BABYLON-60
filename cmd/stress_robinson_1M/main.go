// Package stress — C5-REAL Robinson Resolution Stress Harness
// 1,000,000 iterations de resolución sobre el motor Go nativo.
// Sin I/O de red (Σ15 compliant). Puro CPU/WAM.
// Reporte: p50/p90/p95/p99/p100 latencias en nanosegundos.
package main

import (
	"fmt"
	"math/rand"
	"os"
	"sort"
	"time"
	"crypto/sha256"
	"encoding/hex"
	"strconv"
	"strings"
)

// ============================================================
// MOTOR DE RESOLUCIÓN DE ROBINSON (Go nativo — sin deps)
// ============================================================

type Literal struct {
	Atom     string
	Negated  bool
}

type Clause []Literal

func complementary(a, b Literal) bool {
	return a.Atom == b.Atom && a.Negated != b.Negated
}

func contains(c Clause, l Literal) bool {
	for _, lit := range c {
		if lit == l {
			return true
		}
	}
	return false
}

func erase(c Clause, l Literal) Clause {
	out := make(Clause, 0, len(c))
	removed := false
	for _, lit := range c {
		if !removed && lit == l {
			removed = true
			continue
		}
		out = append(out, lit)
	}
	return out
}

func dedupe(c Clause) Clause {
	seen := make(map[Literal]bool)
	out := make(Clause, 0, len(c))
	for _, l := range c {
		if !seen[l] {
			seen[l] = true
			out = append(out, l)
		}
	}
	return out
}

// resolve aplica el paso de Robinson sobre c1, c2 buscando el literal l
// Retorna la cláusula resolvente y true, o nil/false si no aplica
func resolve(c1, c2 Clause, l Literal) (Clause, bool) {
	lNeg := Literal{Atom: l.Atom, Negated: !l.Negated}
	if !contains(c1, l) || !contains(c2, lNeg) {
		return nil, false
	}
	r1 := erase(c1, l)
	r2 := erase(c2, lNeg)
	merged := append(r1, r2...)
	return dedupe(merged), true
}

// ============================================================
// GENERADOR DE CASOS DE PRUEBA
// ============================================================

// generateContradiction genera un conjunto de 4 cláusulas insatisfacibles
// sobre un átomo aleatorio seleccionado de un pool de 26 letras.
func generateContradiction(rng *rand.Rand) []Clause {
	atoms := []string{"p","q","r","s","t","u","v","w","x","y"}
	a1 := atoms[rng.Intn(len(atoms))]
	a2 := atoms[rng.Intn(len(atoms))]
	for a2 == a1 { a2 = atoms[rng.Intn(len(atoms))] }

	return []Clause{
		{{a1, false}, {a2, false}},
		{{a1, true},  {a2, false}},
		{{a1, false}, {a2, true}},
		{{a1, true},  {a2, true}},
	}
}

// tryRefute ejecuta la saturación de resolución sobre las 4 cláusulas
// y retorna true si alcanza la cláusula vacía (C5-REAL refutación)
func tryRefute(clauses []Clause) bool {
	pool := make([]Clause, len(clauses))
	copy(pool, clauses)

	for iter := 0; iter < 20; iter++ {
		added := false
		for i := 0; i < len(pool); i++ {
			for j := i + 1; j < len(pool); j++ {
				for _, lit := range pool[i] {
					if res, ok := resolve(pool[i], pool[j], lit); ok {
						if len(res) == 0 {
							return true // Contradicción
						}
						// Agregar si no está ya
						found := false
						for _, ex := range pool {
							if clauseEq(ex, res) {
								found = true
								break
							}
						}
						if !found {
							pool = append(pool, res)
							added = true
						}
					}
				}
			}
		}
		if !added { break }
	}
	return false
}

func clauseEq(a, b Clause) bool {
	if len(a) != len(b) { return false }
	for i := range a {
		if a[i] != b[i] { return false }
	}
	return true
}

// ============================================================
// HARNESS DE ESTRÉS — 1,000,000 ITERACIONES
// ============================================================

func percentile(sorted []int64, p float64) int64 {
	idx := int(float64(len(sorted)-1) * p / 100.0)
	return sorted[idx]
}

func main() {
	const N = 1_000_000
	rng := rand.New(rand.NewSource(time.Now().UnixNano()))

	fmt.Printf("╔══════════════════════════════════════════════════════╗\n")
	fmt.Printf("║  ROBINSON RESOLUTION STRESS — C5-REAL (N=%d) ║\n", N)
	fmt.Printf("╚══════════════════════════════════════════════════════╝\n\n")

	latencies := make([]int64, 0, N)
	refuted := 0
	failed := 0

	start := time.Now()

	for i := 0; i < N; i++ {
		clauses := generateContradiction(rng)
		t0 := time.Now()
		ok := tryRefute(clauses)
		ns := time.Since(t0).Nanoseconds()
		latencies = append(latencies, ns)
		if ok {
			refuted++
		} else {
			failed++
		}

		if (i+1) % 100_000 == 0 {
			elapsed := time.Since(start)
			fmt.Printf("  [%d/%d] — elapsed: %v — refuted: %d — failed: %d\n",
				i+1, N, elapsed.Round(time.Millisecond), refuted, failed)
		}
	}

	elapsed := time.Since(start)
	sort.Slice(latencies, func(i, j int) bool { return latencies[i] < latencies[j] })

	totalNs := int64(0)
	for _, l := range latencies { totalNs += l }
	avgNs := totalNs / int64(len(latencies))

	fmt.Printf("\n╔══════════════════════════════════════════════════════╗\n")
	fmt.Printf("║  RESULTADO FINAL — BFT LEDGER INVARIANT              ║\n")
	fmt.Printf("╠══════════════════════════════════════════════════════╣\n")
	fmt.Printf("║  Total iteraciones : %d                       ║\n", N)
	fmt.Printf("║  Refutaciones OK   : %d (%d%%)                    ║\n", refuted, refuted*100/N)
	fmt.Printf("║  Fallos            : %d                              ║\n", failed)
	fmt.Printf("║  Tiempo total      : %v                          ║\n", elapsed.Round(time.Millisecond))
	fmt.Printf("║  Throughput        : %.0f iter/s                  ║\n", float64(N)/elapsed.Seconds())
	fmt.Printf("╠══════════════════════════════════════════════════════╣\n")
	fmt.Printf("║  LATENCIA POR ITERACIÓN (ns)                         ║\n")
	fmt.Printf("║  p50  : %10d ns                                ║\n", percentile(latencies, 50))
	fmt.Printf("║  p90  : %10d ns                                ║\n", percentile(latencies, 90))
	fmt.Printf("║  p95  : %10d ns                                ║\n", percentile(latencies, 95))
	fmt.Printf("║  p99  : %10d ns                                ║\n", percentile(latencies, 99))
	fmt.Printf("║  p100 : %10d ns                                ║\n", percentile(latencies, 100))
	fmt.Printf("║  avg  : %10d ns                                ║\n", avgNs)
	fmt.Printf("╚══════════════════════════════════════════════════════╝\n")

	// Ancla criptográfica del resultado (Ω11 — Master Ledger)
	summary := strings.Join([]string{
		strconv.Itoa(N),
		strconv.Itoa(refuted),
		strconv.Itoa(failed),
		strconv.FormatInt(percentile(latencies, 50), 10),
		strconv.FormatInt(percentile(latencies, 99), 10),
		elapsed.String(),
	}, "|")
	hash := sha256.Sum256([]byte(summary))
	fmt.Printf("\n  CORTEX-TAINT: %s\n", hex.EncodeToString(hash[:]))
	os.Exit(0)
}
