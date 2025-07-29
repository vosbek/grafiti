---
name: Bug Report
about: Create a report to help us improve the CodeAnalysis system
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''
---

## 🐛 Bug Description

A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## ✅ Expected Behavior

A clear and concise description of what you expected to happen.

## ❌ Actual Behavior

A clear and concise description of what actually happened.

## 📸 Screenshots

If applicable, add screenshots to help explain your problem.

## 🖥️ Environment Information

**System Details:**
- OS: [e.g. Windows 11, Ubuntu 20.04, macOS 12]
- Python Version: [e.g. 3.11.9]
- Node.js Version: [e.g. 18.20.0]
- Container Runtime: [Docker/Podman version]

**Installation Method:**
- [ ] Docker deployment
- [ ] Podman deployment  
- [ ] Native installation
- [ ] Development setup

**Application Version:**
- Backend: [version or commit hash]
- Frontend: [version or commit hash]

## 📋 Validation Results

Please run the validation script and paste the output:

```bash
python validate_deployment.py --comprehensive
```

<details>
<summary>Validation Output</summary>

```
Paste validation output here
```

</details>

## 📊 Health Check Results

Please provide the health check output:

```bash
curl http://localhost:8000/api/v1/health
```

<details>
<summary>Health Check Output</summary>

```json
Paste health check JSON here
```

</details>

## 📝 Log Files

**Backend Logs:**
<details>
<summary>Backend Application Logs</summary>

```
Paste relevant backend logs here (from backend/logs/ or container logs)
```

</details>

**Frontend Logs:**
<details>
<summary>Browser Console Logs</summary>

```
Paste browser console errors here
```

</details>

**Container Logs (if applicable):**
<details>
<summary>Container Runtime Logs</summary>

```bash
# Docker
docker logs neo4j-codeanalysis
docker logs redis-codeanalysis

# Podman  
podman logs neo4j-codeanalysis
podman logs redis-codeanalysis
```

</details>

## 🔍 Additional Context

Add any other context about the problem here:

- Related issues or PRs
- Workarounds you've tried
- Impact on your workflow
- Any configuration changes you made

## ✅ Checklist

Before submitting, please confirm:

- [ ] I have searched existing issues for similar problems
- [ ] I have run the validation script (`validate_deployment.py`)
- [ ] I have included relevant log files and error messages
- [ ] I have provided complete environment information
- [ ] I have tried the troubleshooting steps in the documentation

## 📚 Documentation References

Which documentation did you follow?

- [ ] [Quick Start Guide](../docs/QUICK_START_WINDOWS.md) / [Linux Guide](../docs/QUICK_START_LINUX.md)
- [ ] [Deployment Guide](../docs/DEPLOYMENT_GUIDE.md)
- [ ] [Podman Deployment Guide](../PODMAN_DEPLOYMENT_GUIDE.md)
- [ ] [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- [ ] [AWS Bedrock Setup](../docs/BEDROCK_SETUP.md)

---

**Note:** For security-related issues, please do not include sensitive information like API keys, passwords, or proprietary code in this public issue. Contact the maintainers directly for security concerns.