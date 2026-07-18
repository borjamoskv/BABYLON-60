package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"strings"
)

const PORT = ":6060"

type Response struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

func enableCors(w *http.ResponseWriter) {
	(*w).Header().Set("Access-Control-Allow-Origin", "*")
	(*w).Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
	(*w).Header().Set("Access-Control-Allow-Headers", "Content-Type")
}

func portalHandler(w http.ResponseWriter, r *http.Request) {
	enableCors(&w)
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	if r.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	var resp Response
	resp.Status = "error"
	resp.Message = "Ruta no configurada"

	path := r.URL.Path
	switch path {
	case "/launch-brave":
		cmd := exec.Command("open", "-a", "Brave Browser")
		err := cmd.Start()
		if err != nil {
			resp.Message = fmt.Sprintf("Fallo al lanzar Brave: %v", err)
		} else {
			resp.Status = "ok"
			resp.Message = "Brave Browser lanzado exitosamente"
		}

	case "/mount-dmg":
		dmgPath := "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv.dmg"
		if _, err := os.Stat(dmgPath); os.IsNotExist(err) {
			resp.Message = "Archivo DMG no encontrado en la ruta raíz"
		} else {
			cmd := exec.Command("hdiutil", "attach", "-nobrowse", "-readonly", dmgPath)
			out, err := cmd.CombinedOutput()
			if err != nil {
				resp.Message = fmt.Sprintf("Fallo al montar: %v", err)
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
			}
		}

	case "/restart-ollama":
		cmd := exec.Command("open", "-a", "Ollama")
		err := cmd.Start()
		if err != nil {
			resp.Message = fmt.Sprintf("Fallo al iniciar Ollama: %v", err)
		} else {
			resp.Status = "ok"
			resp.Message = "Ollama activado o reiniciado"
		}
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}

func main() {
	http.HandleFunc("/", portalHandler)
	fmt.Printf("Portal daemon Go levantado en el puerto %s\n", PORT)
	err := http.ListenAndServe(PORT, nil)
	if err != nil {
		fmt.Printf("Error al arrancar el servidor: %v\n", err)
	}
}
