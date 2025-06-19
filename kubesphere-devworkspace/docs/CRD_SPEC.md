# KubeSphere DevWorkspace CRD 规范

本文档详细说明了 KubeSphere DevWorkspace 中使用的两个 CRD 的规范。

## WorkspaceTemplate

`WorkspaceTemplate` 是一个集群级别的资源，定义了一种开发环境的模板。它包含了工作空间的基本配置，如容器镜像、资源配额、存储大小等。

### 字段说明

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `spec.displayName` | string | 是 | 在 UI 上展示的名字 |
| `spec.description` | string | 否 | 环境模板的描述信息 |
| `spec.environment.image` | string | 是 | 工作空间使用的容器镜像 |
| `spec.resources.requests.cpu` | string | 否 | CPU 请求量 |
| `spec.resources.requests.memory` | string | 否 | 内存请求量 |
| `spec.resources.limits.cpu` | string | 否 | CPU 限制量 |
| `spec.resources.limits.memory` | string | 否 | 内存限制量 |
| `spec.storage.size` | string | 否 | 存储大小，默认为 "10Gi" |
| `spec.ports` | array | 否 | 容器端口配置 |
| `spec.ports[].name` | string | 否 | 端口名称 |
| `spec.ports[].containerPort` | integer | 是 | 容器端口 |
| `spec.ports[].protocol` | string | 否 | 协议，默认为 "TCP" |

### 示例

```yaml
apiVersion: devworkspace.kubesphere.io/v1alpha1
kind: WorkspaceTemplate
metadata:
  name: nodejs-16
spec:
  displayName: "Node.js 16"
  description: "A standard Node.js 16 environment with npm and yarn."
  environment:
    image: "your-registry/dev-workspace-nodejs:16"
  resources:
    requests:
      cpu: "500m"
      memory: "2Gi"
    limits:
      cpu: "2"
      memory: "4Gi"
  storage:
    size: "10Gi"
  ports:
    - name: http
      containerPort: 8080
      protocol: TCP
```

## WorkspaceInstance

`WorkspaceInstance` 是一个命名空间级别的资源，表示一个实际运行的工作空间实例。它引用了一个 `WorkspaceTemplate`，并可以覆盖模板中的某些配置。

### 字段说明

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `spec.templateRef` | string | 是 | 引用的工作空间模板名称 |
| `spec.overrides.resources.requests.cpu` | string | 否 | 覆盖模板中的 CPU 请求量 |
| `spec.overrides.resources.requests.memory` | string | 否 | 覆盖模板中的内存请求量 |
| `spec.overrides.resources.limits.cpu` | string | 否 | 覆盖模板中的 CPU 限制量 |
| `spec.overrides.resources.limits.memory` | string | 否 | 覆盖模板中的内存限制量 |
| `spec.overrides.storage.size` | string | 否 | 覆盖模板中的存储大小 |

### 状态字段

| 字段 | 类型 | 描述 |
|------|------|------|
| `status.phase` | string | 工作空间的状态，可能的值为 "Pending", "Running", "Stopped", "Failed" |
| `status.message` | string | 状态的详细信息，特别是在失败时 |
| `status.url` | string | 访问工作空间的 URL |
| `status.podName` | string | 工作空间对应的 Pod 名称 |
| `status.pvcName` | string | 工作空间对应的 PVC 名称 |
| `status.serviceName` | string | 工作空间对应的 Service 名称 |

### 示例

```yaml
apiVersion: devworkspace.kubesphere.io/v1alpha1
kind: WorkspaceInstance
metadata:
  name: my-nodejs-workspace
  namespace: default
spec:
  templateRef: nodejs-16
  overrides:
    resources:
      limits:
        memory: "6Gi"
```

## 资源关系

`WorkspaceInstance` 引用 `WorkspaceTemplate`，然后 Operator 根据这两个资源创建 Kubernetes 原生资源：

```
WorkspaceTemplate <---- WorkspaceInstance
                            |
                            v
                        Pod + PVC + Service
``` 