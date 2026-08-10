# Mushroom House Developer Tool — Audit → Test → Clean

## Purpose

A reusable workflow for reducing project weight and removing stale dependencies, files, assets, and experiments **without breaking working behavior**.

The rule is simple:

> **Audit first. Establish a regression test. Clean only what the test and runtime evidence allow. Verify again after every cleanup pass.**

This workflow is for mature projects that have accumulated experiments, abandoned libraries, duplicate assets, generated files, or dependency snapshots over time.

---

## Core principle

**Do not infer “unused” from memory. Prove it.**

A dependency or file may be:

- directly imported,
- loaded indirectly,
- called through a subprocess,
- referenced by HTML/CSS/templates,
- required only at runtime,
- required only by deployment,
- or genuinely obsolete.

Static analysis is evidence, not permission to delete.

---

## The Audit → Test → Clean workflow

### 1. Audit the project

Collect ground truth automatically instead of inspecting files one by one.

Audit:

- direct Python imports,
- package requirements,
- frontend imports and package dependencies,
- subprocess calls,
- runtime entry points,
- large dependencies,
- large assets,
- unreferenced assets,
- caches and generated files,
- empty files,
- duplicate filenames,
- deployment-only files.

Classify findings as:

- **USED** — direct evidence exists.
- **PROBABLY UNUSED** — no evidence in the current runtime or source graph.
- **UNCERTAIN** — may be indirect, dynamic, framework-managed, or deployment-specific.
- **HIGH IMPACT** — large enough to materially affect bundle size, startup time, or deployment flexibility.

Never auto-delete from the audit step.

---

### 2. Map the real runtime path

Static imports alone are not enough.

Start from the actual runtime entry point and follow:

- imports,
- pipeline orchestration,
- `python -m ...` calls,
- direct script subprocesses,
- renderers,
- CLI tools,
- background workers,
- email or external delivery stages.

The goal is to answer:

> **What code actually executes when the user performs the product's main action?**

For a multi-stage application, write the runtime path explicitly.

Example:

```text
HTTP request
→ orchestrator
→ AI stages
→ HTML render
→ PDF render
→ delivery
→ cleanup
```

---

### 3. Establish a baseline integration test

Before deleting anything, create a test that proves the product's important behavior.

The integration test should exercise as much real application code as practical.

Prefer:

- real orchestration,
- real templates,
- real local file generation,
- real renderers,
- real parsing and validation.

Replace only expensive or destructive external effects when appropriate:

- AI calls → deterministic fixtures,
- email sending → intercepted/mock delivery,
- payments → fake provider,
- destructive cloud operations → test double.

The test must pass **before cleanup begins**.

This becomes the regression gate.

---

### 4. Build a fresh lean environment

Do not uninstall packages from the working environment while investigating.

Create a throwaway environment and install only the direct dependencies that runtime evidence says the application needs.

Then run the **same integration test** there.

If it passes, the lean dependency set has functional evidence behind it.

This protects the working development environment and makes rollback trivial.

---

### 5. Clean by category

Clean one category at a time.

Recommended order:

1. generated caches and temporary files,
2. obviously empty or abandoned scaffolding,
3. duplicate deployment entry points,
4. unused top-level dependencies,
5. abandoned dependency stacks,
6. unreferenced assets,
7. old workbench experiments,
8. obsolete configuration.

Do not mix unrelated refactors into cleanup.

---

### 6. Run the regression gate again

After each meaningful cleanup pass:

```text
baseline integration test
→ clean environment test
→ local production/build test
```

If any stage fails, the cleanup is not accepted yet.

A successful static audit is never a substitute for runtime verification.

---

### 7. Measure the result

For deployment problems, measure before and after.

Useful measurements include:

- dependency count,
- virtual-environment size,
- largest installed packages,
- repository asset size,
- deployment bundle size,
- build duration,
- cold-start behavior.

This distinguishes useful cleanup from cosmetic cleanup.

---

### 8. Commit only verified cleanup

A cleanup commit should contain:

- the regression test if newly introduced,
- the verified dependency/file cleanup,
- any required deployment configuration changes.

Avoid bundling feature work with cleanup.

Suggested commit style:

```text
Add pipeline integration test and remove legacy dependencies
```

---

## Decision rules

### A package may be removed when

- it has no direct runtime evidence,
- it is absent from a fresh lean environment,
- the integration test passes without it,
- and deployment/build checks still pass.

### A package should stay when

- it is directly imported,
- a runtime subprocess uses it,
- a framework requires it,
- or removing it breaks the regression gate.

### A file may be removed when

- it has no runtime/configuration/reference role,
- it is not part of deployment,
- and tests/builds pass without it.

### An asset may be removed when

- no source/template/CSS/JSON references it,
- no dynamic lookup convention requires it,
- and visual/regression checks remain correct.

---

## What not to do

Do **not**:

- delete packages just because `grep` finds no import,
- regenerate an entire dependency tree without a reason,
- uninstall from the only working environment during investigation,
- treat transitive packages as direct project dependencies,
- delete every unused-looking asset before checking dynamic filename lookup,
- optimize tiny files while ignoring a 100+ MB runtime dependency,
- change architecture before identifying the actual bottleneck,
- rely on deployment success alone as proof that the product works.

---

## Recommended project structure

For projects that use this workflow:

```text
project/
├── tests/
│   └── test_pipeline_integration.py
├── tools/
│   └── audit_project_dependencies.py
├── workbench/
│   └── temporary experiments
└── ...
```

`tools/` contains reusable project tooling.

`workbench/` contains disposable experiments and should not become permanent runtime code.

`tests/` contains permanent regression gates.

---

## Standard cleanup session

A normal session should look like this:

```text
1. Run audit.
2. Read one report.
3. Identify high-impact candidates.
4. Run baseline integration test.
5. Create fresh lean environment.
6. Test candidate dependency set.
7. Apply cleanup.
8. Run integration test again.
9. Run production/build check.
10. Measure size/build change.
11. Commit.
```

The developer should not spend the session repeatedly copying individual file contents into an assistant.

---

## Example: CV-Job-Matcher lesson

The Kiron project demonstrated why this workflow matters.

A large Python deployment bundle initially suggested many dependencies were the problem. Static auditing identified an old WeasyPrint/Pillow/FontTools stack as probably unused, while Playwright was confirmed as the real PDF renderer.

A permanent integration test was then added that exercised:

- the real pipeline orchestrator,
- real HTML rendering,
- real Playwright PDF rendering,
- deterministic AI fixtures,
- intercepted email delivery.

The same integration test passed in a fresh environment containing only the direct runtime dependencies.

That proved the legacy rendering stack could be removed safely.

Measurement then showed that Playwright itself remained the dominant package by size, revealing the **architectural** bottleneck rather than encouraging more blind dependency deletion.

The lesson:

> **Cleanup should reveal architecture, not hide it.**

---

## Mushroom House rule

**Audit → Test → Clean → Verify → Measure → Commit**

If the evidence is uncertain, do not delete yet.

If the regression gate is not green, cleanup is not complete.
