#!/usr/bin/env python3
"""
KubeSphere DevWorkspace Operator

该 Operator 负责监听 WorkspaceInstance 资源的创建、更新和删除事件，
并根据引用的 WorkspaceTemplate 创建相应的 Pod、PVC 和 Service 资源。
"""

import os
import kopf
import logging
import yaml
import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pykube import HTTPClient, KubeConfig, object_factory
from typing import Dict, Any, Optional
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("devworkspace-operator")

# 尝试加载 Kubernetes 配置
try:
    config.load_incluster_config()
    logger.info("Running inside Kubernetes cluster, using in-cluster config")
except config.ConfigException:
    try:
        config.load_kube_config()
        logger.info("Running outside Kubernetes cluster, using kubeconfig")
    except config.ConfigException:
        logger.error("Could not configure kubernetes client")
        raise

# 创建 Kubernetes API 客户端
api_client = client.ApiClient()
core_v1 = client.CoreV1Api(api_client)
custom_api = client.CustomObjectsApi(api_client)

# 定义 API 版本和资源组
API_GROUP = "devworkspace.kubesphere.io"
API_VERSION = "v1alpha1"
WORKSPACE_TEMPLATE_KIND = "WorkspaceTemplate"
WORKSPACE_INSTANCE_KIND = "WorkspaceInstance"

def get_workspace_template(name: str) -> Optional[Dict[str, Any]]:
    """
    获取指定名称的 WorkspaceTemplate 资源
    
    Args:
        name: WorkspaceTemplate 的名称
        
    Returns:
        WorkspaceTemplate 资源对象，如果找不到则返回 None
    """
    try:
        template = custom_api.get_cluster_custom_object(
            group=API_GROUP,
            version=API_VERSION,
            plural="workspacetemplates",
            name=name
        )
        logger.info(f"Found template: {name}")
        return template
    except ApiException as e:
        if e.status == 404:
            logger.error(f"Template {name} not found")
            return None
        else:
            logger.error(f"Error getting template {name}: {e}")
            raise

def merge_configs(template_spec: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并模板配置和实例中的覆盖配置
    
    Args:
        template_spec: 模板的 spec 部分
        overrides: 实例中的覆盖配置
        
    Returns:
        合并后的配置
    """
    result = template_spec.copy()
    
    # 如果没有覆盖配置，直接返回模板配置
    if not overrides:
        return result
        
    # 处理资源覆盖
    if 'resources' in overrides and 'resources' in result:
        for resource_type in ['requests', 'limits']:
            if resource_type in overrides.get('resources', {}) and resource_type in result.get('resources', {}):
                result['resources'][resource_type].update(overrides['resources'][resource_type])
            elif resource_type in overrides.get('resources', {}):
                if 'resources' not in result:
                    result['resources'] = {}
                result['resources'][resource_type] = overrides['resources'][resource_type]
    
    # 处理存储覆盖
    if 'storage' in overrides and 'storage' in result:
        result['storage'].update(overrides['storage'])
    elif 'storage' in overrides:
        result['storage'] = overrides['storage']
    
    return result

def create_pvc(instance_name: str, namespace: str, storage_size: str) -> str:
    """
    创建 PersistentVolumeClaim 资源
    
    Args:
        instance_name: 工作空间实例的名称
        namespace: 命名空间
        storage_size: 存储大小
        
    Returns:
        创建的 PVC 的名称
    """
    pvc_name = f"{instance_name}-workspace"
    
    pvc_manifest = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": pvc_name,
            "namespace": namespace
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {
                "requests": {
                    "storage": storage_size
                }
            }
        }
    }
    
    try:
        core_v1.create_namespaced_persistent_volume_claim(
            namespace=namespace,
            body=pvc_manifest
        )
        logger.info(f"Created PVC: {pvc_name}")
        return pvc_name
    except ApiException as e:
        if e.status == 409:  # Already exists
            logger.info(f"PVC {pvc_name} already exists")
            return pvc_name
        else:
            logger.error(f"Error creating PVC {pvc_name}: {e}")
            raise

def create_pod(
    instance_name: str, 
    namespace: str, 
    pvc_name: str, 
    image: str, 
    resources: Dict[str, Any],
    ports: list
) -> str:
    """
    创建 Pod 资源
    
    Args:
        instance_name: 工作空间实例的名称
        namespace: 命名空间
        pvc_name: PVC 的名称
        image: 容器镜像
        resources: 资源配置
        ports: 端口配置
        
    Returns:
        创建的 Pod 的名称
    """
    pod_name = f"{instance_name}"
    
    container_ports = []
    if ports:
        for port in ports:
            container_ports.append({
                "name": port.get("name", f"port-{port['containerPort']}"),
                "containerPort": port["containerPort"],
                "protocol": port.get("protocol", "TCP")
            })
    
    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "namespace": namespace,
            "labels": {
                "app": "devworkspace",
                "instance": instance_name
            }
        },
        "spec": {
            "containers": [{
                "name": "vscode-server",
                "image": image,
                "ports": container_ports,
                "volumeMounts": [{
                    "name": "workspace-storage",
                    "mountPath": "/workspace"
                }],
                "resources": resources,
                "command": ["code-server", "--bind-addr", "0.0.0.0:8080", "--auth", "none", "/workspace"]
            }],
            "volumes": [{
                "name": "workspace-storage",
                "persistentVolumeClaim": {
                    "claimName": pvc_name
                }
            }]
        }
    }
    
    try:
        core_v1.create_namespaced_pod(
            namespace=namespace,
            body=pod_manifest
        )
        logger.info(f"Created Pod: {pod_name}")
        return pod_name
    except ApiException as e:
        if e.status == 409:  # Already exists
            logger.info(f"Pod {pod_name} already exists")
            return pod_name
        else:
            logger.error(f"Error creating Pod {pod_name}: {e}")
            raise

def create_service(instance_name: str, namespace: str, ports: list) -> str:
    """
    创建 Service 资源
    
    Args:
        instance_name: 工作空间实例的名称
        namespace: 命名空间
        ports: 端口配置
        
    Returns:
        创建的 Service 的名称
    """
    service_name = f"{instance_name}"
    
    service_ports = []
    if ports:
        for port in ports:
            service_ports.append({
                "name": port.get("name", f"port-{port['containerPort']}"),
                "port": port["containerPort"],
                "targetPort": port["containerPort"],
                "protocol": port.get("protocol", "TCP")
            })
    else:
        # 默认端口
        service_ports.append({
            "name": "http",
            "port": 8080,
            "targetPort": 8080,
            "protocol": "TCP"
        })
    
    service_manifest = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": service_name,
            "namespace": namespace
        },
        "spec": {
            "selector": {
                "app": "devworkspace",
                "instance": instance_name
            },
            "ports": service_ports
        }
    }
    
    try:
        core_v1.create_namespaced_service(
            namespace=namespace,
            body=service_manifest
        )
        logger.info(f"Created Service: {service_name}")
        return service_name
    except ApiException as e:
        if e.status == 409:  # Already exists
            logger.info(f"Service {service_name} already exists")
            return service_name
        else:
            logger.error(f"Error creating Service {service_name}: {e}")
            raise

def get_service_url(service_name: str, namespace: str) -> str:
    """
    获取服务的访问 URL，带有重试逻辑以等待 ClusterIP 分配
    
    Args:
        service_name: 服务名称
        namespace: 命名空间
        
    Returns:
        服务的访问 URL，如果超时则返回 "Unknown"
    """
    retries = 10
    delay = 2  # seconds
    for i in range(retries):
        try:
            service = core_v1.read_namespaced_service(
                name=service_name,
                namespace=namespace
            )
            cluster_ip = service.spec.cluster_ip
            if cluster_ip:
                port = service.spec.ports[0].port
                logger.info(f"Service {service_name} has ClusterIP {cluster_ip}")
                return f"http://{cluster_ip}:{port}"
            else:
                logger.info(f"Service {service_name} does not have a ClusterIP yet. Retrying... ({i+1}/{retries})")
                time.sleep(delay)
        except ApiException as e:
            logger.error(f"Error getting service {service_name}: {e}. Retrying... ({i+1}/{retries})")
            time.sleep(delay)
            
    logger.error(f"Failed to get ClusterIP for service {service_name} after {retries} retries.")
    return "Unknown"

@kopf.on.create('devworkspace.kubesphere.io', 'v1alpha1', 'workspaceinstances')
def create_workspace_instance(spec, meta, status, name, namespace, logger, **kwargs):
    """
    处理 WorkspaceInstance 的创建事件
    """
    logger.info(f"Creating workspace instance: {name} in namespace {namespace}")
    
    # 立即设置一个初始状态，表示正在处理
    patch_status(name, namespace, {"phase": "Provisioning", "message": "Creating resources..."})

    # 获取模板引用
    template_ref = spec.get('templateRef')
    if not template_ref:
        message = "No templateRef specified"
        patch_status(name, namespace, {"phase": "Failed", "message": message})
        return {"message": message}
    
    # 获取模板
    template = get_workspace_template(template_ref)
    if not template:
        message = f"Template {template_ref} not found"
        patch_status(name, namespace, {"phase": "Failed", "message": message})
        return {"message": message}
    
    # 合并配置
    template_spec = template.get('spec', {})
    overrides = spec.get('overrides', {})
    config = merge_configs(template_spec, overrides)
    
    # 获取配置参数
    image = config.get('environment', {}).get('image')
    if not image:
        message = "No image specified in template"
        patch_status(name, namespace, {"phase": "Failed", "message": message})
        return {"message": message}
    
    resources = config.get('resources', {})
    storage_size = config.get('storage', {}).get('size', '10Gi')
    ports = config.get('ports', [])
    
    try:
        # 创建 PVC
        pvc_name = create_pvc(name, namespace, storage_size)
        
        # 创建 Pod
        pod_name = create_pod(name, namespace, pvc_name, image, resources, ports)
        
        # 创建 Service
        service_name = create_service(name, namespace, ports)

        # 检查 Pod 是否运行
        wait_for_pod_running(pod_name, namespace, logger)
        
        # 获取服务 URL (现在带有重试逻辑)
        url = get_service_url(service_name, namespace)
        
        # 更新最终状态
        final_status = {
            "phase": "Running",
            "message": "Workspace is ready",
            "podName": pod_name,
            "pvcName": pvc_name,
            "serviceName": service_name,
            "url": url
        }
        patch_status(name, namespace, final_status)
        logger.info(f"Workspace instance {name} is running at {url}")

    except kopf.TemporaryError as e:
        # If waiting times out, Kopf will automatically retry.
        # Let the exception propagate after patching the status.
        message = f"Failed to create workspace, will retry: {e}"
        patch_status(name, namespace, {"phase": "Provisioning", "message": message})
        raise
    except Exception as e:
        # For other unrecoverable errors, set the status to Failed.
        logger.error(f"Failed to create workspace instance {name}: {e}", exc_info=True)
        message = f"An unexpected error occurred: {e}"
        patch_status(name, namespace, {"phase": "Failed", "message": message})

@kopf.on.update('devworkspace.kubesphere.io', 'v1alpha1', 'workspaceinstances')
def update_workspace_instance(spec, meta, status, name, namespace, logger, **kwargs):
    """
    处理 WorkspaceInstance 的更新事件
    """
    logger.info(f"Updating workspace instance: {name} in namespace {namespace}")
    
    # 获取当前状态
    current_phase = status.get('phase')
    if current_phase == "Failed":
        logger.info(f"Instance {name} is in Failed state, skipping update")
        return
    
    # 获取模板引用
    template_ref = spec.get('templateRef')
    if not template_ref:
        return {"status": {"phase": "Failed", "message": "No templateRef specified"}}
    
    # 获取模板
    template = get_workspace_template(template_ref)
    if not template:
        return {"status": {"phase": "Failed", "message": f"Template {template_ref} not found"}}
    
    # 合并配置
    template_spec = template.get('spec', {})
    overrides = spec.get('overrides', {})
    config = merge_configs(template_spec, overrides)
    
    # 获取配置参数
    image = config.get('environment', {}).get('image')
    if not image:
        return {"status": {"phase": "Failed", "message": "No image specified in template"}}
    
    resources = config.get('resources', {})
    storage_size = config.get('storage', {}).get('size', '10Gi')
    ports = config.get('ports', [])
    
    # 获取当前的 Pod、PVC 和 Service
    pod_name = status.get('podName')
    pvc_name = status.get('pvcName')
    service_name = status.get('serviceName')
    
    # 如果没有 PVC，创建一个
    if not pvc_name:
        pvc_name = create_pvc(name, namespace, storage_size)
    
    # 如果没有 Pod，创建一个
    if not pod_name:
        pod_name = create_pod(name, namespace, pvc_name, image, resources, ports)
    
    # 如果没有 Service，创建一个
    if not service_name:
        service_name = create_service(name, namespace, ports)
    
    # 获取服务 URL
    url = get_service_url(service_name, namespace)
    
    # Update status
    final_status = {
        "phase": "Running",
        "podName": pod_name,
        "pvcName": pvc_name,
        "serviceName": service_name,
        "url": url
    }
    patch_status(name, namespace, final_status)
    logger.info(f"Workspace instance {name} status updated.")

@kopf.on.delete('devworkspace.kubesphere.io', 'v1alpha1', 'workspaceinstances')
def delete_workspace_instance(spec, meta, status, name, namespace, logger, **kwargs):
    """
    处理 WorkspaceInstance 的删除事件
    """
    logger.info(f"Deleting workspace instance: {name} in namespace {namespace}")
    
    # 如果 status 为空，说明实例可能从未成功创建，直接返回
    if not status:
        logger.warning(f"Workspace instance {name} has no status, nothing to delete.")
        return

    # 获取当前的 Pod、PVC 和 Service
    pod_name = status.get('podName')
    pvc_name = status.get('pvcName')
    service_name = status.get('serviceName')
    
    # 删除 Pod
    if pod_name:
        try:
            core_v1.delete_namespaced_pod(
                name=pod_name,
                namespace=namespace
            )
            logger.info(f"Deleted Pod: {pod_name}")
        except ApiException as e:
            if e.status != 404:  # 忽略 "Not Found" 错误
                logger.error(f"Error deleting Pod {pod_name}: {e}")
    
    # 删除 Service
    if service_name:
        try:
            core_v1.delete_namespaced_service(
                name=service_name,
                namespace=namespace
            )
            logger.info(f"Deleted Service: {service_name}")
        except ApiException as e:
            if e.status != 404:  # 忽略 "Not Found" 错误
                logger.error(f"Error deleting Service {service_name}: {e}")
    
    # 删除 PVC（可选，取决于是否要保留数据）
    # 在实际使用中，可能需要根据策略来决定是否删除 PVC
    if pvc_name:
        try:
            core_v1.delete_namespaced_persistent_volume_claim(
                name=pvc_name,
                namespace=namespace
            )
            logger.info(f"Deleted PVC: {pvc_name}")
        except ApiException as e:
            if e.status != 404:  # 忽略 "Not Found" 错误
                logger.error(f"Error deleting PVC {pvc_name}: {e}")
    
    # 不需要返回任何状态，因为资源正在被删除

def patch_status(name: str, namespace: str, status: Dict[str, Any]):
    """
    通过 patch 方法更新 WorkspaceInstance 的状态
    """
    try:
        custom_api.patch_namespaced_custom_object_status(
            group=API_GROUP,
            version=API_VERSION,
            namespace=namespace,
            plural="workspaceinstances",
            name=name,
            body={"status": status}
        )
    except ApiException as e:
        logger.error(f"Failed to patch status for {name}: {e}")

def wait_for_pod_running(pod_name: str, namespace: str, logger):
    """
    等待 Pod 进入 Running 状态
    """
    retries = 30 # 30 * 10s = 5 minutes timeout
    delay = 10
    for i in range(retries):
        try:
            pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            if pod.status.phase == 'Running':
                logger.info(f"Pod {pod_name} is running.")
                return
            elif pod.status.phase == 'Failed' or pod.status.phase == 'Unknown':
                 raise kopf.PermanentError(f"Pod {pod_name} entered {pod.status.phase} state.")
            else:
                logger.info(f"Pod {pod_name} is in {pod.status.phase} phase. Waiting...")
                time.sleep(delay)
        except ApiException as e:
            logger.error(f"Error reading pod status for {pod_name}: {e}")
            time.sleep(delay)
    
    raise kopf.TemporaryError(f"Pod {pod_name} did not become ready in time.", delay=60)

def main():
    """
    主函数
    """
    logger.info("Starting KubeSphere DevWorkspace Operator")
    kopf.run()

if __name__ == "__main__":
    main() 