# User Manual - Microsoft Entra ID Emulator

Guida completa per utilizzare l'emulatore Microsoft Entra ID nei tuoi progetti di sviluppo e testing.

---

## 1. Quick Start

### Prerequisiti

- **Docker Desktop** installato e funzionante
- **Docker Compose** v2.0+
- **Porta 8029** disponibile sul sistema
- Conoscenza base di OAuth 2.0 e OpenID Connect

### Installazione in 3 Passi

```bash
# 1. Clone o naviga nella directory del progetto
cd /path/to/ldap

# 2. Build del container Docker
docker-compose build

# 3. Avvio dell'emulatore
docker-compose up -d entra-emulator
```

### Verifica dell'Installazione

```bash
# Health check
curl http://localhost:8029/health
# Output atteso: {"status":"healthy"}

# OIDC Discovery Document
curl http://localhost:8029/common/v2.0/.well-known/openid-configuration
```

Se ricevi risposte JSON valide, l'emulatore è pronto! 🎉

---

## 2. Registrare un'Applicazione

L'emulatore include applicazioni pre-registrate per il testing rapido, ma puoi aggiungerne di nuove.

### Applicazioni Pre-configurate

#### App Web (test-app-123)
```json
{
  "appId": "test-app-123",
  "clientSecret": "test-secret",
  "redirectUris": [
    "http://localhost:3029/callback",
    "http://localhost:3029/auth"
  ],
  "allowedScopes": ["openid", "profile", "email", "User.Read"]
}
```

#### App Service (service-app-456)
```json
{
  "appId": "service-app-456",
  "clientSecret": "service-secret",
  "redirectUris": [],
  "allowedScopes": ["api://.default", "https://graph.microsoft.com/.default"]
}
```

### Aggiungere una Nuova Applicazione

1. **Arresta l'emulatore**:
   ```bash
   docker-compose down
   ```

2. **Modifica** `data/applications.json`:
   ```json
   [
     {
       "appId": "my-custom-app",
       "displayName": "La Mia App",
       "clientSecret": "my-secret-123",
       "redirectUris": ["http://localhost:5000/callback"],
       "allowedScopes": ["openid", "profile", "email"]
     }
   ]
   ```

3. **Riavvia**:
   ```bash
   docker-compose up -d entra-emulator
   ```

---

## 3. Creare Utenti di Test

### Utenti Pre-configurati

| Email | Password | Ruolo | Nome Completo |
|-------|----------|-------|---------------|
| `test@contoso.onmicrosoft.com` | `Test123!` | Developer | Test User |
| `admin@contoso.onmicrosoft.com` | `Password123!` | Administrator | Admin User |

### Aggiungere Nuovi Utenti

1. **Arresta l'emulatore**:
   ```bash
   docker-compose down
   ```

2. **Modifica** `data/users.json`:
   ```json
   [
     {
       "id": "unique-id-here",
       "userPrincipalName": "mario.rossi@contoso.onmicrosoft.com",
       "displayName": "Mario Rossi",
       "givenName": "Mario",
       "surname": "Rossi",
       "mail": "mario.rossi@contoso.onmicrosoft.com",
       "jobTitle": "Developer",
       "department": "IT",
       "passwordHash": "$2b$12$..."
     }
   ]
   ```

3. **Genera l'hash della password** (usando Python):
   ```bash
   docker-compose run --rm entra-emulator python -c "import bcrypt; print(bcrypt.hashpw(b'MyPassword123', bcrypt.gensalt()).decode())"
   ```

4. **Riavvia**:
   ```bash
   docker-compose up -d entra-emulator
   ```

---

## 4. Authentication Flow

### Authorization Code Flow (Web Apps)

Il flow più comune per applicazioni web.

#### Step 1: Richiedi il Codice di Autorizzazione

**Browser URL**:
```
http://localhost:8029/common/oauth2/v2.0/authorize?
  client_id=test-app-123&
  response_type=code&
  redirect_uri=http://localhost:3029/callback&
  scope=openid%20profile%20email&
  state=random-state-123&
  nonce=random-nonce-456
```

**Opzioni**:
- Per testing automatico, aggiungi `&test_user=test@contoso.onmicrosoft.com`
- Per UI login, ometti `test_user` e usa il form

#### Step 2: Gestisci il Redirect

Il browser verrà reindirizzato a:
```
http://localhost:3029/callback?code=AUTHORIZATION_CODE&state=random-state-123
```

#### Step 3: Scambia il Code per Token

```bash
curl -X POST "http://localhost:8029/common/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id=test-app-123" \
  -d "client_secret=test-secret" \
  -d "code=AUTHORIZATION_CODE" \
  -d "redirect_uri=http://localhost:3029/callback"
```

**Risposta**:
```json
{
  "token_type": "Bearer",
  "expires_in": 3600,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "long-refresh-token-string",
  "id_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Authorization Code Flow con PKCE (Mobile/SPA)

Per app native e single-page applications.

#### Step 1: Genera Code Verifier e Challenge

```javascript
// JavaScript example
const codeVerifier = generateRandomString(128);
const codeChallenge = base64UrlEncode(sha256(codeVerifier));
```

#### Step 2: Richiedi Codice con Challenge

```
http://localhost:8029/common/oauth2/v2.0/authorize?
  client_id=test-app-123&
  response_type=code&
  redirect_uri=http://localhost:3029/callback&
  scope=openid%20profile&
  code_challenge=CODE_CHALLENGE&
  code_challenge_method=S256
```

#### Step 3: Scambia Code con Verifier

```bash
curl -X POST "http://localhost:8029/common/oauth2/v2.0/token" \
  -d "grant_type=authorization_code" \
  -d "client_id=test-app-123" \
  -d "code=AUTH_CODE" \
  -d "redirect_uri=http://localhost:3029/callback" \
  -d "code_verifier=CODE_VERIFIER"
```

### Resource Owner Password Credentials (Testing Only)

⚠️ **Solo per testing** - non usare in produzione!

```bash
curl -X POST "http://localhost:8029/common/oauth2/v2.0/token" \
  -d "grant_type=password" \
  -d "client_id=test-app-123" \
  -d "username=test@contoso.onmicrosoft.com" \
  -d "password=Test123!" \
  -d "scope=openid profile email"
```

---

## 5. Client Credentials

Per autenticazione service-to-service (nessun utente coinvolto).

### Ottenere un Access Token

```bash
curl -X POST "http://localhost:8029/common/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=service-app-456" \
  -d "client_secret=service-secret" \
  -d "scope=api://.default"
```

**Risposta**:
```json
{
  "token_type": "Bearer",
  "expires_in": 3600,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Usare il Token

```bash
curl -H "Authorization: Bearer ACCESS_TOKEN" \
  http://your-api-endpoint/resource
```

---

## 6. Token Inspection

### Decodificare un JWT

Usa [jwt.io](https://jwt.io) o uno script Python:

```python
import jwt

token = "eyJ0eXAiOiJKV1QiLCJhbGc..."
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
```

### Access Token Claims Tipici

```json
{
  "aud": "api://test-app-123",
  "iss": "http://localhost:8029/common/v2.0",
  "iat": 1705245600,
  "nbf": 1705245600,
  "exp": 1705249200,
  "name": "Test User",
  "oid": "user-id-uuid",
  "preferred_username": "test@contoso.onmicrosoft.com",
  "scp": "openid profile email",
  "sub": "user-id-uuid",
  "tid": "common",
  "ver": "2.0"
}
```

### ID Token Claims Tipici

```json
{
  "aud": "test-app-123",
  "iss": "http://localhost:8029/common/v2.0",
  "sub": "user-id-uuid",
  "email": "test@contoso.onmicrosoft.com",
  "name": "Test User",
  "given_name": "Test",
  "family_name": "User",
  "preferred_username": "test@contoso.onmicrosoft.com",
  "oid": "user-id-uuid"
}
```

### Validare un Token

```bash
# 1. Ottieni JWKS
curl http://localhost:8029/common/discovery/v2.0/keys

# 2. Usa la chiave pubblica per validare
# Vedi Developer Manual per dettagli
```

### Refresh Token

```bash
curl -X POST "http://localhost:8029/common/oauth2/v2.0/token" \
  -d "grant_type=refresh_token" \
  -d "client_id=test-app-123" \
  -d "refresh_token=YOUR_REFRESH_TOKEN" \
  -d "scope=openid profile"
```

---

## 7. Troubleshooting

### L'emulatore non si avvia

**Problema**: Container esce immediatamente

**Soluzione**:
```bash
# Controlla i log
docker-compose logs entra-emulator

# Verifica porta disponibile
lsof -i :8029

# Rebuild completo
docker-compose down
docker-compose build --no-cache
docker-compose up -d entra-emulator
```

### Errore 401 Unauthorized

**Problema**: Token rifiutato

**Cause comuni**:
1. Token scaduto - verifica claim `exp`
2. Client ID errato - verifica `client_id`
3. Scope non permesso - verifica `allowedScopes` in `applications.json`

**Debug**:
```bash
# Decodifica il token
jwt decode YOUR_TOKEN

# Verifica discovery document
curl http://localhost:8029/common/v2.0/.well-known/openid-configuration
```

### Errore 400 Invalid Grant

**Problema**: Authorization code non valido

**Cause**:
1. Code già usato (one-time use)
2. Code scaduto (10 minuti)
3. Redirect URI non corrisponde

**Soluzione**:
- Richiedi un nuovo authorization code
- Verifica che `redirect_uri` sia identico in entrambe le richieste

### Login Page non appare

**Problema**: Redirect invece di login form

**Causa**: Parametro `test_user` presente

**Soluzione**:
- Rimuovi `test_user` dall'URL di autorizzazione
- Usa il form HTML per login interattivo

### Token non contiene claims attesi

**Problema**: Claims mancanti nell'access token

**Causa**: Scope non richiesto correttamente

**Soluzione**:
```bash
# Richiedi scope specifici
scope=openid profile email User.Read
```

### Docker: Cannot connect to Docker daemon

**Problema**: Docker non in esecuzione

**Soluzione**:
```bash
# macOS
open -a Docker

# Verifica
docker ps
```

### Porta 8029 occupata

**Problema**: Altra applicazione usa la porta

**Soluzione**:
```bash
# Trova il processo
lsof -i :8029

# Cambia porta in docker-compose.yml
ports:
  - "8030:8029"  # Usa porta 8030 invece
```

---

## Comandi Utili

### Gestione Container

```bash
# Avvia emulatore
docker-compose up -d entra-emulator

# Ferma emulatore
docker-compose down

# Restart
docker-compose restart entra-emulator

# Logs in real-time
docker-compose logs -f entra-emulator

# Ricostruisci immagine
docker-compose build --no-cache
```

### Testing

```bash
# Esegui test suite
docker-compose run --rm tests

# Test singolo file
docker-compose run --rm tests pytest tests/test_oauth.py -v

# Test con output dettagliato
docker-compose run --rm tests pytest -vv --tb=long
```

### Manutenzione

```bash
# Pulisci dati persistenti
rm -rf data/*.json keys/*.pem

# Reset completo
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d entra-emulator
```

---

## Best Practices

1. **Non usare in produzione** - solo development/testing
2. **Proteggere le credenziali** - anche in testing, non committare secret in Git
3. **Scope minimo** - richiedi solo gli scope necessari
4. **Token expiry** - implementa sempre il refresh token flow
5. **HTTPS in produzione** - l'emulatore usa HTTP, Microsoft Entra usa HTTPS
6. **Testing isolato** - usa container separati per evitare conflitti

---

## Risorse Aggiuntive

- [Developer Manual](developer-manual.md) - Riferimento tecnico completo
- [Microsoft Entra Documentation](https://learn.microsoft.com/en-us/entra/)
- [OAuth 2.0 RFC](https://datatracker.ietf.org/doc/html/rfc6749)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)
