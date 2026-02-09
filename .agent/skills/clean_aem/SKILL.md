---
name: clean-aem
description: Cleans the Maven build and removes old AEM logs to save space.
---

# clean-aem Skill

This skill performs a `mvn clean` and removes log files from `crx-quickstart/logs` that are older than 7 days.

## Usage

Run the script directly:
```bash
# Run everything
./.agent/skills/clean_aem/clean-aem.sh

# Skip Maven clean
./.agent/skills/clean_aem/clean-aem.sh --skip-mvn

# Skip Log cleanup
./.agent/skills/clean_aem/clean-aem.sh --skip-logs
```

Or trigger via workflow.
