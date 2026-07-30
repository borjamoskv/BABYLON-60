## 📋 Descripción
<!-- Qué cambia este PR y por qué -->


## 🔒 Checklist de Seguridad (obligatorio)

### Secretos y Credenciales
- [ ] **No hay secretos hardcodeados** (API keys, tokens, passwords, connection strings)
- [ ] **No hay archivos .env** ni configuración con valores reales
- [ ] **No hay claves privadas** (.pem, .key, .p12, certificados)
- [ ] **No hay IPs internas** ni URLs de entornos privados
- [ ] **Los nuevos secretos se agregaron a** el vault / secrets manager (no al código)

### Archivos y Configuración
- [ ] **`.gitignore` cubre** cualquier archivo nuevo sensible
- [ ] **Pre-commit hooks pasan** sin warnings (`pre-commit run --all-files`)
- [ ] **No hay archivos de base de datos** (.sql, .sqlite, .dump)
- [ ] **No hay logs** que puedan contener tokens o PII

### Código
- [ ] **Variables de entorno** se usan para toda configuración sensible
- [ ] **No hay comentarios** con credenciales, TODOs con secretos, o URLs con tokens
- [ ] **Los ejemplos usan placeholders**: `YOUR_API_KEY_HERE`, `changeme`, `xxx`
- [ ] **No se deshabilitó** validación SSL / verificación de certificados

### Si aplica IaC / DevOps
- [ ] **Terraform/K8s** no tiene secretos en plaintext
- [ ] **Dockerfiles** no copian archivos .env ni claves
- [ ] **CI/CD** usa secrets del runner, no variables hardcodeadas

---

> ⚠️ **Si algún check falla**: No mergear. Contactar al equipo de seguridad.
> 🤖 **Escaneo automático**: Gitleaks + TruffleHog corren en CI sobre este PR.
