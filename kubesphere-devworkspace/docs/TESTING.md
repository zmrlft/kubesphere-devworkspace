# KubeSphere DevWorkspace 测试指南

本文档提供了如何在本地 Kubernetes 集群上测试 KubeSphere DevWorkspace 的详细步骤。

## 前提条件

- 运行中的 Kubernetes 集群（1.19+）
- kubectl 命令行工具
- Python 3.9+ (如果要本地运行 Operator)

## 测试步骤

### 1. 安装 CRD

首先，安装 WorkspaceTemplate 和 WorkspaceInstance CRD：

```bash
kubectl apply -f crds/workspace_template_crd.yaml
kubectl apply -f crds/workspace_instance_crd.yaml
```

验证 CRD 已安装：

```bash
kubectl get crd | grep devworkspace.kubesphere.io
```

应该看到以下输出：

```
workspacetemplates.devworkspace.kubesphere.io    2023-xx-xxTxx:xx:xxZ
workspaceinstances.devworkspace.kubesphere.io    2023-xx-xxTxx:xx:xxZ
```

### 2. 创建 RBAC 资源

安装 Operator 所需的 RBAC 资源：

```bash
kubectl apply -f operator/k8s/rbac.yaml
```

### 3. 本地运行 Operator（用于开发测试）

如果您想在本地运行 Operator 进行测试，可以执行以下命令：

```bash
# 安装依赖
cd operator
pip install -r requirements.txt

# 运行 Operator
python src/main.py
```

### 4. 或者，部署 Operator 到集群

如果您想将 Operator 部署到集群中，可以执行以下命令：

```bash
# 构建镜像（需要 Docker）
cd operator
docker build -t kubesphere/devworkspace-operator:latest .

# 推送镜像（如果需要）
docker push kubesphere/devworkspace-operator:latest

# 部署 Operator
kubectl apply -f k8s/deployment.yaml
```

### 5. 创建工作空间模板

创建示例工作空间模板：

```bash
kubectl apply -f crds/examples/nodejs-template.yaml
kubectl apply -f crds/examples/python-template.yaml
```

验证模板已创建：

```bash
kubectl get workspacetemplates
```

应该看到以下输出：

```
NAME         DISPLAYNAME   IMAGE                        AGE
nodejs-16    Node.js 16    codercom/code-server:4.9.1   1m
python-3.9   Python 3.9    codercom/code-server:4.9.1   1m
```

### 6. 创建工作空间实例

创建示例工作空间实例：

```bash
kubectl apply -f crds/examples/workspace-instance.yaml
```

验证实例已创建：

```bash
kubectl get workspaceinstances
```

应该看到以下输出：

```
NAME                 TEMPLATE    PHASE     URL                           AGE
my-nodejs-workspace  nodejs-16   Running   http://10.xx.xx.xx:8080       1m
```

### 7. 验证资源创建

检查是否创建了相应的 Pod、PVC 和 Service：

```bash
# 检查 Pod
kubectl get pods | grep my-nodejs-workspace

# 检查 PVC
kubectl get pvc | grep my-nodejs-workspace

# 检查 Service
kubectl get svc | grep my-nodejs-workspace
```

### 8. 访问工作空间

获取工作空间的访问 URL：

```bash
kubectl get workspaceinstances my-nodejs-workspace -o jsonpath='{.status.url}'
```

如果您在本地集群上运行，可能需要使用端口转发来访问工作空间：

```bash
kubectl port-forward svc/my-nodejs-workspace 8080:8080
```

然后在浏览器中访问 http://localhost:8080

### 9. 测试工作空间功能

在工作空间中，您可以：

1. 使用终端克隆代码仓库：
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. 安装依赖并运行应用程序：
   ```bash
   # 对于 Node.js 项目
   npm install
   npm start
   ```

3. 编辑代码并保存更改。

### 10. 清理资源

测试完成后，清理资源：

```bash
# 删除工作空间实例
kubectl delete workspaceinstance my-nodejs-workspace

# 删除工作空间模板
kubectl delete workspacetemplate nodejs-16 python-3.9

# 删除 Operator（如果已部署到集群）
kubectl delete -f operator/k8s/deployment.yaml

# 删除 RBAC 资源
kubectl delete -f operator/k8s/rbac.yaml

# 删除 CRD
kubectl delete -f crds/workspace_instance_crd.yaml
kubectl delete -f crds/workspace_template_crd.yaml
```

## 常见问题排查

### Operator 无法找到模板

如果工作空间实例的状态为 `Failed`，并且消息为 `Template xxx not found`，请检查：

1. 模板是否存在：
   ```bash
   kubectl get workspacetemplates
   ```

2. 模板名称是否与实例中引用的名称匹配。

### Pod 无法启动

如果 Pod 无法启动，请检查 Pod 的事件和日志：

```bash
# 检查 Pod 状态
kubectl describe pod my-nodejs-workspace

# 检查 Pod 日志
kubectl logs my-nodejs-workspace
```

### 无法访问工作空间

如果无法访问工作空间，请检查：

1. Service 是否正常：
   ```bash
   kubectl describe service my-nodejs-workspace
   ```

2. Pod 是否正常运行：
   ```bash
   kubectl get pod my-nodejs-workspace
   ```

3. 尝试使用端口转发：
   ```bash
   kubectl port-forward pod/my-nodejs-workspace 8080:8080
   ```