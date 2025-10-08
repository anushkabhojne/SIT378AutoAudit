"""
Kubernetes Manager

Manages Kubernetes resources for compliance workflows.

Author: Senior Lead, AutoAudit
"""

from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging

class KubernetesManager:
    
    def __init__(self, kubeconfig_path: str = None):
        self._logger = logging.getLogger(self.__class__.__name__)
    
        try:
    
            if kubeconfig_path:
                config.load_kube_config(config_file = kubeconfig_path)
                self._logger.info(f"Loaded kubeconfig from {kubeconfig_path}")
    
            else:
                config.load_incluster_config()
                self._logger.info("Loaded in-cluster kubeconfig")
    
            self._core_v1_api = client.CoreV1Api()
            self._apps_v1_api = client.AppsV1Api()
    
        except Exception as e:
            self._logger.error(f"Failed to load Kubernetes configuration: {e}")
            raise

    def create_namespace(self, name: str):
        """
        Create a Kubernetes namespace.

        :param name: Namespace name.
        """
        
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=name))
        
        try:
            self._core_v1_api.create_namespace(namespace)
            self._logger.info(f"Namespace '{name}' created")
        
        except ApiException as e:
        
            if e.status == 409:
                self._logger.warning(f"Namespace '{name}' already exists")
        
            else:
                self._logger.error(f"Failed to create namespace '{name}': {e}")
                raise

    def delete_namespace(self, name: str):
        """
        Delete a Kubernetes namespace.

        :param name: Namespace name.
        """
        
        try:
            self._core_v1_api.delete_namespace(name)
            self._logger.info(f"Namespace '{name}' deleted")
        
        except ApiException as e:
            self._logger.error(f"Failed to delete namespace '{name}': {e}")
            raise

    def deploy_pod(self, namespace: str, pod_manifest: dict):
        """
        Deploy a pod in the specified namespace.

        :param namespace: Namespace name.
        :param pod_manifest: Pod manifest as a dictionary.
        """
        
        try:
            self._core_v1_api.create_namespaced_pod(namespace = namespace, body = pod_manifest)
            self._logger.info(f"Pod deployed in namespace '{namespace}'")
        
        except ApiException as e:
            self._logger.error(f"Failed to deploy pod in namespace '{namespace}': {e}")
            raise

    def delete_pod(self, namespace: str, pod_name: str):
        """
        Delete a pod in the specified namespace.

        :param namespace: Namespace name.
        :param pod_name: Pod name.
        """
        
        try:
            self._core_v1_api.delete_namespaced_pod(name = pod_name, namespace = namespace)
            self._logger.info(f"Pod '{pod_name}' deleted from namespace '{namespace}'")

        except ApiException as e:
            self._logger.error(f"Failed to delete pod '{pod_name}' in namespace '{namespace}': {e}")
            raise

    def list_pods(self, namespace: str):
        """
        List pods in the specified namespace.

        :param namespace: Namespace name.
        :return: List of pod names.
        """
        
        try:
            pods = self._core_v1_api.list_namespaced_pod(namespace = namespace)
            pod_names = [pod.metadata.name for pod in pods.items]
            self._logger.info(f"Listed pods in namespace '{namespace}': {pod_names}")
            return pod_names
        
        except ApiException as e:
            self._logger.error(f"Failed to list pods in namespace '{namespace}': {e}")
            raise
