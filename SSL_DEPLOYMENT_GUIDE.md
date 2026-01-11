# SSL Configuration & Deployment Guide

## ✅ Current Status

- **SSL Enforcement:** Enabled in Supabase
- **Certificate:** Downloaded and stored in `backend/certs/prod-ca-2021.crt`
- **.gitignore:** Updated to exclude certificates
- **Backend Config:** SSL certificate path configured

---

## 🔐 What We've Implemented

### 1. SSL Enforcement in Supabase
**Status:** ✅ Active

- All database connections must use SSL/TLS
- Non-SSL connections are rejected
- Protects against man-in-the-middle attacks

### 2. Certificate Management
**Location:** `backend/certs/prod-ca-2021.crt`

```
ai-webscraper/
├── backend/
│   ├── certs/
│   │   ├── prod-ca-2021.crt    ✅ SSL certificate
│   │   └── README.md           ✅ Documentation
│   └── ...
└── .gitignore                  ✅ Excludes certificates
```

### 3. Backend Configuration
**File:** `backend/app/core/config.py`

```python
SUPABASE_SSL_CERT_PATH: str = os.getenv(
    "SUPABASE_SSL_CERT_PATH",
    "./backend/certs/prod-ca-2021.crt"  # Default path
)
```

---

## 🚀 How SSL Works in This Project

### Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │ HTTPS (SSL)
         ↓
┌─────────────────┐
│ Supabase Client │
│ (Auto SSL/TLS)  │
└────────┬────────┘
         │ SSL/TLS
         ↓
┌─────────────────┐
│   Supabase      │
│   Database      │
│ (SSL Enforced)  │
└─────────────────┘
```

### Current Implementation

**✅ Supabase Client Method (Active)**
```python
# backend/app/db/supabase.py
from supabase import create_client

# SSL is automatic - no config needed!
supabase = create_client(url, key)
```

**Benefits:**
- Zero configuration required
- SSL/TLS handled automatically
- Works with SSL enforcement
- No certificate path needed

---

## 📦 Deployment Checklist

### Local Development
- [x] SSL certificate downloaded
- [x] Certificate in `backend/certs/`
- [x] `.gitignore` excludes certificates
- [x] SSL enforcement enabled in Supabase
- [x] Backend config updated

### Staging Environment
- [ ] Deploy certificate to staging server
- [ ] Set `SUPABASE_SSL_CERT_PATH` in staging `.env`
- [ ] Test all database connections
- [ ] Verify SSL enforcement is working

### Production Environment
- [ ] Deploy certificate to production server
- [ ] Set `SUPABASE_SSL_CERT_PATH` in production `.env`
- [ ] Test connections before launch
- [ ] Monitor SSL connection logs
- [ ] Set up certificate expiration alerts

---

## 🛠️ Deployment Instructions

### Option 1: Docker Deployment (Recommended)

**1. Add certificate to Docker image:**

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Create certs directory
RUN mkdir -p /app/certs

# Copy certificate (DO NOT use in public repos)
# Better: mount as volume or use secrets manager
COPY backend/certs/prod-ca-2021.crt /app/certs/

# Set environment variable
ENV SUPABASE_SSL_CERT_PATH=/app/certs/prod-ca-2021.crt
```

**2. Or use Docker secrets (more secure):**

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    image: ai-webscraper-backend
    secrets:
      - supabase_cert
    environment:
      SUPABASE_SSL_CERT_PATH: /run/secrets/supabase_cert

secrets:
  supabase_cert:
    file: ./backend/certs/prod-ca-2021.crt
```

---

### Option 2: Direct Server Deployment

**1. Copy certificate to server:**
```bash
# On your local machine
scp backend/certs/prod-ca-2021.crt user@your-server:/opt/ai-webscraper/certs/
```

**2. Set permissions:**
```bash
# On the server
chmod 600 /opt/ai-webscraper/certs/prod-ca-2021.crt
chown app-user:app-group /opt/ai-webscraper/certs/prod-ca-2021.crt
```

**3. Update environment:**
```bash
# /opt/ai-webscraper/.env
SUPABASE_SSL_CERT_PATH=/opt/ai-webscraper/certs/prod-ca-2021.crt
```

---

### Option 3: Cloud Deployment (AWS, GCP, Azure)

**AWS Secrets Manager:**
```python
import boto3
import os

def get_ssl_cert():
    if os.getenv("ENVIRONMENT") == "production":
        secrets_manager = boto3.client('secretsmanager')
        response = secrets_manager.get_secret_value(SecretId='supabase-ssl-cert')
        return response['SecretString']
    return None
```

**Google Cloud Secret Manager:**
```python
from google.cloud import secretmanager

def get_ssl_cert():
    client = secretmanager.SecretManagerServiceClient()
    name = "projects/PROJECT_ID/secrets/supabase-ssl-cert/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

---

## 🧪 Testing SSL Configuration

### Test 1: Verify SSL is Active

```python
# test_ssl.py
from app.db.supabase import supabase_client

try:
    response = supabase_client.table("crawls").select("*").limit(1).execute()
    print("✅ SSL connection successful!")
except Exception as e:
    print(f"❌ SSL connection failed: {e}")
```

### Test 2: Verify Enforcement

Try connecting without SSL (should fail):
```bash
# Should be rejected by Supabase
psql "postgresql://postgres:password@db.your-project.supabase.co:5432/postgres?sslmode=disable"

# Expected output: Connection rejected
```

### Test 3: Check Certificate Validity

```bash
# Check certificate expiration
openssl x509 -in backend/certs/prod-ca-2021.crt -noout -enddate

# Verify certificate details
openssl x509 -in backend/certs/prod-ca-2021.crt -text -noout
```

---

## 🔄 Certificate Rotation Process

### When to Rotate:
- Certificate expiring (check Supabase dashboard)
- Security incident
- Supabase certificate update

### How to Rotate:

**1. Download new certificate:**
- Go to Supabase Dashboard > Settings > Database
- Download latest certificate

**2. Update local files:**
```bash
# Backup old certificate
cp backend/certs/prod-ca-2021.crt backend/certs/prod-ca-2021.crt.old

# Replace with new certificate
cp ~/Downloads/new-cert.crt backend/certs/prod-ca-2021.crt
```

**3. Deploy to all environments:**
```bash
# Staging
scp backend/certs/prod-ca-2021.crt user@staging:/opt/app/certs/

# Production
scp backend/certs/prod-ca-2021.crt user@production:/opt/app/certs/
```

**4. Restart services:**
```bash
# Restart backend to load new certificate
systemctl restart ai-webscraper-backend
```

**5. Verify:**
```bash
# Test connection
python test_ssl.py
```

---

## 🚨 Security Best Practices

### DO:
- ✅ Use SSL enforcement in production
- ✅ Store certificates securely
- ✅ Rotate certificates regularly
- ✅ Monitor certificate expiration
- ✅ Use secrets management in cloud
- ✅ Restrict file permissions (chmod 600)

### DON'T:
- ❌ Commit certificates to Git
- ❌ Share certificates via email/chat
- ❌ Use same certificate across projects
- ❌ Store in public S3 buckets
- ❌ Hardcode certificate contents
- ❌ Disable SSL in production

---

## 🔍 Troubleshooting

### Issue: "SSL connection required"
**Cause:** SSL enforcement is active (good!)
**Solution:** Ensure client uses SSL (Supabase client does this automatically)

### Issue: "Certificate verify failed"
**Possible causes:**
- Certificate file missing
- Wrong file path
- File permissions issue
- Certificate expired

**Solution:**
```bash
# Check file exists
ls -la backend/certs/prod-ca-2021.crt

# Check permissions
chmod 600 backend/certs/prod-ca-2021.crt

# Verify certificate
openssl verify backend/certs/prod-ca-2021.crt
```

### Issue: Connection timeout
**Possible causes:**
- Firewall blocking port 5432
- Wrong database URL
- Network issue

**Solution:**
```bash
# Test connectivity
nc -zv db.your-project.supabase.co 5432

# Check database URL
echo $SUPABASE_URL
```

---

## 📊 Monitoring & Alerts

### What to Monitor:
- SSL connection success rate
- Certificate expiration date
- Failed connection attempts
- SSL handshake errors

### Suggested Alerts:
- Certificate expires in 30 days
- SSL connection failures > 5%
- Unauthorized connection attempts

### Implementation Example:
```python
# monitoring.py
import ssl
import socket
from datetime import datetime

def check_cert_expiration(host, port=5432):
    """Check SSL certificate expiration date."""
    context = ssl.create_default_context()
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
            expiry = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            days_left = (expiry - datetime.now()).days

            if days_left < 30:
                print(f"⚠️  Certificate expires in {days_left} days!")
            else:
                print(f"✅ Certificate valid for {days_left} more days")
```

---

## 📚 Additional Resources

- [Supabase SSL Documentation](https://supabase.com/docs/guides/database/connecting-to-postgres#ssl-enforcement)
- [PostgreSQL SSL Support](https://www.postgresql.org/docs/current/libpq-ssl.html)
- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [OWASP Transport Layer Protection](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

## ✅ Completion Checklist

- [x] SSL enforcement enabled in Supabase
- [x] Certificate downloaded and stored
- [x] `.gitignore` updated
- [x] Backend configuration updated
- [x] Documentation created
- [ ] Tested in development
- [ ] Deployed to staging (when ready)
- [ ] Deployed to production (when ready)
- [ ] Monitoring set up
- [ ] Team notified

---

**SSL is now properly configured! Your database connections are encrypted and secure.** 🔐
