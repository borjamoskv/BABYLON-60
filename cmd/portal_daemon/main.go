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
	"strings"
	"syscall"
	"time"
)

// Response is the generic JSON envelope returned by action endpoints.
type Response struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// HealthResponse is returned by the /health endpoint.
type HealthResponse struct {
	Status  string `json:"status"`
	Version string `json:"version"`
}

// enableCors sets permissive CORS headers on every response.
func enableCors(w *http.ResponseWriter) {
	(*w).Header().Set("Access-Control-Allow-Origin", "*")
	(*w).Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
	(*w).Header().Set("Access-Control-Allow-Headers", "Content-Type")
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
		enableCors(&w)
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next(w, r)
	}
}

// mustPOST rejects non-POST requests with 405.
func mustPOST(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		next(w, r)
	}
}

// mustGET rejects non-GET requests with 405.
func mustGET(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		next(w, r)
	}
}

// launchBraveHandler handles POST /launch-brave.
func launchBraveHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("[%s] POST /launch-brave from %s", time.Now().Format(time.RFC3339), r.RemoteAddr)
	resp := Response{Status: "error", Message: "Ruta no configurada"}

	cmd := exec.Command("open", "-a", "Brave Browser")
	if err := cmd.Start(); err != nil {
		resp.Message = fmt.Sprintf("Fallo al lanzar Brave: %v", err)
		log.Printf("[ERROR] /launch-brave: %v", err)
	} else {
		resp.Status = "ok"
		resp.Message = "Brave Browser lanzado exitosamente"
		log.Printf("[INFO] /launch-brave: success")
	}

	writeJSON(w, http.StatusOK, resp)
}

// mountDMGHandler handles POST /mount-dmg.
func mountDMGHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("[%s] POST /mount-dmg from %s", time.Now().Format(time.RFC3339), r.RemoteAddr)
	resp := Response{Status: "error", Message: "Ruta no configurada"}

	dmgPath := os.Getenv("CORTEX_DMG_PATH")
	if dmgPath == "" {
		dmgPath = "Teorema-Robinson-Moskv.dmg"
	}
	if _, err := os.Stat(dmgPath); os.IsNotExist(err) {
		resp.Message = "Archivo DMG no encontrado en la ruta raíz"
		log.Printf("[WARN] /mount-dmg: DMG not found at %s", dmgPath)
	} else {
		cmd := exec.Command("hdiutil", "attach", "-nobrowse", "-readonly", dmgPath)
		out, err := cmd.CombinedOutput()
		if err != nil {
			resp.Message = fmt.Sprintf("Fallo al montar: %v", err)
			log.Printf("[ERROR] /mount-dmg: %v", err)
		} else {
			parts := strings.Fields(string(out))
			mountPoint := "Volumen"
			if len(parts) > 0 {
				mountPoint = parts[len(parts)-1]
			}
			resp.Status = "ok"
			resp.Message = fmt.Sprintf("DMG montado en: %s", mountPoint)
			log.Printf("[INFO] /mount-dmg: mounted at %s", mountPoint)
		}
	}

	writeJSON(w, http.StatusOK, resp)
}

// restartOllamaHandler handles POST /restart-ollama.
func restartOllamaHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("[%s] POST /restart-ollama from %s", time.Now().Format(time.RFC3339), r.RemoteAddr)
	resp := Response{Status: "error", Message: "Ruta no configurada"}

	cmd := exec.Command("open", "-a", "Ollama")
	if err := cmd.Start(); err != nil {
		resp.Message = fmt.Sprintf("Fallo al iniciar Ollama: %v", err)
		log.Printf("[ERROR] /restart-ollama: %v", err)
	} else {
		resp.Status = "ok"
		resp.Message = "Ollama activado o reiniciado"
		log.Printf("[INFO] /restart-ollama: success")
	}

	writeJSON(w, http.StatusOK, resp)
}

// healthHandler handles GET /health — liveness probe.
func healthHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("[%s] GET /health from %s", time.Now().Format(time.RFC3339), r.RemoteAddr)
	writeJSON(w, http.StatusOK, HealthResponse{Status: "ok", Version: "c5-real"})
}

// listRoutesHandler handles GET /list-routes — returns available route names.
func listRoutesHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("[%s] GET /list-routes from %s", time.Now().Format(time.RFC3339), r.RemoteAddr)
	routes := []string{
		"/launch-brave",
		"/mount-dmg",
		"/restart-ollama",
		"/health",
		"/list-routes",
	}
	writeJSON(w, http.StatusOK, routes)
}

func main() {
	port := os.Getenv("PORTAL_PORT")
	if port == "" {
		port = "6060"
	}
	addr := ":" + port

	mux := http.NewServeMux()
	mux.HandleFunc("/launch-brave", corsMiddleware(mustPOST(launchBraveHandler)))
	mux.HandleFunc("/mount-dmg", corsMiddleware(mustPOST(mountDMGHandler)))
	mux.HandleFunc("/restart-ollama", corsMiddleware(mustPOST(restartOllamaHandler)))
	mux.HandleFunc("/health", corsMiddleware(mustGET(healthHandler)))
	mux.HandleFunc("/list-routes", corsMiddleware(mustGET(listRoutesHandler)))

	srv := &http.Server{
		Addr:         addr,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  30 * time.Second,
	}

	go func() {
		log.Printf("[STARTUP] Portal daemon Go levantado en el puerto %s\n", addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[FATAL] Error al arrancar el servidor: %v\n", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("[SHUTDOWN] Shutting down server gracefully...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("[ERROR] Server forced to shutdown: %v", err)
	}
	log.Println("[SHUTDOWN] Server exited properly")
}
