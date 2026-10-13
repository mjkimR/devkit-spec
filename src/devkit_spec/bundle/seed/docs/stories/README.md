# User Stories

A directory managing user/actor-centric value journeys and concrete acceptance criteria.

---

## 1. Directory Structure & File Naming

Stories reside in subdirectories partitioned by user journey area. The area represents a categorizing shelf and does not need to match `capabilities/` areas.

```text
stories/
├── README.md
├── <area-1>/                  # e.g., onboarding, checkout, operations
│   └── US-<slug>.md
└── <area-2>/
    └── US-<slug>.md
```

- File name is `US-<slug>.md` and frontmatter `id` matches the file stem without sequence numbers.
- Frontmatter `area` must match the parent directory name. Only `README.md` resides directly under `stories/`.
- Create a new area once 3 or more stories cluster around the same journey; before that, place stories in the closest existing area. Moving a story between areas only requires moving the file and updating `area`; the `id` remains unchanged.
- Conventions are checked by `RULE-id-convention`, and `devkit rules fix` aligns `id`, `area`, and H1 heading token to the path.

## 2. Authoring Principles
1. **Actor Value Centric**: Describe stories from the perspective of actor value ("As an actor, I want to ..., so that ..."), rather than internal system actions.
2. **Acceptance Criteria**: Specify verifiable scenarios using `Given-When-Then` format.
3. **M:N Association with Capabilities**: Reference underpinning capabilities in the frontmatter `capabilities:` list using `CAP-<AREA>-<slug>` identifiers.

---

## 3. Template & CLI Discovery
- **Authoring a New Story**: Copy and adapt `.devkit/managed/spec/templates/story.md`.
- **Listing Registered Stories**: Dynamically discover stories via CLI frontmatter parsing grouped by area:
  ```bash
  devkit spec list story
  devkit spec list story --area <area>
  ```
