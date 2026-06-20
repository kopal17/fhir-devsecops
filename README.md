# 🔒 Secure FHIR API — DevSecOps Pipeline

> A HIPAA-compliant FHIR R4 Patient API with a full Microsoft-integrated DevSecOps security pipeline.  
> Built to demonstrate real-world healthcare security engineering aligned with Microsoft's Secure Future Initiative (SFI) — Pillar 4: Engineering Systems Security.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   GitHub Repository                      │
│                                                         │
│  Push / PR ──► GitHub Actions Pipeline                  │
│                       │                                 │
│         ┌─────────────┼─────────────────┐               │
│         ▼             ▼                 ▼               │
│   Secret Scan     CodeQL SAST     Dep CVE Scan          │
│  (Gitleaks)    (GitHub Adv Sec)    (Safety)             │
│         │             │                 │               │
│         └─────────────┼─────────────────┘               │
│                       ▼                                 │
│              Security Unit Tests                        │
│               (pytest — auth, injection,                │
│                input validation, PHI safety)            │
│                       │                                 │
│                       ▼                                 │
│            Container Scan (Trivy)                       │
│            CVEs + secret in layers                      │
│                       │                                 │
└───────────────────────┼─────────────────────────────────┘
                        │
                        ▼
         Microsoft Defender for Cloud
         ┌──────────────────────────────┐
         │  SARIF findings ingested     │
         │  Security recommendations    │
         │  Compliance dashboard        │
         │  Alert → Microsoft Sentinel  │
         └──────────────────────────────┘
```

---

## 🔐 Security Controls Implemented

| Control | Implementation | HIPAA Reference |
|---|---|---|
| Authentication | Bearer token (Entra ID in prod) | §164.312(d) |
| Input sanitisation | Patient ID validation, injection prevention | §164.312(c)(1) |
| PHI audit logging | Structured logs — who, what, when (never data) | §164.312(b) |
| Secret scanning | Gitleaks on all commits and history | §164.312(a)(2)(iv) |
| SAST | CodeQL — security-extended query suite | §164.312(c)(2) |
| Dependency CVEs | Safety check on every build | §164.306(a)(1) |
| Container hardening | Non-root user, minimal image, pinned digest | §164.312(a)(1) |
| Security gate | All checks must pass before merge | §164.308(a)(8) |

---

## 🗂️ Project Structure

```
fhir-devsecops/
├── .github/
│   └── workflows/
│       └── devsecops-pipeline.yml   ← The core DevSecOps pipeline
├── src/
│   ├── api/
│   │   └── main.py                  ← FastAPI FHIR R4 endpoint
│   ├── models/
│   │   └── patient.py               ← FHIR Patient Pydantic models
│   └── utils/
│       ├── auth.py                  ← Token verification
│       └── audit.py                 ← HIPAA PHI access audit logger
├── tests/
│   └── test_security.py             ← Security unit tests (auth, injection, PHI)
├── Dockerfile                       ← Hardened container image
├── requirements.txt
└── README.md
```

---

## 🚀 Pipeline Stages

### 1. 🔑 Secret Scanning (Gitleaks)
Scans **full git history** for hardcoded credentials, API keys, connection strings.  
Fails immediately if any secret pattern is detected — before any code runs.

### 2. 🔍 Static Analysis — CodeQL
Microsoft's CodeQL engine (the same engine powering GitHub Advanced Security and **Microsoft Defender for Cloud**) analyses the Python code for:
- SQL / command injection vulnerabilities
- Insecure deserialization
- Path traversal
- Hardcoded credentials

Results upload as **SARIF** to the GitHub Security tab and are automatically ingested by **Defender for Cloud** when connected.

### 3. 📦 Dependency CVE Scan (Safety)
Every package in `requirements.txt` is checked against the CVE database.  
No known-vulnerable dependencies reach production.

### 4. 🧪 Security Unit Tests (pytest)
Custom security test suite covering:
- Authentication bypass attempts (missing/malformed token)
- SQL injection in patient ID
- Path traversal attacks
- XSS payloads
- Unrestricted search (full dataset exposure)
- PHI leak in error responses

### 5. 🐳 Container Scan (Trivy)
Scans the built Docker image for:
- OS-level CVEs (CRITICAL/HIGH fail the pipeline)
- Secrets accidentally baked into image layers
- Dockerfile misconfigurations

### 6. ☁️ Microsoft Defender for Cloud Integration
On every merge to `main`:
- Authenticates to Azure using a service principal (stored as GitHub Secret)
- Confirms Defender for Cloud is active on the subscription
- All SARIF findings from CodeQL and Trivy are available in the **Defender for Cloud Security Recommendations** blade

---

## ⚙️ Setup Guide

### Prerequisites
- GitHub account (free)
- Azure free account → [portal.azure.com](https://portal.azure.com)

### Step 1: Fork and clone this repo
```bash
git clone https://github.com/YOUR_USERNAME/fhir-devsecops
cd fhir-devsecops
```

### Step 2: Create Azure Service Principal
```bash
# Login to Azure
az login

# Create service principal for GitHub Actions
az ad sp create-for-rbac \
  --name "fhir-devsecops-sp" \
  --role contributor \
  --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID> \
  --sdk-auth
```
Copy the JSON output.

### Step 3: Add GitHub Secret
1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `AZURE_CREDENTIALS`
4. Value: paste the JSON from Step 2

### Step 4: Enable GitHub Advanced Security
GitHub repo → **Settings** → **Code security and analysis** → Enable:
- Dependency graph
- Dependabot alerts
- Code scanning (CodeQL)
- Secret scanning

### Step 5: Enable Microsoft Defender for Cloud
```bash
# Enable Defender for DevOps (connects GitHub to Defender for Cloud)
az security setting update \
  --name "MCAS" \
  --setting-type DataExportSettings \
  --enabled true
```
In Azure Portal: **Defender for Cloud** → **Environment Settings** → **Add environment** → **GitHub**

### Step 6: Push a commit and watch the pipeline
```bash
git add .
git commit -m "feat: initial secure FHIR API"
git push origin main
```

Go to your repo → **Actions** tab → Watch all 6 stages run.

---

## 🧪 Run Tests Locally

```bash
pip install -r requirements.txt pytest pytest-cov

# Run security test suite
pytest tests/test_security.py -v

# Run with coverage
pytest tests/test_security.py --cov=src --cov-report=term-missing
```

---

## 🔗 Microsoft Stack Used

| Tool | Purpose |
|---|---|
| **GitHub Advanced Security** | CodeQL SAST + secret scanning |
| **Microsoft Defender for Cloud** | Centralised security posture |
| **Microsoft Entra ID** | Auth (production token validation) |
| **Azure Monitor / Log Analytics** | PHI audit log destination |
| **Microsoft Sentinel** | SIEM — alert on pipeline failures |

---

## 📖 Related Reading

- [Microsoft SFI Engineering Systems Pillar](https://learn.microsoft.com/en-us/security/zero-trust/sfi/secure-future-initiative-overview)
- [GitHub Advanced Security + Defender for Cloud Integration](https://learn.microsoft.com/en-us/azure/defender-for-cloud/defender-for-devops-introduction)
- [HIPAA Security Rule §164.312 Technical Safeguards](https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html)
- [FHIR R4 Patient Resource Specification](https://www.hl7.org/fhir/patient.html)

---

## 👤 Author

Built as part of a targeted Microsoft Security portfolio project.  
Domain: Healthcare security (Optum) → Microsoft Security engineering.  

Connect on [LinkedIn](#) | View other projects on [GitHub](#)
