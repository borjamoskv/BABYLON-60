package main

import (
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func TestVerifyPhantomTargets(t *testing.T) {
	tempDir := t.TempDir()
	
	// Should fail when .agents doesn't exist
	if err := verifyPhantomTargets(tempDir); err == nil {
		t.Errorf("expected error when .agents is missing, got nil")
	}

	// Should pass when .agents exists
	agentsDir := filepath.Join(tempDir, ".agents")
	if err := os.Mkdir(agentsDir, 0755); err != nil {
		t.Fatalf("failed to create .agents: %v", err)
	}

	if err := verifyPhantomTargets(tempDir); err != nil {
		t.Errorf("unexpected error when .agents exists: %v", err)
	}
}

func TestWriteJSON(t *testing.T) {
	rec := httptest.NewRecorder()
	payload := HealthResponse{
		Status:    "ok",
		Version:   "1.0.0",
		BuildHash: "test_hash",
		BuildTime: "now",
	}

	writeJSON(rec, http.StatusOK, payload)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", rec.Code)
	}

	contentType := rec.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("expected application/json, got %s", contentType)
	}
}

func TestCorsMiddleware(t *testing.T) {
	handler := corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// Test OPTIONS preflight
	req := httptest.NewRequest("OPTIONS", "/health", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected OPTIONS 200, got %d", rec.Code)
	}
	if rec.Header().Get("Access-Control-Allow-Origin") != "*" {
		t.Errorf("missing CORS headers on OPTIONS")
	}
}
