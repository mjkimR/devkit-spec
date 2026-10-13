# Reference and Research Materials

A free-form repository to store **any reference materials** relevant to the project, such as research findings, technical spikes, external API specifications, article clippings, and benchmark results.

---

## 1. Operating Principles: Free-form
- **Format-Agnostic**: Store reference materials in any format, including Markdown (`.md`), JSON, plain text, code snippets, or diagrams.
- **No Mandatory Metadata**: Creation dates and modification histories are managed by Git commit history; unnecessary frontmatter metadata is not enforced.
- **Project Autonomy**: File naming conventions and subfolder structures can be determined freely to suit each project's context.

---

## 2. Recommended Best Practices
To help team members and AI agents easily understand why materials are kept here, the following lightweight guidelines are recommended:

1. **Top Purpose Note (for Markdown files)**:
   - Add a 1-2 line note at the top of the file stating the collection purpose or source.
   ```markdown
   > **Purpose**: Scraped official documentation to verify webhook timeout retry policies.
   ```

2. **Accompanying Meta Files (for raw or read-only data)**:
   - For raw files that cannot be edited (`schema.sql`, `openapi.json`, etc.), place a `<filename>.meta.md` alongside to briefly describe the collection purpose and source links.
