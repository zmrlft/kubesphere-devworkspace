# KubeSphere DevWorkspace

KubeSphere DevWorkspace 是一个轻量级的在线 IDE 解决方案，为企业内部开发团队提供云端、容器化的开发环境。它允许开发者快速创建一个预配置的开发环境，无需在本地安装任何语言环境或工具。

## 项目架构

DevWorkspace 由以下核心组件组成：

1. **WorkspaceTemplate CRD**：定义了一种开发环境的模板，包括使用的容器镜像、资源配额、存储大小等。
2. **WorkspaceInstance CRD**：用户创建的工作空间实例，引用了一个模板，并可以覆盖某些配置。
3. **DevWorkspace Operator**：监听 WorkspaceInstance 资源的变化，并创建相应的 Pod、PVC 和 Service 资源。

## 目录结构

```
kubesphere-devworkspace/
├── crds/                      # CRD 定义文件
│   ├── workspace_template_crd.yaml
│   ├── workspace_instance_crd.yaml
│   └── examples/              # 示例 CR 文件
│       ├── nodejs-template.yaml
│       ├── python-template.yaml
│       └── workspace-instance.yaml
├── operator/                  # Operator 代码
│   ├── src/
│   │   └── main.py            # Operator 主程序
│   ├── requirements.txt       # Python 依赖
│   ├── Dockerfile             # Operator 容器镜像构建文件
│   └── k8s/                   # Operator 部署文件
│       ├── rbac.yaml          # RBAC 配置
│       └── deployment.yaml    # Deployment 配置
├── docs/                      # 文档
└── install.sh                 # 安装脚本
```

## 快速开始

### 前提条件

- Kubernetes 集群（1.19+）
- kubectl 命令行工具

### 安装

1. 克隆仓库：

```bash
git clone https://github.com/kubesphere/devworkspace.git
cd devworkspace
```

2. 运行安装脚本：

```bash
./install.sh
```

这将安装 CRD、Operator 和示例模板。

### 创建工作空间

1. 查看可用的工作空间模板：

```bash
kubectl get workspacetemplates
```

2. 创建工作空间实例：

```bash
kubectl apply -f crds/examples/workspace-instance.yaml
```

3. 查看工作空间实例状态：

```bash
kubectl get workspaceinstances
```

4. 获取访问 URL：

```bash
kubectl get workspaceinstances my-nodejs-workspace -o jsonpath='{.status.url}'
```

## 自定义工作空间模板

您可以创建自己的工作空间模板，例如：

```yaml
apiVersion: devworkspace.kubesphere.io/v1alpha1
kind: WorkspaceTemplate
metadata:
  name: golang-1.17
spec:
  displayName: "Go 1.17"
  description: "A standard Go 1.17 environment."
  environment:
    image: "your-registry/dev-workspace-golang:1.17"
  resources:
    requests:
      cpu: "500m"
      memory: "1Gi"
    limits:
      cpu: "1"
      memory: "2Gi"
  storage:
    size: "5Gi"
```

## 工作空间实例配置

创建工作空间实例时，您可以覆盖模板中的某些配置：

```yaml
apiVersion: devworkspace.kubesphere.io/v1alpha1
kind: WorkspaceInstance
metadata:
  name: my-golang-workspace
  namespace: default
spec:
  templateRef: golang-1.17
  overrides:
    resources:
      limits:
        memory: "4Gi"
    storage:
      size: "10Gi"
``` 