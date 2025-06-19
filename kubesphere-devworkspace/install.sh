#!/bin/bash

# 安装 CRD
echo "Installing CRDs..."
kubectl apply -f crds/workspace_template_crd.yaml
kubectl apply -f crds/workspace_instance_crd.yaml

# 安装 RBAC
echo "Installing RBAC..."
kubectl apply -f operator/k8s/rbac.yaml

# 安装 Operator
echo "Installing Operator..."
kubectl apply -f operator/k8s/deployment.yaml

# 等待 Operator 就绪
echo "Waiting for Operator to be ready..."
kubectl -n kube-system rollout status deployment devworkspace-operator

# 创建示例模板
echo "Creating example templates..."
kubectl apply -f crds/examples/nodejs-template.yaml
kubectl apply -f crds/examples/python-template.yaml

echo "Installation completed successfully!"
echo "You can now create a workspace instance with:"
echo "kubectl apply -f crds/examples/workspace-instance.yaml" 