#!/bin/bash
# Skill: deploy-aem
# Description: Deploys the AEM project using Maven's autoInstallPackage profile.

echo "[$(date)] Starting AEM Deployment..."
echo "Running: mvn clean install -PautoInstallPackage"

# Use a temporary local repo if permissions are an issue, otherwise default
# Checking for the temp repo presence or just using standard first?
# Given previous errors, I should probably stick to what works for the user or make it robust.
# The user asked for "mvn clean install -PautoInstallPackage". I will stick to that exactly, 
# but maybe add the -Dmaven.repo.local arg if I detect I'm in the agent environment? 
# No, for the USER'S skill, it should use their environment. 
# However, if I am running it, I might need the flag. 
# I will write the standard command as requested.

mvn clean install -PautoInstallPackage

if [ $? -eq 0 ]; then
    echo "[$(date)] AEM Deployment Finished Successfully."
else
    echo "[$(date)] AEM Deployment Failed."
    exit 1
fi
