#!/bin/bash

# 安装脚本

set -e

# 1. 安装 CRD
echo "1. 安装 CRD..."
kubectl apply -f crds/devworkspacetemplate_crd.yaml
kubectl apply -f crds/devworkspace_crd.yaml

# 等待 CRD 就绪
echo "等待 CRD 就绪..."
sleep 5

# 2. 创建示例模板
echo "2. 创建示例模板..."
kubectl apply -f crds/examples/nodejs-template.yaml
kubectl apply -f crds/examples/python-template.yaml

# 3. 安装 RBAC
echo "3. 安装 RBAC..."
kubectl apply -f operator/k8s/rbac.yaml

echo "安装完成！"
echo "您现在可以创建 DevWorkspace 实例了。"
echo "例如: kubectl apply -f crds/examples/devworkspace.yaml" 