# GCP Workload Identity Federation — Setup (sin claves JSON)

> **Por qué:** los jobs `validate` y `deploy` usaban `GCP_SA_KEY` (clave JSON de
> larga duración en secrets — viola INV_C5_02 y el espíritu de la rotación P0).
> Con WIF, GitHub Actions canjea su token OIDC por credenciales GCP de **corta
> duración (~1 h)**. No existe ninguna clave que filtrar ni que rotar.

Flujo: `GitHub OIDC token → STS (iamcredentials) → impersonación del Service Account → gcloud autenticado`.

---

## 1. Variables (edítalas una vez)

```bash
export PROJECT_ID="<tu-proyecto-gcp>"
export REPO="borjamoskv/BABYLON-60"
export POOL="github-pool"
export PROVIDER="github-provider"
export SA_NAME="github-actions-ci"

export PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
```

## 2. APIs necesarias

```bash
gcloud services enable iamcredentials.googleapis.com sts.googleapis.com \
  --project="$PROJECT_ID"
```

## 3. Workload Identity Pool + Provider (restringido a ESTE repo)

```bash
gcloud iam workload-identity-pools create "$POOL" \
  --location=global --project="$PROJECT_ID" \
  --display-name="GitHub Actions pool"

gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
  --location=global --workload-identity-pool="$POOL" --project="$PROJECT_ID" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.actor=assertion.actor,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository=='${REPO}'"
```

La `attribute-condition` es la puerta: **solo tokens OIDC emitidos para
`borjamoskv/BABYLON-60`** pueden canjear credenciales. Otros repos (aunque
sean tuyos) quedan fuera.

## 4. Service Account

¿Ya tenías una SA para el antiguo `GCP_SA_KEY`? **Reutilízala** (salta al paso 5
poniendo su nombre en `SA_NAME`) — conserva sus roles actuales.

Si no, créala con los roles mínimos que necesiten tus pipelines:

```bash
gcloud iam service-accounts create "$SA_NAME" --project="$PROJECT_ID" \
  --display-name="GitHub Actions CI (WIF)"

# Ejemplo — ajusta a lo que realmente use orchestration-pipelines:
# gcloud projects add-iam-policy-binding "$PROJECT_ID" \
#   --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
#   --role="roles/editor"   # ⚠️ baja esto al rol mínimo real
```

## 5. Binding: permitir que el repo impersonice la SA

```bash
gcloud iam service-accounts add-iam-policy-binding \
  "${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${REPO}"
```

## 6. Secrets en GitHub (los dos nuevos)

```bash
# Obtén el nombre de recurso completo del provider:
gcloud iam workload-identity-pools providers describe "$PROVIDER" \
  --location=global --workload-identity-pool="$POOL" --project="$PROJECT_ID" \
  --format="value(name)"
```

En **Settings → Secrets and variables → Actions** del repo:

| Secret | Valor |
|:---|:---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `GCP_SERVICE_ACCOUNT` | `github-actions-ci@<PROJECT_ID>.iam.gserviceaccount.com` |

(Con `gh`: `gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER -R borjamoskv/BABYLON-60` y lo pegas.)

## 7. Verificación

Tras mergear la PR de los workflows y crear los secrets:

1. Abre cualquier PR contra `main` (o re-ejecuta el job `validate` de la PR de migración) — debe pasar el paso `auth` en ~5 s.
2. Push a `main` → `Deploy to Dev` debe autenticar y desplegar.
3. Limpieza: `gh secret delete GCP_SA_KEY -R borjamoskv/BABYLON-60` cuando los dos jobs estén verdes. Si la SA antigua solo existía para esa clave, bórrale la clave desde GCP Console (IAM → Service Accounts → Keys) — así queda inutilizable aunque alguien la tenga.

## Rollback

Si algo falla: `git revert` del commit de los workflows devuelve a
`credentials_json` (mientras no hayas borrado `GCP_SA_KEY`).

---

*Author: Borja Moskv (borjamoskv)*
