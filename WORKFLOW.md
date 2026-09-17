# AI Log Analysis Platform - Workflow Protocol

## Phase Overview

```
/refine → /design → /plan → /build → /review → /ship
```

Each phase has defined inputs, outputs, pass conditions, and rollback triggers.

---

## /refine - Requirements Clarification

### Purpose
Clarify ambiguous requirements, align on scope and priorities.

### Input
- User request or feature description
- Existing constraints (CLAUDE.md, DESIGN.md)

### Checklist
- [ ] Identify all ambiguous terms
- [ ] List assumptions made
- [ ] Confirm scope boundaries (in/out)
- [ ] Identify dependencies on external systems

### Output
- Clarified requirement document
- Scope statement with explicit exclusions
- Risk/assumption list

### Pass Condition
- User explicitly confirms understanding
- No open questions remain

### Rollback Trigger
- User rejects interpretation → restart /refine

---

## /design - Architecture Decision

### Purpose
Make technical decisions, update architecture docs.

### Input
- Clarified requirements from /refine
- Current DESIGN.md

### Checklist
- [ ] Evaluate architectural options
- [ ] Document trade-offs
- [ ] Update DESIGN.md if needed
- [ ] Verify consistency with tech stack contract

### Output
- Architecture Decision Record (ADR) if significant change
- Updated DESIGN.md (if modified)
- Component diagram (if new components)

### Pass Condition
- Design is consistent with CLAUDE.md constraints
- User approves approach

### Rollback Trigger
- Design violates red lines → back to /refine to adjust requirements
- User rejects approach → iterate /design

---

## /plan - Task Breakdown

### Purpose
Break work into discrete, testable tasks.

### Input
- Approved design from /design
- Current codebase state

### Checklist
- [ ] Break into tasks ≤ 2 hours each
- [ ] Identify task dependencies
- [ ] Assign priority order
- [ ] Estimate complexity (S/M/L)

### Output
- Task list with:
  - Description
  - Acceptance criteria
  - Dependencies
  - Estimated size

### Pass Condition
- All tasks have clear acceptance criteria
- Dependencies form a valid DAG (no cycles)
- User approves task list

### Rollback Trigger
- Tasks too vague → refine task descriptions
- Scope creep detected → back to /refine

---

## /build - Implementation

### Purpose
Write code, tests, and documentation.

### Input
- Approved task list from /plan
- CLAUDE.md constraints

### Checklist
- [ ] Implement feature code
- [ ] Write unit tests (critical paths must be covered)
- [ ] Run linter: `ruff check .` (backend), `pnpm lint` (frontend)
- [ ] Run tests: `pytest` (backend), `pnpm test` (frontend)
- [ ] Type check passes
- [ ] No hardcoded secrets

### Output
- Working code with tests
- Updated dependencies (if any)
- Commit(s) following Conventional Commits

### Pass Condition
- All checklist items green
- Tests pass
- Linter clean
- Code compiles/runs

### Rollback Trigger
- Tests fail → fix before proceeding
- Linter errors → fix before proceeding
- Red line violation → revert and redesign

### Artifacts
- Git commits
- Updated code files
- Test files

---

## /review - Quality Check

### Purpose
Verify implementation meets requirements and quality standards.

### Input
- Completed build from /build
- Original requirements from /refine

### Checklist
- [ ] Code review against DESIGN.md
- [ ] Security review (no injection, no hardcoded secrets)
- [ ] Test coverage adequate for critical paths
- [ ] Documentation updated (if API changed)
- [ ] Manual testing of happy path
- [ ] Edge case verification

### Output
- Review findings (if any)
- Sign-off or revision requests

### Pass Condition
- No blocking issues
- All revision requests addressed
- Manual test passes

### Rollback Trigger
- Security issue found → back to /build to fix
- Requirement mismatch → back to /refine to clarify

---

## /ship - Deployment

### Purpose
Deploy to target environment, verify production readiness.

### Input
- Reviewed and approved code from /review
- Deployment configuration

### Checklist
- [ ] Build artifacts (docker images)
- [ ] Run smoke tests
- [ ] Deploy to staging (if available)
- [ ] Verify health checks pass
- [ ] Deploy to production
- [ ] Monitor for errors (5 min)

### Output
- Deployed application
- Deployment record (commit SHA, timestamp, environment)

### Pass Condition
- Application running and healthy
- No errors in monitoring window
- User confirms functionality

### Rollback Trigger
- Health check fails → rollback deployment
- Errors spike → rollback deployment
- User reports critical bug → hotfix or rollback

---

## Phase Transition Rules

```
┌─────────┐     reject      ┌─────────┐
│ /refine │◄───────────────│ /design │
└────┬────┘                 └────┬────┘
     │ confirm                   │ approve
     ▼                           ▼
┌─────────┐     scope creep ┌─────────┐
│ /design │◄───────────────│  /plan  │
└────┬────┘                 └────┬────┘
     │ approve                   │ approve
     ▼                           ▼
┌─────────┐     red line    ┌─────────┐
│  /plan  │◄───────────────│ /build  │
└─────────┘    violation    └────┬────┘
                                 │ pass
                                 ▼
                            ┌─────────┐
                            │ /review │
                            └────┬────┘
                                 │ approve
                                 ▼
                            ┌─────────┐
                            │  /ship  │
                            └─────────┘
```

## Emergency Protocols

### Hotfix Path
For critical production bugs:
```
/refine (minimal) → /build → /review (expedited) → /ship
```
Skip /design and /plan if fix is obvious and localized.

### Rollback Decision Tree
1. Is production broken? → Immediate rollback
2. Is data at risk? → Immediate rollback
3. Is it a regression? → Rollback, then investigate
4. Is it a new edge case? → Hotfix forward
