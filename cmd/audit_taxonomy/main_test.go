package main

import (
	"os"
	"testing"
)

func TestAuditTaxonomyFileCheck(t *testing.T) {
	yamlPath := "cortex/ontology/10000_space_taxonomy.yaml"
	if _, err := os.Stat(yamlPath); os.IsNotExist(err) {
		t.Skip("10000_space_taxonomy.yaml not present at default path during unit test")
	}
}
