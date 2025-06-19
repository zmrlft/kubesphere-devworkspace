#!/bin/bash

# 清理脚本，用于删除测试资源

echo "===== KubeSphere DevWorkspace 清理脚本 ====="

# 1. 删除工作空间实例
echo "1. 删除工作空间实例..."
kubectl delete workspaceinstance my-nodejs-workspace --ignore-not-found

# 2. 删除工作空间模板
echo "2. 删除工作空间模板..."
kubectl delete workspacetemplate nodejs-16 python-3.9 --ignore-not-found

# 3. 删除 RBAC 资源
echo "3. 删除 RBAC 资源..."
kubectl delete -f operator/k8s/rbac.yaml --ignore-not-found

# 4. 删除 CRD
echo "4. 删除 CRD..."
kubectl delete -f crds/workspace_instance_crd.yaml --ignore-not-found
kubectl delete -f crds/workspace_template_crd.yaml --ignore-not-found

echo "===== 清理完成 =====" 