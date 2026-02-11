---
name: deploy-frontend-to-aem
description: Builds the React frontend, copies artifacts to ui.apps, and deploys to AEM.
---

# Deploy Frontend to AEM

This skill automates the manual deployment steps for the frontend application. It is useful when standard Maven builds fail due to permission issues with frontend-maven-plugin or when you want to rapidly deploy frontend changes.

## Actions
1.  Runs `npm install` and `npm run build` in `ui.frontend`.
2.  Copies built JS/CSS artifacts to `ui.apps`.
3.  Runs `mvn clean install -PautoInstallPackage` in `ui.apps`.

## Usage
```bash
.agent/skills/deploy_frontend_to_aem/deploy.sh
```
