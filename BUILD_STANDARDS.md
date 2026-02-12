# Build Standards & CI/CD Requirements

## Overview

This document defines mandatory standards for all build processes, CI/CD pipelines, and deployment procedures in the NWU Protocol project.

---

## Core Principles

1. **Reproducibility** - Builds must be reproducible across environments
2. **Security** - All builds must be secure and traceable
3. **Automation** - Manual steps should be eliminated
4. **Fast Feedback** - CI/CD should complete quickly
5. **Fail Fast** - Catch issues as early as possible

---

## Build Requirements

### General Build Standards

All build processes must:

- ✅ Be deterministic (same input = same output)
- ✅ Use version-locked dependencies
- ✅ Include security scanning
- ✅ Generate reproducible artifacts
- ✅ Be container-friendly
- ✅ Complete within reasonable time (<10 minutes for CI)

### Version Locking

**Node.js**

```json
{
  "engines": {
    "node": ">=18.0.0 <21.0.0",
    "npm": ">=9.0.0"
  }
}
```

- Use `package-lock.json` (committed to repository)
- Pin major versions of critical dependencies
- Use `npm ci` instead of `npm install` in CI

**Python**

```txt
# requirements.txt - Use exact versions for production
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
```

- Use `requirements.txt` with pinned versions
- Separate `requirements-dev.txt` for development tools
- Use virtual environments (`venv` or `poetry`)

**Docker**

```dockerfile
# Pin base image versions with SHA
FROM node:18.19.0-alpine@sha256:abc123...

# Pin system packages
RUN apk add --no-cache \
    python3=3.11.6-r0 \
    gcc=12.2.1-r5
```

### Dependency Management

#### Approved Ecosystems

We support security scanning for these ecosystems:

- npm (Node.js)
- pip (Python)
- maven (Java, if added)
- go modules (Go, if added)
- composer (PHP, if added)
- rubygems (Ruby, if added)
- nuget (.NET, if added)
- cargo (Rust, if added)

#### Security Requirements

**Before Adding New Dependencies:**

1. Check for known vulnerabilities
2. Review license compatibility
3. Assess maintenance status
4. Evaluate alternatives
5. Get Tiger Team approval for new critical dependencies

**Dependency Scanning:**

```yaml
# Automated scanning in CI/CD
- Security audit (npm audit, pip-audit)
- License compliance check
- Outdated dependency detection
- Vulnerability database check
```

#### Update Policy

- **Critical vulnerabilities**: Patch within 24 hours
- **High vulnerabilities**: Patch within 72 hours
- **Medium vulnerabilities**: Patch within 30 days
- **Low vulnerabilities**: Patch within 90 days
- **Dependencies**: Update monthly during maintenance window

---

## CI/CD Pipeline Standards

### Pipeline Structure

Every component must have a CI/CD pipeline with these stages:

```yaml
stages: 1. ✅ Checkout & Setup
  2. ✅ Dependency Installation
  3. ✅ Linting & Formatting
  4. ✅ Type Checking (if applicable)
  5. ✅ Unit Tests
  6. ✅ Security Scanning
  7. ✅ Build
  8. ✅ Integration Tests
  9. ✅ Coverage Report
  10. ✅ Artifact Generation
```

### Required Checks (Non-Negotiable)

#### 1. Code Quality Checks

**Linting**

```yaml
# JavaScript/TypeScript
- name: Lint
  run: npm run lint

# Python
- name: Lint with Flake8
  run: flake8 .

- name: Format check with Black
  run: black --check .
```

**Type Checking**

```yaml
# TypeScript
- name: Type Check
  run: tsc --noEmit

# Python
- name: Type Check with MyPy
  run: mypy src/
```

#### 2. Testing

**Unit Tests**

```yaml
- name: Run Tests
  run: npm test -- --coverage
  env:
    CI: true

- name: Check Coverage
  run: |
    COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
    if (( $(echo "$COVERAGE < 80" | bc -l) )); then
      echo "Coverage $COVERAGE% is below 80%"
      exit 1
    fi
```

**Integration Tests**

```yaml
- name: Start Test Services
  run: docker-compose -f docker-compose.test.yml up -d

- name: Run Integration Tests
  run: npm run test:integration

- name: Cleanup
  if: always()
  run: docker-compose -f docker-compose.test.yml down
```

#### 3. Security Scanning

**Vulnerability Scanning**

```yaml
- name: Security Audit
  run: npm audit --audit-level=moderate

- name: Trivy Scan
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    format: 'sarif'
    output: 'trivy-results.sarif'
```

**SAST (Static Application Security Testing)**

```yaml
- name: CodeQL Analysis
  uses: github/codeql-action/analyze@v2
  with:
    languages: javascript, python
```

**Secret Scanning**

```yaml
- name: TruffleHog Secret Scan
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
    base: main
    head: HEAD
```

#### 4. Build Verification

**Build Success**

```yaml
- name: Build Application
  run: npm run build

- name: Verify Build Artifacts
  run: |
    if [ ! -d "dist" ]; then
      echo "Build artifacts not found"
      exit 1
    fi
```

**Build Optimization**

```yaml
- name: Check Bundle Size
  run: |
    SIZE=$(du -sh dist | cut -f1)
    echo "Bundle size: $SIZE"
    # Add size limit check
```

---

## Docker Standards

### Dockerfile Best Practices

```dockerfile
# ✅ Good Dockerfile structure
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy dependency files first (better caching)
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Change ownership
RUN chown -R nodejs:nodejs /app

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

# Start application
CMD ["node", "dist/index.js"]
```

### Docker Security Standards

- ✅ Use official base images
- ✅ Pin image versions with SHA256
- ✅ Run as non-root user
- ✅ Multi-stage builds to reduce image size
- ✅ Scan images for vulnerabilities
- ✅ Use `.dockerignore` to exclude unnecessary files
- ✅ No secrets in images
- ✅ Include health checks

### Docker Compose Standards

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    image: nwu-protocol-backend:${VERSION:-latest}
    container_name: nwu-backend
    restart: unless-stopped
    environment:
      NODE_ENV: production
      DATABASE_URL: ${DATABASE_URL}
    env_file:
      - .env
    ports:
      - '8000:8000'
    volumes:
      - ./logs:/app/logs
    networks:
      - nwu-network
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8000/health']
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    depends_on:
      db:
        condition: service_healthy
    labels:
      - 'com.nwu-protocol.service=backend'
      - 'com.nwu-protocol.version=${VERSION:-latest}'

  db:
    image: postgres:15-alpine
    # ... configuration

networks:
  nwu-network:
    driver: bridge

volumes:
  postgres-data:
    driver: local
```

---

## Secrets Management

### Environment Variables

**Structure**

```bash
# .env.example (committed to repository)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
API_KEY=your-api-key-here
SECRET_KEY=your-secret-key-here

# .env (NOT committed, local development only)
DATABASE_URL=postgresql://localuser:localpass@localhost:5432/localdb
API_KEY=sk-local-development-key
SECRET_KEY=local-secret-key
```

### CI/CD Secrets

**GitHub Secrets**

```yaml
- name: Deploy to Production
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    API_KEY: ${{ secrets.API_KEY }}
    DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
  run: ./deploy.sh
```

### Secrets Scanning

- ✅ Pre-commit hooks to detect secrets
- ✅ CI/CD scanning for secrets
- ✅ Automated rotation of exposed secrets
- ✅ Audit trail for secret access

**Tools**

- TruffleHog
- git-secrets
- detect-secrets

---

## Artifact Management

### Build Artifacts

**Requirements**

- ✅ Versioned (semantic versioning)
- ✅ Signed (for verification)
- ✅ Immutable (cannot be overwritten)
- ✅ Traceable (linked to source commit)
- ✅ Stored securely

**Naming Convention**

```
<component>-<version>-<commit-sha>.tar.gz
nwu-backend-1.2.3-abc1234.tar.gz
```

### Container Images

**Tagging Strategy**

```bash
# Semantic version
nwu-protocol/backend:1.2.3

# Git commit SHA
nwu-protocol/backend:abc1234

# Environment
nwu-protocol/backend:staging
nwu-protocol/backend:production

# Latest (avoid in production)
nwu-protocol/backend:latest
```

### Artifact Storage

- Docker images: Container registry (Docker Hub, GitHub Container Registry)
- Build artifacts: Artifact storage (GitHub Artifacts, S3)
- Smart contracts: IPFS + GitHub releases
- Documentation: GitHub Pages

---

## Deployment Standards

### Pre-Deployment Checklist

- [ ] All CI/CD checks pass
- [ ] Security scan clean
- [ ] Code review approved
- [ ] Integration tests pass
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Rollback plan documented
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] Stakeholders notified

### Deployment Process

**Staging Deployment**

```yaml
1. Automated on merge to develop branch
2. Deploy to staging environment
3. Run smoke tests
4. Notify team
```

**Production Deployment**

```yaml
1. Manual approval required
2. Deploy during maintenance window
3. Gradual rollout (canary/blue-green)
4. Monitor metrics
5. Verify health checks
6. Rollback if issues detected
```

### Deployment Strategies

**Blue-Green Deployment**

- Zero-downtime deployments
- Instant rollback capability
- Full environment testing

**Canary Deployment**

- Gradual rollout (e.g., 10%, 25%, 50%, 100%)
- Monitor metrics at each stage
- Auto-rollback on error rate increase

**Rolling Deployment**

- Update instances gradually
- Maintain service availability
- Monitor health continuously

### Rollback Procedures

**Automated Rollback Triggers**

- Error rate > 5% increase
- Response time > 2x baseline
- Health check failures
- Resource exhaustion

**Manual Rollback**

```bash
# Quick rollback to previous version
./scripts/rollback.sh --to-version=1.2.2

# Verify rollback
./scripts/health-check.sh
```

---

## Monitoring & Observability

### Required Monitoring

**Application Metrics**

- Request rate
- Response time (p50, p95, p99)
- Error rate
- Success rate

**System Metrics**

- CPU usage
- Memory usage
- Disk usage
- Network I/O

**Business Metrics**

- User registrations
- Active users
- Contribution submissions
- Verification completions

### Logging Standards

**Log Levels**

```python
# ERROR - System errors requiring attention
logger.error("Database connection failed", exc_info=True)

# WARNING - Potential issues
logger.warning("API rate limit approaching")

# INFO - Important business events
logger.info("User registered", extra={"user_id": user_id})

# DEBUG - Detailed diagnostic info (dev only)
logger.debug("Processing request", extra={"request_id": req_id})
```

**Structured Logging**

```json
{
  "timestamp": "2026-02-12T02:19:35.295Z",
  "level": "INFO",
  "service": "backend",
  "message": "User registered",
  "user_id": "123",
  "trace_id": "abc-def-ghi",
  "environment": "production"
}
```

### Alerting

**Critical Alerts** (Immediate notification)

- Production down
- Database connection lost
- Security breach detected
- Error rate > 10%

**Warning Alerts** (Within 1 hour)

- Error rate > 5%
- Response time > 2x baseline
- Disk space > 80%
- Memory usage > 85%

---

## Performance Standards

### Build Performance

- **CI/CD pipeline**: < 10 minutes
- **Unit tests**: < 5 minutes
- **Integration tests**: < 10 minutes
- **Docker build**: < 5 minutes

### Application Performance

- **API response time**: < 200ms (p95)
- **Page load time**: < 2 seconds
- **Database queries**: < 100ms (p95)
- **Build size**: Minimize and track

### Optimization Techniques

- Caching (Redis, CDN)
- Database indexing
- Query optimization
- Code splitting
- Image optimization
- Compression (gzip, brotli)

---

## Compliance & Audit

### Build Traceability

Every build must be traceable:

```yaml
Build Metadata:
  - Git commit SHA
  - Build timestamp
  - Builder identity
  - Dependencies snapshot
  - Test results
  - Security scan results
```

### Audit Requirements

**Quarterly Audit**

- Review all CI/CD configurations
- Verify security scanning enabled
- Check secrets management
- Review deployment logs
- Validate rollback procedures

**Documentation**

- Keep build logs for 90 days
- Retain deployment records for 1 year
- Archive critical incidents indefinitely

---

## CI/CD Templates

### GitHub Actions Workflow Template

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read
  security-events: write

jobs:
  test-and-build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npm run type-check

      - name: Test
        run: npm test -- --coverage

      - name: Security audit
        run: npm audit --audit-level=moderate

      - name: Build
        run: npm run build

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
```

---

## Continuous Improvement

### Metrics Review

**Weekly**

- CI/CD success rate
- Build time trends
- Test coverage trends

**Monthly**

- Deployment frequency
- Mean time to recovery
- Change failure rate

**Quarterly**

- Standards compliance audit
- Tool and process review
- Performance optimization review

---

## Related Documents

- [Governance Framework](GOVERNANCE.md)
- [Coding Standards](CODING_STANDARDS.md)
- [Definition of Done](DEFINITION_OF_DONE.md)
- [Security Policy](SECURITY.md)

---

**Version**: 1.0  
**Last Updated**: 2026-02-12  
**Owner**: DevOps Lead + Tiger Team  
**Review Cycle**: Quarterly
