# KubeSphere DevWorkspace

KubeSphere DevWorkspace 是一个轻量级的在线 IDE 解决方案，为企业内部开发团队提供云端、容器化的开发环境。它允许开发者快速创建一个预配置的开发环境，无需在本地安装任何语言环境或工具。

## 功能特点

- **秒级创建**：从模板库中选择所需环境，一键创建空白但配置完备的 VS Code 工作空间
- **环境一致性**：团队成员通过选择平台提供的标准环境模板，确保开发基础环境的绝对一致
- **资源高效利用**：工作空间按需创建、集中管理，提升资源利用率
- **安全可控**：代码不落本地，提升安全性

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

## 项目结构

```
kubesphere-devworkspace/
├── crds/                      # CRD 定义文件
│   ├── workspace_template_crd.yaml
│   ├── workspace_instance_crd.yaml
│   └── examples/              # 示例 CR 文件
├── operator/                  # Operator 代码
│   ├── src/
│   │   └── main.py        # Operator 主程序
│   ├── requirements.txt       # Python 依赖
│   ├── Dockerfile             # Operator 容器镜像构建文件
│   └── k8s/                   # Operator 部署文件
├── docs/                      # 文档
└── install.sh                 # 安装脚本
```

## 文档

- [架构设计](docs/ARCHITECTURE.md)
- [CRD 规范](docs/CRD_SPEC.md)
- [测试指南](docs/TESTING.md)
- [详细文档](docs/README.md)

## 贡献

欢迎贡献代码、报告问题或提出改进建议。请参阅 [贡献指南](CONTRIBUTING.md)。

## 许可证

本项目采用 Apache 2.0 许可证。详见 [LICENSE](LICENSE) 文件。 