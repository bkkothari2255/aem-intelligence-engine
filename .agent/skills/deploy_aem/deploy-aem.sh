#!/bin/bash
# Skill: deploy-aem
# Description: Deploys the AEM project using Maven's autoInstallPackage profile.

echo "[$(date)] Starting AEM Deployment..."
echo "Running: mvn -f aem-core/pom.xml clean install -PautoInstallPackage -Dmaven.repo.local=/tmp/aem-core-repo"
mvn -f aem-core/pom.xml clean install -PautoInstallPackage -Dmaven.repo.local=/tmp/aem-core-repo

if [ $? -eq 0 ]; then
    echo "[$(date)] AEM Deployment Finished Successfully."
else
    echo "[$(date)] AEM Deployment Failed."
    exit 1
fi
