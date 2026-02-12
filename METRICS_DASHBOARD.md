# Metrics Dashboard & KPI Framework

## Overview

This document defines the key performance indicators (KPIs) and metrics framework for the NWU Protocol Stability & Excellence Initiative. These metrics are reviewed bi-weekly by the Executive Committee.

---

## KPI Dashboard Structure

### Real-Time Visibility

All metrics are accessible through:

1. **GitHub Insights** - Built-in repository metrics
2. **CI/CD Dashboard** - GitHub Actions workflow metrics
3. **Security Dashboard** - Vulnerability and compliance metrics
4. **Custom Dashboards** - Grafana/Prometheus for application metrics

**Transparency Principle**: All dashboards are visible to the entire team to ensure excellence and under-performance are transparent and acted on quickly.

---

## Core KPI Categories

### 1. Reliability Metrics

#### System Uptime
- **Definition**: Percentage of time system is operational and accessible
- **Target**: ≥ 99.9% (43.2 minutes downtime/month max)
- **Measurement**: Automated health checks every 60 seconds
- **Owner**: DevOps Lead

**Calculation**:
```
Uptime % = (Total Time - Downtime) / Total Time × 100
```

**Traffic Light Indicators**:
- 🟢 Green: ≥ 99.9%
- 🟡 Yellow: 99.5% - 99.9%
- 🔴 Red: < 99.5%

#### Mean Time Between Failures (MTBF)
- **Definition**: Average time between system failures
- **Target**: > 720 hours (30 days)
- **Measurement**: Time between incidents requiring intervention
- **Owner**: DevOps Lead

#### Mean Time to Recovery (MTTR)
- **Definition**: Average time to restore service after failure
- **Target**: < 1 hour
- **Measurement**: Time from incident detection to resolution
- **Owner**: DevOps Lead

**Calculation**:
```
MTTR = Total Recovery Time / Number of Incidents
```

**Traffic Light Indicators**:
- 🟢 Green: < 30 minutes
- 🟡 Yellow: 30-60 minutes
- 🔴 Red: > 60 minutes

---

### 2. Deployment Metrics

#### Deployment Frequency
- **Definition**: How often code is deployed to production
- **Target**: ≥ 1 per week (moving toward daily)
- **Measurement**: Count of production deployments
- **Owner**: Technical Leader

**Maturity Levels**:
- Elite: Multiple times per day
- High: Once per day to once per week
- Medium: Once per week to once per month
- Low: Less than once per month

#### Deployment Success Rate
- **Definition**: Percentage of deployments that succeed without rollback
- **Target**: ≥ 95%
- **Measurement**: Successful deployments / Total deployments × 100
- **Owner**: DevOps Lead

**Traffic Light Indicators**:
- 🟢 Green: ≥ 95%
- 🟡 Yellow: 90% - 95%
- 🔴 Red: < 90%

#### Lead Time for Changes
- **Definition**: Time from code commit to production deployment
- **Target**: < 24 hours
- **Measurement**: Time from first commit to production deployment
- **Owner**: Technical Leader

**Calculation**:
```
Lead Time = Deployment Time - First Commit Time
```

**Traffic Light Indicators**:
- 🟢 Green: < 24 hours
- 🟡 Yellow: 24-72 hours
- 🔴 Red: > 72 hours

#### Change Failure Rate
- **Definition**: Percentage of changes that cause production incidents
- **Target**: < 5%
- **Measurement**: Failed changes / Total changes × 100
- **Owner**: Technical Leader

**Traffic Light Indicators**:
- 🟢 Green: < 5%
- 🟡 Yellow: 5% - 15%
- 🔴 Red: > 15%

---

### 3. Quality Metrics

#### Test Coverage
- **Definition**: Percentage of code covered by automated tests
- **Target**: ≥ 80% overall, ≥ 95% for critical paths
- **Measurement**: Lines covered / Total lines × 100
- **Owner**: Tiger Team

**By Component**:
- Backend API: Target ≥ 85%
- Frontend: Target ≥ 80%
- Smart Contracts: Target ≥ 95%
- AI Agents: Target ≥ 80%

**Traffic Light Indicators**:
- 🟢 Green: ≥ 80%
- 🟡 Yellow: 70% - 80%
- 🔴 Red: < 70%

#### Code Review Turnaround Time
- **Definition**: Average time from PR creation to approval
- **Target**: < 24 hours
- **Measurement**: Time from PR open to first approval
- **Owner**: Tiger Team

**Traffic Light Indicators**:
- 🟢 Green: < 24 hours
- 🟡 Yellow: 24-48 hours
- 🔴 Red: > 48 hours

#### Critical Bug Escape Rate
- **Definition**: Number of critical bugs reaching production
- **Target**: < 1 per month
- **Measurement**: Count of critical bugs found in production
- **Owner**: Technical Leader

**Traffic Light Indicators**:
- 🟢 Green: 0 per month
- 🟡 Yellow: 1 per month
- 🔴 Red: > 1 per month

#### Technical Debt Ratio
- **Definition**: Ratio of time to fix code vs. time to write it
- **Target**: < 5%
- **Measurement**: (Remediation cost / Development cost) × 100
- **Owner**: Technical Leader

**Traffic Light Indicators**:
- 🟢 Green: < 5%
- 🟡 Yellow: 5% - 10%
- 🔴 Red: > 10%

---

### 4. Security Metrics

#### Vulnerabilities by Severity
- **Definition**: Count of vulnerabilities by severity level
- **Target**: 0 critical, 0 high
- **Measurement**: Security scan results
- **Owner**: Security Lead

**Targets by Severity**:
- Critical: 0 (patch within 24h)
- High: 0 (patch within 72h)
- Medium: < 5 (patch within 30 days)
- Low: < 20 (patch within 90 days)

#### Time to Patch Critical Issues
- **Definition**: Average time to patch critical vulnerabilities
- **Target**: < 24 hours
- **Measurement**: Time from discovery to patch deployment
- **Owner**: Security Lead

**Traffic Light Indicators**:
- 🟢 Green: < 24 hours
- 🟡 Yellow: 24-48 hours
- 🔴 Red: > 48 hours

#### Security Scan Coverage
- **Definition**: Percentage of code/containers with security scanning
- **Target**: 100%
- **Measurement**: (Scanned components / Total components) × 100
- **Owner**: Security Lead

#### Dependency Health Score
- **Definition**: Percentage of dependencies up-to-date and secure
- **Target**: ≥ 95%
- **Measurement**: (Healthy deps / Total deps) × 100
- **Owner**: DevOps Lead

**Traffic Light Indicators**:
- 🟢 Green: ≥ 95%
- 🟡 Yellow: 90% - 95%
- 🔴 Red: < 90%

---

### 5. Adoption & Compliance Metrics

#### Standards Compliance Rate
- **Definition**: Percentage of code meeting all standards
- **Target**: 100%
- **Measurement**: (Compliant PRs / Total PRs) × 100
- **Owner**: Tiger Team

**Traffic Light Indicators**:
- 🟢 Green: 100%
- 🟡 Yellow: 95% - 99%
- 🔴 Red: < 95%

#### CI/CD Pipeline Adoption
- **Definition**: Percentage of components with CI/CD pipelines
- **Target**: 100%
- **Measurement**: (Components with CI/CD / Total components) × 100
- **Owner**: DevOps Lead

#### Documentation Coverage
- **Definition**: Percentage of code with adequate documentation
- **Target**: ≥ 90%
- **Measurement**: Manual review + automated checks
- **Owner**: Technical Leader

#### Training Completion Rate
- **Definition**: Percentage of team completing required training
- **Target**: 100% within 30 days
- **Measurement**: (Completed training / Total team) × 100
- **Owner**: Change Management Lead

---

## Dashboard Views

### Executive Dashboard (Weekly Review)

```
╔══════════════════════════════════════════════════════════╗
║           NWU Protocol - Executive Dashboard            ║
║                     Week of 2026-02-12                   ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  RELIABILITY                                             ║
║  ├─ System Uptime:          99.95% 🟢                   ║
║  ├─ MTBF:                   840 hours 🟢                ║
║  └─ MTTR:                   45 minutes 🟢               ║
║                                                          ║
║  DEPLOYMENT                                              ║
║  ├─ Deployment Frequency:   2 per week 🟢               ║
║  ├─ Deployment Success:     97% 🟢                      ║
║  ├─ Lead Time:              18 hours 🟢                 ║
║  └─ Change Failure Rate:    3% 🟢                       ║
║                                                          ║
║  QUALITY                                                 ║
║  ├─ Test Coverage:          82% 🟢                      ║
║  ├─ Review Turnaround:      20 hours 🟢                 ║
║  ├─ Bug Escape Rate:        0 this month 🟢             ║
║  └─ Technical Debt:         4.2% 🟢                     ║
║                                                          ║
║  SECURITY                                                ║
║  ├─ Critical Vulns:         0 🟢                        ║
║  ├─ High Vulns:             0 🟢                        ║
║  ├─ Patch Time (avg):       12 hours 🟢                 ║
║  └─ Dependency Health:      96% 🟢                      ║
║                                                          ║
║  ADOPTION                                                ║
║  ├─ Standards Compliance:   98% 🟡                      ║
║  ├─ CI/CD Adoption:         100% 🟢                     ║
║  ├─ Documentation:          88% 🟡                      ║
║  └─ Training Completion:    95% 🟡                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

### Team Dashboard (Daily View)

Accessible via GitHub repository insights and custom dashboards.

**Daily Metrics**:
- CI/CD pipeline status
- Active PRs and review status
- Open issues by priority
- Recent deployments
- Test coverage trends
- Security scan results

### Developer Dashboard (Real-Time)

**Individual Metrics**:
- My open PRs and status
- PRs awaiting my review
- My assigned issues
- My code quality metrics
- My test coverage
- My review turnaround time

---

## Reporting Cadence

### Daily
- Automated dashboard updates
- Alert notifications
- Team standup metrics review

### Weekly
- Executive Committee review
- Tiger Team metrics analysis
- Trend identification
- Action item creation

### Bi-Weekly
- Comprehensive KPI review
- Deep dive on specific metrics
- Adjustment of targets if needed
- Communication to broader team

### Monthly
- Detailed trend analysis
- Success story identification
- Challenge resolution review
- Strategic adjustments

### Quarterly
- Comprehensive stability audit
- Full governance review
- Annual planning updates
- Celebration of achievements

---

## Metric Collection Methods

### Automated Collection

**GitHub API**
```python
# Example: Collect deployment metrics
def get_deployment_metrics(repo, start_date, end_date):
    deployments = repo.get_deployments(
        environment='production',
        created_after=start_date,
        created_before=end_date
    )
    
    total = len(deployments)
    successful = len([d for d in deployments if d.state == 'success'])
    
    return {
        'total': total,
        'successful': successful,
        'success_rate': successful / total * 100 if total > 0 else 0
    }
```

**CI/CD Metrics**
- GitHub Actions API for workflow metrics
- Test results from CI pipeline
- Coverage reports from Codecov

**Security Metrics**
- Trivy/Snyk API for vulnerability data
- Dependabot alerts
- CodeQL results

### Manual Collection

**Quarterly Audits**
- Code quality spot checks
- Documentation review
- Compliance verification
- Team feedback surveys

---

## Action Thresholds

### Yellow Zone (Warning)
- **Action**: Monitor closely
- **Timeline**: Address within 1 week
- **Owner**: Component owner
- **Escalation**: Tiger Team if not improving

### Red Zone (Critical)
- **Action**: Immediate attention required
- **Timeline**: Address within 24 hours
- **Owner**: Tiger Team + Component owner
- **Escalation**: Executive Committee

### Persistent Issues
- **Definition**: Metric in yellow/red for 2+ weeks
- **Action**: Root cause analysis required
- **Timeline**: Resolution plan within 3 days
- **Owner**: Technical Leader

---

## Continuous Improvement

### Metric Evolution

**Add New Metrics**:
1. Propose metric with business justification
2. Define measurement method
3. Set realistic targets
4. Pilot for 1 month
5. Adopt or adjust

**Remove/Modify Metrics**:
1. Review quarterly
2. Assess continued relevance
3. Get Tiger Team approval
4. Communicate changes
5. Update dashboards

---

## Tools & Implementation

### Required Tools

- **GitHub Insights**: Built-in metrics
- **Codecov**: Test coverage tracking
- **Dependabot**: Dependency monitoring
- **Trivy/Snyk**: Security scanning
- **Custom Scripts**: Additional metric collection

### Optional Tools

- **Grafana**: Custom dashboards
- **Prometheus**: Time-series metrics
- **DataDog**: Application monitoring
- **PagerDuty**: Incident tracking

---

## Related Documents

- [Governance Framework](GOVERNANCE.md)
- [Stability Mandate](STABILITY_MANDATE.md)
- [Definition of Done](DEFINITION_OF_DONE.md)
- [Build Standards](BUILD_STANDARDS.md)

---

**Version**: 1.0  
**Last Updated**: 2026-02-12  
**Owner**: Technical Leader + Tiger Team  
**Review Cycle**: Quarterly
