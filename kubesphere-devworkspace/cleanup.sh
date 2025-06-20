#!/bin/bash

# 清理脚本

set -e

echo "开始清理 DevWorkspace 相关资源..."

# 1. 删除示例 DevWorkspace 和 Template
echo "1. 删除示例 DevWorkspace 和 Template..."
kubectl delete devworkspaces.devworkspace.kubesphere.io --all --all-namespaces || true
kubectl delete devworkspacetemplates.devworkspace.kubesphere.io --all || true

# 2. 删除 RBAC
echo "2. 删除 RBAC..."
kubectl delete -f operator/k8s/rbac.yaml || true

# 3. 删除 CRD
echo "3. 删除 CRD..."
kubectl delete -f crds/devworkspace_crd.yaml || true
kubectl delete -f crds/devworkspacetemplate_crd.yaml || true

echo "清理完成！" 