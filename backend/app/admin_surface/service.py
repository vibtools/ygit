from __future__ import annotations

from backend.app.admin_surface.schemas import (
    AdminAuditLogEntry,
    AdminDeploymentSummary,
    AdminHealthComponent,
    AdminMetric,
    AdminOperationsManifest,
    AdminOverview,
    AdminQueueStatus,
    AdminSettingsSummary,
    AdminUserSummary,
    AdminSystemMonitoring,
)
from backend.engines.platform_engine.public import platform_service


class AdminOperationsService:
    """Admin Operations Surface service.

    This is deliberately not an engine. It aggregates safe, read-oriented operational
    data through approved public APIs and contracts. It must not own tables, import
    providers, mutate engine-owned repositories, or expose secrets.
    """

    async def get_overview(self) -> AdminOverview:
        health = await platform_service.get_health()
        system = await platform_service.get_system_status()
        return AdminOverview(
            metrics=[
                AdminMetric(key="users", label="Users", value="restricted", status="unknown", description="User count requires live DB and Auth Engine read API."),
                AdminMetric(key="deployments", label="Deployments", value="restricted", status="unknown", description="Deployment counts come from Deployment History Engine in live runtime."),
                AdminMetric(key="failed_jobs", label="Failed Jobs", value="not_checked", status="unknown", description="Job aggregation requires live Worker / Job System query."),
                AdminMetric(key="queue", label="Queue", value=system.queue_status, status="ok", description="Queue status from Platform Engine skeleton."),
            ],
            health=[
                AdminHealthComponent(name="api", status="ok", description=health.status),
                AdminHealthComponent(name="database", status="not_checked", description=health.database),
                AdminHealthComponent(name="redis", status="not_checked", description=health.redis),
                AdminHealthComponent(name="worker", status="configured", description=health.worker),
            ],
            operations_focus=[
                "Platform Health",
                "Queue Status",
                "Audit Logs",
                "Deployments",
                "Users",
                "System Monitoring",
            ],
            boundary="Admin Surface -> /api/v1 -> approved engine public APIs. No Admin Engine, no provider direct access, no database direct mutation.",
        )

    async def get_queue_status(self) -> AdminQueueStatus:
        system = await platform_service.get_system_status()
        return AdminQueueStatus(
            status="configured" if system.queue_status else "unknown",
            queues=[
                AdminMetric(key="default", label="Default Queue", value="not_checked", status="unknown", description="Live queue length requires Redis/PostgreSQL runtime."),
                AdminMetric(key="deployments", label="Deployments Queue", value="not_checked", status="unknown", description="Deploy and redeploy jobs are dispatched through Deploy Pipeline."),
                AdminMetric(key="analysis", label="Analysis Queue", value="not_checked", status="unknown", description="Deep repository analysis jobs use Worker / Job System."),
                AdminMetric(key="webhooks", label="Webhooks Queue", value="not_checked", status="unknown", description="Webhook processing is worker-backed."),
            ],
            retry_policy={"max_attempts": 3, "owner": "Worker / Job System", "mode": "durable jobs table + queue transport"},
            notes=[
                "Worker owns only the jobs table.",
                "Worker dispatches to Engine Public APIs or Deploy Pipeline; it does not call providers directly.",
            ],
        )

    async def list_deployments(self) -> list[AdminDeploymentSummary]:
        return [
            AdminDeploymentSummary(
                message="Deployment operations data is exposed through Deploy Engine and Deployment History Engine public APIs in live runtime. No placeholder database mutation is performed by Admin Surface."
            )
        ]

    async def list_users(self) -> list[AdminUserSummary]:
        return [
            AdminUserSummary(
                message="User operations data belongs to Auth Engine. Admin Surface may display safe summaries only; password, tokens, and provider secrets are never exposed."
            )
        ]

    async def list_audit_logs(self) -> list[AdminAuditLogEntry]:
        return [
            AdminAuditLogEntry(
                event_name="audit.created",
                target_type="admin_surface",
                target_id="admin_panel_v0.1.0",
                message="Audit log surface is wired as immutable/read-only MVP section. Live rows belong to Audit Engine."
            )
        ]

    async def get_system_monitoring(self) -> AdminSystemMonitoring:
        health = await platform_service.get_health()
        system = await platform_service.get_system_status()
        return AdminSystemMonitoring(
            api="ok" if health.status == "ok" else "unknown",
            database="not_checked",
            redis="not_checked",
            worker="configured" if system.worker_status else "unknown",
            queue="configured" if system.queue_status else "unknown",
            provider_checks={"github": "not_checked", "cloudflare": "not_checked"},
            notes=[
                "Live provider checks must use provider health adapters, not direct admin provider calls.",
                "Sensitive configuration remains in environment/Coolify secrets, not Admin Panel state.",
            ],
        )

    async def get_settings_summary(self) -> AdminSettingsSummary:
        settings = await platform_service.get_settings_summary()
        flags = await platform_service.get_feature_flags()
        return AdminSettingsSummary(
            maintenance_banner=settings.maintenance_enabled,
            registration_enabled=settings.registration_enabled,
            allowed_repository_providers=settings.allowed_repository_providers,
            allowed_deployment_providers=settings.allowed_deployment_providers,
            templates_beta_enabled=flags.flags.get("templates_beta", False),
            sensitive_config_location=settings.sensitive_config_location,
            mutable_in_mvp=settings.mutable_in_mvp,
        )

    async def get_manifest(self) -> AdminOperationsManifest:
        return AdminOperationsManifest(
            primary_sections=[
                "Overview",
                "Platform Health",
                "Queue Status",
                "System Monitoring",
                "Deployments",
                "Users",
                "Audit Logs",
                "Settings",
            ]
        )


admin_operations_service = AdminOperationsService()
