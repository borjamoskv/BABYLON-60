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

type Response struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

func enableCors(w *http.ResponseWriter) {
	(*w).Header().Set("Access-Control-Allow-Origin", "*")
	(*w).Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
	(*w).Header().Set("Access-Control-Allow-Headers", "Content-Type")
}

func writeJSON(w http.ResponseWriter, resp Response) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}

func launchBraveHandler(w http.ResponseWriter, r *http.Request) {
	enableCors(&w)
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}
	if r.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	log.Printf("[ACTION] Executing launchBraveHandler")
	
	resp := Response{Status: "error"}
	cmd := exec.Command("open", "-a", "Brave Browser")
	err := cmd.Start()
	if err != nil {
		resp.Message = fmt.Sprintf("Fallo al lanzar Brave: %v", err)
		log.Printf("[ERROR] launchBraveHandler: %v", err)
	} else {
		resp.Status = "ok"
		resp.Message = "Brave Browser lanzado exitosamente"
		log.Printf("[SUCCESS] launchBraveHandler")
	}
	writeJSON(w, resp)
}

func mountDMGHandler(w http.ResponseWriter, r *http.Request) {
	enableCors(&w)
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}
	if r.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	log.Printf("[ACTION] Executing mountDMGHandler")

	resp := Response{Status: "error"}
	dmgPath := "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv.dmg"
	if _, err := os.Stat(dmgPath); os.IsNotExist(err) {
		resp.Message = "Archivo DMG no encontrado en la ruta raíz"
		log.Printf("[ERROR] mountDMGHandler: %v", err)
	} else {
		cmd := exec.Command("hdiutil", "attach", "-nobrowse", "-readonly", dmgPath)
		out, err := cmd.CombinedOutput()
		if err != nil {
			resp.Message = fmt.Sprintf("Fallo al montar: %v", err)
			log.Printf("[ERROR] mountDMGHandler: %v", err)
		} else {
			parts := strings.Fields(string(out))
			var mountPoint string
			if len(parts) > 0 {
				mountPoint = parts[len(parts)-1]
			} else {
				mountPoint = "Volumen"
			}
			resp.Status = "ok"
			resp.Message = fmt.Sprintf("DMG montado en: %s", mountPoint)
			log.Printf("[SUCCESS] mountDMGHandler: %s", mountPoint)
		}
	}
	writeJSON(w, resp)
}

func restartOllamaHandler(w http.ResponseWriter, r *http.Request) {
	enableCors(&w)
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}
	if r.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	log.Printf("[ACTION] Executing restartOllamaHandler")

	resp := Response{Status: "error"}
	cmd := exec.Command("open", "-a", "Ollama")
	err := cmd.Start()
	if err != nil {
		resp.Message = fmt.Sprintf("Fallo al iniciar Ollama: %v", err)
		log.Printf("[ERROR] restartOllamaHandler: %v", err)
	} else {
		resp.Status = "ok"
		resp.Message = "Ollama activado o reiniciado"
		log.Printf("[SUCCESS] restartOllamaHandler")
	}
	writeJSON(w, resp)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	enableCors(&w)
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}
	if r.Method != "GET" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	log.Printf("[ACTION] Executing healthHandler")
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok", "version": "c5-real"})
}

func listRoutesHandler(w http.ResponseWriter, r *http.Request) {
	enableCors(&w)
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}
	if r.Method != "GET" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	log.Printf("[ACTION] Executing listRoutesHandler")
	routes := []string{
		"/launch-brave",
		"/mount-dmg",
		"/restart-ollama",
		"/health",
		"/list-routes",
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(routes)
}

func main() {
	port := os.Getenv("PORTAL_PORT")
	if port == "" {
		port = "6060"
	}
	addr := ":" + port

	mux := http.NewServeMux()
	mux.HandleFunc("/launch-brave", launchBraveHandler)
	mux.HandleFunc("/mount-dmg", mountDMGHandler)
	mux.HandleFunc("/restart-ollama", restartOllamaHandler)
	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/list-routes", listRoutesHandler)

	srv := &http.Server{
		Addr:    addr,
		Handler: mux,
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
