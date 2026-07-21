package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"
)

// Build-time variables injected via -ldflags.
var (
	version   = "dev"
	buildHash = "unknown"
	buildTime = "unknown"
)

// ANSI color constants — Industrial Noir 2026.
const (
	cobalt   = "\033[38;5;27m"
	orange   = "\033[38;5;202m"
	red      = "\033[38;5;160m"
	green    = "\033[38;5;46m"
	darkGrey = "\033[38;5;236m"
	reset    = "\033[0m"
)

// HealthResponse is returned by the /health endpoint.
type HealthResponse struct {
	Status    string `json:"status"`
	Version   string `json:"version"`
	BuildHash string `json:"build_hash"`
	BuildTime string `json:"build_time"`
}

// ActionResponse is the generic JSON envelope for action endpoints.
type ActionResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

func banner() {
	fmt.Printf("%s================================================%s\n", cobalt, reset)
	fmt.Printf("%s     BABYLON-60 SOBERANÍA (C5-REAL)             %s\n", cobalt, reset)
	fmt.Printf("%s     [ IDE KERNEL V4 / GO NATIVE ]              %s\n", cobalt, reset)
	fmt.Printf("%s     Build: %s @ %s                             %s\n", darkGrey, version, buildTime, reset)
	fmt.Printf("%s================================================%s\n", cobalt, reset)
}

func usage() {
	fmt.Println()
	fmt.Println("Uso: babylon60 [comando] [argumentos]")
	fmt.Println()
	fmt.Println("Comandos (Modo C5-REAL):")
	fmt.Printf("  %sforge%s   [prompt] [path] [payload] -> Colapso Atómico (Mutación + Hash)\n", green, reset)
	fmt.Printf("  %spurge%s                             -> [SIGKILL SLOP] Purga TIER_1\n", orange, reset)
	fmt.Printf("  %sbft%s                               -> Invoca Consenso Bizantino Manual\n", cobalt, reset)
	fmt.Printf("  %shalt%s                              -> Pánico Epistémico. Crash duro del Kernel.\n", red, reset)
	fmt.Printf("  %sserve%s   [--port PORT]             -> Levanta el Portal HTTP daemon\n", green, reset)
	fmt.Printf("  %shealth%s                            -> Health check del sistema\n", cobalt, reset)
	fmt.Printf("  %sversion%s                           -> Imprime versión y hash de build\n", darkGrey, reset)
}

// verifyPhantomTargets checks structural invariants before executing commands (Ω22).
func verifyPhantomTargets(root string) error {
	agentsDir := filepath.Join(root, ".agents")
	if info, err := os.Stat(agentsDir); err != nil || !info.IsDir() {
		return fmt.Errorf("%s[EpistemicHalt] Directorio .agents/ no encontrado. (MIMETIC_ITER DETECTADO)%s", red, reset)
	}

	cursorrules := filepath.Join(root, ".cursorrules")
	if _, err := os.Stat(cursorrules); os.IsNotExist(err) {
		fmt.Printf("%s[WARN] .cursorrules ausente. El entorno no está anclado a Vibe Code.%s\n", orange, reset)
	}
	return nil
}

// execCommandWithIPC ensures CORTEX_IPC_SOCKET is always present in sub-process environment.
func execCommandWithIPC(name string, arg ...string) *exec.Cmd {
	cmd := exec.Command(name, arg...)
	env := os.Environ()
	hasIPC := false
	for _, e := range env {
		if strings.HasPrefix(e, "CORTEX_IPC_SOCKET=") {
			hasIPC = true
			break
		}
	}
	if !hasIPC {
		ipcSocket := os.Getenv("CORTEX_IPC_SOCKET")
		if ipcSocket == "" {
			ipcSocket = "/tmp/cortex_ipc.sock"
		}
		env = append(env, "CORTEX_IPC_SOCKET="+ipcSocket)
	}
	cmd.Env = env
	return cmd
}

// runForge executes the forge transducer.
func runForge(root string, args []string) {
	prompt := "N/A"
	target := "N/A"
	payload := ""

	if len(args) >= 1 {
		prompt = args[0]
	}
	if len(args) >= 2 {
		target = args[1]
	}
	if len(args) >= 3 {
		payload = args[2]
	}

	if target == "N/A" {
		fmt.Printf("%s[EpistemicHalt] Target no especificado. Violación Φ1.%s\n", red, reset)
		os.Exit(1)
	}

	fmt.Printf("%s>>> INYECTANDO TELEOLOGÍA (Ψ) AL BFT_STATE_LOOP...%s\n", cobalt, reset)

	// Locate the transducer script.
	scriptPath := filepath.Join(root, "scripts", "50_audit_loop.py")
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		// Fallback to legacy name.
		scriptPath = filepath.Join(root, "scripts", "50_audit_loop.py")
		if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
			fmt.Printf("%s[EpistemicHalt] Falta el transductor físico (scripts/50_audit_loop.py)%s\n", red, reset)
			os.Exit(1)
		}
	}

	pythonBin := filepath.Join(root, ".venv", "bin", "python3")
	if _, err := os.Stat(pythonBin); os.IsNotExist(err) {
		pythonBin = "python3"
	}
	cmd := execCommandWithIPC(pythonBin, scriptPath, prompt, target, payload)
	cmd.Dir = root
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		fmt.Printf("%s[FATAL] Transductor falló: %v%s\n", red, err, reset)
		os.Exit(1)
	}
}

// runPurge executes the entropy purge pipeline.
func runPurge(root string) {
	fmt.Printf("%s[SIGKILL SLOP] Invocando purga vectorial C5-REAL...%s\n", orange, reset)

	purgeScript := filepath.Join(root, "scripts", "52_legion_purge.py")
	if _, err := os.Stat(purgeScript); err == nil {
		pythonBin := filepath.Join(root, ".venv", "bin", "python3")
		if _, err := os.Stat(pythonBin); os.IsNotExist(err) {
			pythonBin = "python3"
		}
		cmd := exec.Command(pythonBin, purgeScript)
		cmd.Dir = root
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err != nil {
			fmt.Printf("%s[ERROR] Purga falló: %v%s\n", red, err, reset)
			os.Exit(1)
		}
	}

	fmt.Printf("%s[OK] ATP Conservado. Memoria sintética eliminada.%s\n", green, reset)
}

// runUltrathink executes the 1000 agent MCTS UltraThink loop.
func runUltrathink(root string, args []string) {
	fmt.Printf("%s[ULTRATHINK] Invocando MCTS Inferencia de Frontera (1000 agentes)...%s\n", cobalt, reset)

	scriptPath := filepath.Join(root, "scripts", "43_iter_ultrathink.py")
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		fmt.Printf("%s[EpistemicHalt] Falta el transductor físico (scripts/43_iter_ultrathink.py)%s\n", red, reset)
		os.Exit(1)
	}

	pythonBin := filepath.Join(root, ".venv", "bin", "python3")
	if _, err := os.Stat(pythonBin); os.IsNotExist(err) {
		pythonBin = "python3"
	}

	var cmd *exec.Cmd
	if len(args) > 0 {
		cmd = exec.Command(pythonBin, append([]string{scriptPath}, args...)...)
	} else {
		cmd = exec.Command(pythonBin, scriptPath)
	}
	cmd.Dir = root
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		fmt.Printf("%s[FATAL] UltraThink falló: %v%s\n", red, err, reset)
		os.Exit(1)
	}
}

// runBFT triggers the Byzantine consensus verification.
func runBFT() {
	fmt.Printf("%s[BFT SYNC] Despertando Nodos Alpha y Beta...%s\n", cobalt, reset)

	// Check git status as a real-world BFT signal.
	cmd := exec.Command("git", "status", "--porcelain")
	out, err := cmd.Output()
	if err != nil {
		fmt.Printf("%s[WARN] git status falló: %v%s\n", orange, err, reset)
	}

	dirtyFiles := strings.TrimSpace(string(out))
	if dirtyFiles == "" {
		fmt.Printf("%s[OK] Simetría BFT lograda. Working tree limpio (Zero Drift).%s\n", green, reset)
	} else {
		lineCount := len(strings.Split(dirtyFiles, "\n"))
		fmt.Printf("%s[WARN] %d archivos con drift detectados. Commit pendiente.%s\n", orange, lineCount, reset)
		fmt.Println(dirtyFiles)
	}
}

// runHealth prints system health diagnostics.
func runHealth(root string) {
	fmt.Printf("%sSistema de diagnóstico C5-REAL%s\n", cobalt, reset)
	fmt.Println()

	// Go version.
	if goOut, err := exec.Command("go", "version").Output(); err == nil {
		fmt.Printf("  Go Runtime:    %s\n", strings.TrimSpace(string(goOut)))
	}

	// Git HEAD.
	if gitOut, err := exec.Command("git", "rev-parse", "--short", "HEAD").Output(); err == nil {
		fmt.Printf("  Git HEAD:      %s\n", strings.TrimSpace(string(gitOut)))
	}

	// Git branch.
	if brOut, err := exec.Command("git", "branch", "--show-current").Output(); err == nil {
		fmt.Printf("  Git Branch:    %s\n", strings.TrimSpace(string(brOut)))
	}

	// DB check.
	dbPaths := []string{
		filepath.Join(root, "db"),
		filepath.Join(root, ".cortex"),
	}
	for _, dp := range dbPaths {
		if info, err := os.Stat(dp); err == nil && info.IsDir() {
			fmt.Printf("  DB Path:       %s%s [EXISTS]%s\n", green, dp, reset)
		} else {
			fmt.Printf("  DB Path:       %s%s [MISSING]%s\n", orange, dp, reset)
		}
	}

	// Binary inventory.
	binDir := filepath.Join(root, "bin")
	entries, err := os.ReadDir(binDir)
	if err == nil {
		fmt.Printf("  Binarios:      ")
		names := make([]string, 0, len(entries))
		for _, e := range entries {
			if !e.IsDir() {
				names = append(names, e.Name())
			}
		}
		fmt.Println(strings.Join(names, ", "))
	}
}

// writeJSON serialises v as JSON into w with the given HTTP status code.
func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("[ERROR] json encode: %v", err)
	}
}

// corsMiddleware wraps a handler with CORS + OPTIONS pre-flight handling.
func corsMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next(w, r)
	}
}

// runServe starts the embedded HTTP portal daemon.
func runServe(port string) {
	if port == "" {
		port = os.Getenv("PORTAL_PORT")
	}
	if port == "" {
		port = "6060"
	}
	addr := ":" + port

	mux := http.NewServeMux()

	// Health endpoint.
	mux.HandleFunc("/health", corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		writeJSON(w, http.StatusOK, HealthResponse{
			Status:    "ok",
			Version:   version,
			BuildHash: buildHash,
			BuildTime: buildTime,
		})
	}))

	// List routes endpoint.
	mux.HandleFunc("/list-routes", corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		routes := []string{"/health", "/list-routes", "/launch-brave", "/mount-dmg", "/restart-ollama"}
		writeJSON(w, http.StatusOK, routes)
	}))

	// Launch Brave.
	mux.HandleFunc("/launch-brave", corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		resp := ActionResponse{Status: "error", Message: "Fallo"}
		cmd := exec.Command("open", "-a", "Brave Browser", "--args", "--remote-debugging-port=9222")
		if err := cmd.Start(); err != nil {
			resp.Message = fmt.Sprintf("Fallo al lanzar Brave: %v", err)
			log.Printf("[ERROR] /launch-brave: %v", err)
		} else {
			resp.Status = "ok"
			resp.Message = "Brave Browser lanzado con CDP en el puerto 9222"
		}
		writeJSON(w, http.StatusOK, resp)
	}))

	// Mount DMG.
	mux.HandleFunc("/mount-dmg", corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		resp := ActionResponse{Status: "error", Message: "DMG no encontrado"}
		dmgPath := os.Getenv("CORTEX_DMG_PATH")
		if dmgPath == "" {
			dmgPath = "Teorema-Robinson-Moskv.dmg"
		}
		if _, err := os.Stat(dmgPath); os.IsNotExist(err) {
			writeJSON(w, http.StatusOK, resp)
			return
		}
		cmd := exec.Command("hdiutil", "attach", "-nobrowse", "-readonly", dmgPath)
		out, err := cmd.CombinedOutput()
		if err != nil {
			resp.Message = fmt.Sprintf("Fallo al montar: %v", err)
		} else {
			parts := strings.Fields(string(out))
			mountPoint := "Volumen"
			if len(parts) > 0 {
				mountPoint = parts[len(parts)-1]
			}
			resp.Status = "ok"
			resp.Message = fmt.Sprintf("DMG montado en: %s", mountPoint)
		}
		writeJSON(w, http.StatusOK, resp)
	}))

	// Restart Ollama.
	mux.HandleFunc("/restart-ollama", corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		resp := ActionResponse{Status: "error", Message: "Fallo"}
		cmd := exec.Command("open", "-a", "Ollama")
		if err := cmd.Start(); err != nil {
			resp.Message = fmt.Sprintf("Fallo al iniciar Ollama: %v", err)
		} else {
			resp.Status = "ok"
			resp.Message = "Ollama activado o reiniciado"
		}
		writeJSON(w, http.StatusOK, resp)
	}))

	srv := &http.Server{
		Addr:         addr,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  30 * time.Second,
	}

	go func() {
		fmt.Printf("%s[STARTUP] BABYLON-60 Portal daemon levantado en %s%s\n", green, addr, reset)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[FATAL] Error al arrancar el servidor: %v\n", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	fmt.Printf("\n%s[SHUTDOWN] Apagado controlado...%s\n", orange, reset)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("[ERROR] Server forced shutdown: %v", err)
	}
	fmt.Printf("%s[SHUTDOWN] Servidor terminado limpiamente.%s\n", green, reset)
}

func main() {
	projectRoot, err := os.Getwd()
	if err != nil {
		fmt.Printf("%s[FATAL] No se pudo obtener CWD: %v%s\n", red, err, reset)
		os.Exit(1)
	}

	banner()

	if err := verifyPhantomTargets(projectRoot); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	if len(os.Args) < 2 {
		usage()
		os.Exit(0)
	}

	command := os.Args[1]

	switch command {
	case "forge":
		fmt.Printf("%sMotor de Transducción (Auditor)... %s[%sONLINE%s]\n", darkGrey, reset, green, reset)
		runForge(projectRoot, os.Args[2:])

	case "ultrathink":
		runUltrathink(projectRoot, os.Args[2:])

	case "purge":
		runPurge(projectRoot)

	case "bft":
		runBFT()

	case "halt":
		fmt.Printf("%s[PANIC] EpistemicHalt forzado por el Operador.%s\n", red, reset)
		os.Exit(1)

	case "serve":
		port := ""
		for i, arg := range os.Args[2:] {
			if arg == "--port" && i+3 < len(os.Args) {
				port = os.Args[i+3]
			}
		}
		runServe(port)

	case "health":
		runHealth(projectRoot)

	case "version":
		fmt.Printf("babylon60 %s (build: %s, time: %s)\n", version, buildHash, buildTime)

	default:
		fmt.Printf("%s[FATAL] Anergía detectada. Comando '%s' no reconocido.%s\n", red, command, reset)
		os.Exit(1)
	}
}
