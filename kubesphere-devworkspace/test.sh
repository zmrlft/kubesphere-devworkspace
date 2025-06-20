#!/bin/bash

# 测试脚本，用于验证 KubeSphere DevWorkspace 的功能

set -e

echo "===== KubeSphere DevWorkspace 测试脚本 ====="

# 1. 安装 CRD
echo "1. 安装 CRD..."
kubectl apply -f crds/devworkspacetemplate_crd.yaml
kubectl apply -f crds/devworkspace_crd.yaml

# 等待 CRD 就绪
echo "等待 CRD 就绪..."
sleep 5

# 2. 验证 CRD 安装
echo "2. 验证 CRD 安装..."
kubectl get crd devworkspacetemplates.devworkspace.kubesphere.io
kubectl get crd devworkspaces.devworkspace.kubesphere.io

# 3. 创建示例模板
echo "3. 创建示例模板..."
kubectl apply -f crds/examples/nodejs-template.yaml
kubectl apply -f crds/examples/python-template.yaml

# 4. 验证模板创建
echo "4. 验证模板创建..."
kubectl get devworkspacetemplates

# 5. 安装 RBAC
echo "5. 安装 RBAC..."
kubectl apply -f operator/k8s/rbac.yaml

# 6. 本地运行 Operator（开发测试）
echo "6. 准备本地运行 Operator..."
echo "请在另一个终端中运行以下命令："
echo "cd $(pwd)/operator && pip install -r requirements.txt && python src/main.py"
echo "按回车键继续..."
read

# 7. 创建工作空间实例
echo "7. 创建 DevWorkspace 实例..."
kubectl apply -f crds/examples/devworkspace.yaml

# 8. 验证工作空间实例创建
echo "8. 验证 DevWorkspace 实例创建..."
echo "等待 DevWorkspace 实例就绪..."
sleep 10
kubectl get devworkspaces

# 9. 验证资源创建
echo "9. 验证资源创建..."
echo "Pod:"
kubectl get pods -l app=devworkspace,instance=my-nodejs-workspace
echo "PVC:"
kubectl get pvc -l app=devworkspace,instance=my-nodejs-workspace
echo "Service:"
kubectl get svc -l app=devworkspace,instance=my-nodejs-workspace

# 10. 获取访问 URL
echo "10. 获取访问 URL..."
URL=$(kubectl get devworkspace my-nodejs-workspace -o jsonpath='{.status.url}')
echo "工作空间访问 URL: $URL"

echo "如果您在本地集群上运行，可能需要使用端口转发来访问工作空间："
echo "kubectl port-forward svc/my-nodejs-workspace 8080:8080"
echo "然后在浏览器中访问 http://localhost:8080"

echo "===== 测试完成 ====="
echo "清理资源请运行 ./cleanup.sh" 