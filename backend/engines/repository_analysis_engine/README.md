# YGIT Repository Analysis Engine v0.1.0

Owner: Repository Analysis Engine
Contract: Engine Contract Specification v1.0
Architecture: YGIT Architecture Freeze v1.1

## Scope

This engine is the deploy-readiness analysis boundary for YGIT.

Implemented modules:

- Quick Analysis
- Framework Detection
- Package Manager Detection
- Build Command Detection
- Output Directory Detection
- Static/Dynamic Detection
- Deploy Readiness
- Repository Score
- Warnings
- Recommendations
- Deep Analysis queue placeholder
- Result Store

## Flow

```text
Quick Analysis
↓
Deep Analysis
↓
Result Store
```

Deep Analysis is queued as a job reference in this phase. Durable worker-backed execution belongs to the Worker / Job System phase.

## Public API

External callers may import only:

```python
backend.engines.repository_analysis_engine.public
```

Do not import:

```python
backend.engines.repository_analysis_engine.internal.*
backend.engines.repository_analysis_engine.repository
backend.engines.repository_analysis_engine.models
```
