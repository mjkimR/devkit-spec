# Capabilities

A directory managing the durable system capabilities (WBS Functional Decomposition) provided by the system.

---

## 1. Directory Structure & File Naming
Create subdirectories by functional area, and write individual capability documents within them:

```text
capabilities/
├── README.md
├── <area-1>/                  # e.g., auth, billing, notification, etc.
│   └── CAP-<AREA>-<slug>.md   # <AREA> is uppercase abbreviation of area (e.g., auth -> AUTH)
└── <area-2>/
    └── CAP-<AREA>-<slug>.md
```

- File name is `CAP-<AREA>-<slug>.md` and frontmatter `id` matches the file stem without sequence numbers.
- Frontmatter `area` must match the parent directory name.
- Conventions are checked by `RULE-id-convention`, and `devkit rules fix` aligns `id`, `area`, and H1 heading token to the path.
- **Authoring a New Capability**: Copy and adapt `.devkit/managed/spec/templates/capability.md`.
- **Listing Registered Capabilities**: Dynamically discover capabilities via CLI frontmatter parsing:
  ```bash
  devkit spec list capability
  devkit spec list capability --area <area>
  ```

## 2. Authoring Principles
1. **Durable Functional Specification**: Define permanent system capabilities and responsibilities, not transient tickets.
2. **M:N Association with Stories**: Reference associated user stories using `US-<slug>` identifiers in the frontmatter `stories:` list.
3. **Normative Force**: Express business rules explicitly using RFC 2119 keywords (`MUST`, `SHOULD`, `MAY`).
