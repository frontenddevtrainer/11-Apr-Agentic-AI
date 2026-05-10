#!/usr/bin/env bash
#
# terminate.sh — Tear down all Azure resources for the Capstone Project
#
# Usage:  ./terminate.sh
#
# This deletes the entire resource group, which removes:
#   - Azure Container Instance
#   - Azure Container Registry
#   - All associated resources
#
set -euo pipefail

RESOURCE_GROUP="rg-capstone-feedback"

echo "============================================"
echo "  Terminating Capstone Project on Azure"
echo "============================================"
echo ""

# Check if resource group exists
if ! az group show --name "$RESOURCE_GROUP" &>/dev/null; then
    echo "Resource group '$RESOURCE_GROUP' does not exist. Nothing to delete."
    exit 0
fi

# Show what will be deleted
echo "The following resources will be deleted:"
az resource list --resource-group "$RESOURCE_GROUP" --query "[].{Name:name, Type:type}" -o table 2>/dev/null
echo ""

read -p "Are you sure you want to delete ALL resources in '$RESOURCE_GROUP'? (y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Deleting resource group: $RESOURCE_GROUP ..."
echo "(This may take 1-2 minutes)"
az group delete \
    --name "$RESOURCE_GROUP" \
    --yes \
    --no-wait

echo ""
echo "============================================"
echo "  Teardown initiated!"
echo "============================================"
echo ""
echo "  Resource group '$RESOURCE_GROUP' is being deleted."
echo "  This runs in the background and may take a few minutes."
echo ""
echo "  To check status:"
echo "    az group show -n $RESOURCE_GROUP --query 'properties.provisioningState' -o tsv"
echo "============================================"
