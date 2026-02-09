---
name: deploy-aem
description: Deploys the project to valid local AEM instance.
---

# deploy-aem Skill

This skill deploys the AEM project using the `autoInstallPackage` Maven profile.

## Usage

```bash
./.agent/skills/deploy_aem/deploy-aem.sh
```

## Requirements
- Maven installed and on PATH
- AEM running on localhost:4502 (default)
