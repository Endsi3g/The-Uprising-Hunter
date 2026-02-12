---
name: deployment-scaling-optimization
description: Plan and execute production deployment workflows with zero-downtime practices, observability, scaling, and cost control across frontend, backend, and data services. Use when shipping to production, hardening reliability, optimizing latency and spend, setting up monitoring and alerting, or preparing an app to handle real user traffic.
---

# Deployment Scaling Optimization

## Overview

Deploy and operate production applications with reliability-first processes and measurable service health.
Balance performance, availability, and budget from first release onward.

## Core Workflow

1. Define deployment topology and environment strategy.
2. Establish CI pipeline: test, build, package, deploy, verify.
3. Configure secrets and environment variables securely.
4. Add monitoring, alerting, and error tracking before launch.
5. Execute staged rollout with rollback plan.
6. Review production telemetry and tune scaling and cost.

## Platform Baseline

- Frontend deployment: Vercel.
- Backend and data: Supabase managed services by default.
- Alternative self-host path: containerized services for Railway or DigitalOcean.
- Keep regional latency low for Canadian users when possible.

## Reliability Controls

- Use health checks and smoke tests on each deployment.
- Require rollback command or procedure before production release.
- Keep SSL and HTTPS mandatory in all environments.
- Track error rates, latency, and saturation for core services.

## Monitoring and Alerting

- Use Sentry for exception monitoring and release correlation.
- Use uptime and synthetic checks for endpoint availability.
- Track web performance and API latency metrics after each release.
- Route critical alerts to team communication channels.

## Performance and Cost Optimization

- Enable CDN caching and edge delivery where safe.
- Use image optimization and lazy loading for frontend performance.
- Add data-layer indexing and query analysis for high-traffic paths.
- Set monthly budget targets and review spend drift regularly.

## Deployment Checklist

- CI pipeline green on target branch.
- Production environment variables verified.
- Migration compatibility and rollback confirmed.
- Monitoring dashboards and alerts active.
- Post-deploy validation steps completed.

## Example Invocations

- "Create a CI pipeline that deploys to Vercel and validates production health checks."
- "Design a scaling and observability plan for a Supabase-backed app with traffic growth."
