"""
Batch download SKILL.md + references/*.md from SQLLivesiteAgents Availability skills.
Run with: python fetch_availability_skills.py
Requires: mcp_msdata_repo_get_file_content (run via copilot agent)
"""

# This is the mapping of source paths -> local destination paths
# Format: (ado_path, local_dir_relative_to_kql-templates/sqldb/)

FILES_TO_FETCH = [
    # ── failover ──
    ("Availability/failover/SKILL.md", "availability/failover/SKILL.md"),
    ("Availability/failover/references/knowledge.md", "availability/failover/references/knowledge.md"),
    ("Availability/failover/references/output.md", "availability/failover/references/output.md"),
    ("Availability/failover/references/principles.md", "availability/failover/references/principles.md"),
    ("Availability/failover/references/queries.md", "availability/failover/references/queries.md"),
    
    # ── quorum-loss ──
    ("Availability/quorum-loss/SKILL.md", "availability/quorum-loss/SKILL.md"),
    ("Availability/quorum-loss/references/knowledge.md", "availability/quorum-loss/references/knowledge.md"),
    ("Availability/quorum-loss/references/principles.md", "availability/quorum-loss/references/principles.md"),
    ("Availability/quorum-loss/references/queries.md", "availability/quorum-loss/references/queries.md"),
    
    # ── error-40613-state-126 → error-40613/ ──
    ("Availability/error-40613-state-126/SKILL.md", "availability/error-40613/error-40613-state-126-SKILL.md"),
    ("Availability/error-40613-state-126/references/knowledge.md", "availability/error-40613/references/state-126-knowledge.md"),
    ("Availability/error-40613-state-126/references/queries.md", "availability/error-40613/references/state-126-queries.md"),
    
    # ── error-40613-state-127 → error-40613/ ──
    ("Availability/error-40613-state-127/SKILL.md", "availability/error-40613/error-40613-state-127-SKILL.md"),
    ("Availability/error-40613-state-127/references/knowledge.md", "availability/error-40613/references/state-127-knowledge.md"),
    ("Availability/error-40613-state-127/references/queries.md", "availability/error-40613/references/state-127-queries.md"),
    
    # ── error-40613-state-129 → error-40613/ ──
    ("Availability/error-40613-state-129/SKILL.md", "availability/error-40613/error-40613-state-129-SKILL.md"),
    ("Availability/error-40613-state-129/references/knowledge.md", "availability/error-40613/references/state-129-knowledge.md"),
    ("Availability/error-40613-state-129/references/queries.md", "availability/error-40613/references/state-129-queries.md"),
    
    # ── high-sync-commit-wait ──
    ("Availability/high-sync-commit-wait/SKILL.md", "availability/high-sync-commit-wait/SKILL.md"),
    ("Availability/high-sync-commit-wait/references/knowledge.md", "availability/high-sync-commit-wait/references/knowledge.md"),
    ("Availability/high-sync-commit-wait/references/queries.md", "availability/high-sync-commit-wait/references/queries.md"),
    
    # ── seeding-rca ──
    ("Availability/seeding-rca/SKILL.md", "availability/seeding-rca/SKILL.md"),
    ("Availability/seeding-rca/references/knowledge.md", "availability/seeding-rca/references/knowledge.md"),
    ("Availability/seeding-rca/references/queries.md", "availability/seeding-rca/references/queries.md"),
    
    # ── long-reconfig-database → long-reconfig/ ──
    ("Availability/long-reconfig-database/SKILL.md", "availability/long-reconfig/SKILL.md"),
    ("Availability/long-reconfig-database/references/knowledge.md", "availability/long-reconfig/references/knowledge.md"),
    ("Availability/long-reconfig-database/references/principles.md", "availability/long-reconfig/references/principles.md"),
    ("Availability/long-reconfig-database/references/queries.md", "availability/long-reconfig/references/queries.md"),
    
    # ── update-slo ──
    ("Availability/update-slo/SKILL.md", "availability/update-slo/SKILL.md"),
    ("Availability/update-slo/references/knowledge.md", "availability/update-slo/references/knowledge.md"),
    ("Availability/update-slo/references/output.md", "availability/update-slo/references/output.md"),
    ("Availability/update-slo/references/principles.md", "availability/update-slo/references/principles.md"),
    ("Availability/update-slo/references/queries.md", "availability/update-slo/references/queries.md"),
    
    # ── login-failure-triage → login-failure/ ──
    ("Availability/login-failure-triage/SKILL.md", "availability/login-failure/SKILL.md"),
    ("Availability/login-failure-triage/references/knowledge.md", "availability/login-failure/references/knowledge.md"),
    ("Availability/login-failure-triage/references/queries.md", "availability/login-failure/references/queries.md"),
    
    # ── triage ──
    ("Availability/triage/SKILL.md", "availability/triage/SKILL.md"),
    ("Availability/triage/references/queries.md", "availability/triage/references/queries.md"),
    
    # ── unhealthy-worker-cl → MI ──
    ("Availability/unhealthy-worker-cl/SKILL.md", "mi-availability/unhealthy-worker-cl/SKILL.md"),
    ("Availability/unhealthy-worker-cl/references/knowledge.md", "mi-availability/unhealthy-worker-cl/references/knowledge.md"),
    ("Availability/unhealthy-worker-cl/references/principles.md", "mi-availability/unhealthy-worker-cl/references/principles.md"),
    ("Availability/unhealthy-worker-cl/references/queries.md", "mi-availability/unhealthy-worker-cl/references/queries.md"),
    
    # ── NodeHealth/node-health ──
    ("NodeHealth/node-health/SKILL.md", "availability/node-health/SKILL.md"),
    ("NodeHealth/node-health/references/knowledge.md", "availability/node-health/references/knowledge.md"),
    ("NodeHealth/node-health/references/principles.md", "availability/node-health/references/principles.md"),
    ("NodeHealth/node-health/references/queries.md", "availability/node-health/references/queries.md"),
]

# Total: 48 files
print(f"Total files to fetch: {len(FILES_TO_FETCH)}")
for src, dst in FILES_TO_FETCH:
    print(f"  {src} → {dst}")
