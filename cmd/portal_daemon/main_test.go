package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	handler := corsMiddleware(mustGET(healthHandler))
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", rec.Code)
	}
}

func TestListRoutesHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/list-routes", nil)
	rec := httptest.NewRecorder()

	handler := corsMiddleware(mustGET(listRoutesHandler))
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", rec.Code)
	}
}

func TestMustPOSTRejectGET(t *testing.T) {
	req := httptest.NewRequest("GET", "/launch-brave", nil)
	rec := httptest.NewRecorder()

	handler := corsMiddleware(mustPOST(launchBraveHandler))
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusMethodNotAllowed {
		t.Errorf("expected status 405 MethodNotAllowed, got %d", rec.Code)
	}
}
