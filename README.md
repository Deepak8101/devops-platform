<<<<<<< HEAD
# devops-platform
MY_REPO
=======
# 🚀 Cloud-Native DevOps Platform

A production-grade microservices platform built with modern DevOps tooling.

## Architecture

- **3 Python/Flask Microservices** — Auth, Order, Recommendation
- **API Gateway** — Nginx reverse proxy
- **Kubernetes** — Container orchestration
- **Redis** — Caching layer
- **PostgreSQL** — Persistent storage
- **Prometheus + Grafana** — Observability
- **ArgoCD** — GitOps deployments
- **GitHub Actions** — CI/CD pipelines
- **Terraform** — Infrastructure as Code

## Project Structure
```
devops-platform/
├── services/          # Microservices source code
├── kubernetes/        # K8s manifests
├── monitoring/        # Prometheus & Grafana configs
├── gitops/            # ArgoCD applications
├── ci-cd/             # GitHub Actions workflows
├── terraform/         # Infrastructure as Code
├── scripts/           # Utility scripts
└── docs/              # Architecture documentation
```

## Getting Started

See [docs/setup.md](docs/setup.md) for full setup instructions.
>>>>>>> a258942 (feat: initialize devops-platform project structure)
