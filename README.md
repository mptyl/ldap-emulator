# Microsoft Entra ID Emulator

Un emulatore completo di Microsoft Entra ID (ex Azure Active Directory) per development e testing, implementato con FastAPI e Docker.

## 📋 Caratteristiche

- ✅ **OAuth 2.0** completo (Authorization Code, Client Credentials, ROPC, Refresh Token)
- ✅ **OpenID Connect** (OIDC Discovery, JWKS, UserInfo)
- ✅ **SAML 2.0** Federation Metadata
- ✅ **JWT** con struttura claims Microsoft Entra-compatibile
- ✅ **Docker-ready** con docker-compose
- ✅ **Test suite** completa con pytest

## 🚀 Quick Start

### Prerequisiti
- Docker e Docker Compose
- Porta 8029 disponibile

### Avvio rapido

```bash
# 1. Build del container
docker-compose build

# 2. Avvio dell'emulatore
docker-compose up -d entra-emulator

# 3. Verifica salute
curl http://localhost:8029/health

# 4. Verifica OIDC Discovery
curl http://localhost:8029/common/v2.0/.well-known/openid-configuration
```

L'emulatore sarà disponibile su **http://localhost:8029**

## 📖 Documentazione

- **[User Manual](docs/user-manual.md)** - Guida step-by-step per l'utilizzo
- **[Developer Manual](docs/developer-manual.md)** - Reference tecnica completa

## 🧪 Testing

```bash
# Esecuzione test nel container
docker-compose run --rm tests

# Test singolo endpoint
curl -X POST "http://localhost:8029/common/oauth2/v2.0/token" \
  -d "grant_type=client_credentials&client_id=service-app-456&client_secret=service-secret&scope=api://.default"
```

## 📁 Struttura Progetto

```
/Users/mp/PythonProjects/ldap/
├── Dockerfile                 # Container build
├── docker-compose.yml         # Orchestration
├── main.py                    # Entry point FastAPI
├── config.py                  # Configurazione
├── requirements.txt           # Dipendenze
├── routers/                   # Endpoints
│   ├── oauth.py              # OAuth 2.0
│   ├── oidc.py               # OpenID Connect
│   └── saml.py               # SAML
├── services/                  # Business logic
│   ├── token_service.py      # JWT generation
│   ├── key_service.py        # RSA keys
│   ├── user_service.py       # User management
│   └── app_service.py        # App registry
├── models/                    # Data models
│   ├── user.py
│   └── application.py
├── templates/                 # UI
│   └── login.html
├── tests/                     # Test suite
├── docs/                      # Documentation
└── data/                      # Persistent data
```

## 🔑 Credenziali di Test

### Utenti predefiniti

| Email | Password | Ruolo |
|-------|----------|-------|
| `test@contoso.onmicrosoft.com` | `Test123!` | Developer |
| `admin@contoso. onmicrosoft.com` | `Password123!` | Administrator |

### Applicazioni registrate

| Client ID | Client Secret | Tipo |
|-----------|---------------|------|
| `test-app-123` | `test-secret` | Web App |
| `service-app-456` | `service-secret` | Service |

## ⚙️ Configurazione

Variabili d'ambiente (via docker-compose.yml):

```yaml
environment:
  - EMULATOR_HOST=0.0.0.0
  - EMULATOR_PORT=8029
  - TENANT_ID=contoso
  - ISSUER_URL=http://localhost:8029
  - TOKEN_EXPIRY_SECONDS=3600
```

## 🎯 Endpoint Principali

| Endpoint | Descrizione |
|----------|-------------|
| `GET /{tenant}/oauth2/v2.0/authorize` | Authorization endpoint |
| `POST /{tenant}/oauth2/v2.0/token` | Token endpoint |
| `GET /{tenant}/v2.0/.well-known/openid-configuration` | OIDC Discovery |
| `GET /{tenant}/discovery/v2.0/keys` | JWKS |
| `GET /oidc/userinfo` | UserInfo |
| `GET /health` | Health check |

## ⚠️ Note Importanti

> [!WARNING]
> **Questo emulatore è SOLO per testing/sviluppo**. Non utilizzare in produzione.

> [!TIP]
> Il client sviluppato contro questo emulatore funzionerà senza modifiche con Microsoft Entra reale.

## 📝 License

MIT

## 🤝 Contributi

Questo è un progetto di simulazione per scopi didattici e di testing.
# ldap-emulator
