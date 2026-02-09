---
description: Build the maven project and clean up old logs automatically
---

# Build and Clean Workflow

This workflow builds the Maven project and then runs the `clean-aem` skill to keep storage usage low.

## Steps

1. Run the Maven build:
```bash
mvn clean install -PautoInstallPackage
```

2. Run the clean-aem skill:
// turbo
```bash
./.agent/skills/clean_aem/clean-aem.sh
```
