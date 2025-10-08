"""
Container Runtime Manager

Manages container runtime operations for compliance workflows.

Author: Senior Lead, AutoAudit
"""

import docker
import logging

class ContainerRuntimeManager:
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
    
        try:
            self._client = docker.from_env()
            self._logger.info("The docker client is initialised")
    
        except Exception as e:
            self._logger.error(f"Failed to initialise the Docker client: {e}")
            raise

    def run_container(self, image: str, name: str = None, command: list = None, environment: dict = None, detach: bool = True):
        """
        Run a container.

        :param image: Docker image name.
        :param name: Container name.
        :param command: Command to run in the container.
        :param environment: Environment variables.
        :param detach: Run container in detached mode.
        :return: Container object.
        """
        
        try:
            container = self._client.containers.run(
                image = image,
                name = name,
                command = command,
                environment = environment,
                detach = detach
            )

            self._logger.info(f"Container '{name or container.id}' started with image '{image}'")
            return container
        
        except Exception as e:
            self._logger.error(f"Failed to run container with image '{image}': {e}")
            raise

    def stop_container(self, container_id: str):
        """
        Stop a running container.

        :param container_id: Container ID or name.
        """
        
        try:
            container = self._client.containers.get(container_id)
            container.stop()
            self._logger.info(f"Container '{container_id}' stopped")
        
        except Exception as e:
            self._logger.error(f"Failed to stop container '{container_id}': {e}")
            raise

    def remove_container(self, container_id: str, force: bool = False):
        """
        Remove a container.

        :param container_id: Container ID or name.
        :param force: Force removal.
        """
        
        try:
            container = self._client.containers.get(container_id)
            container.remove(force = force)
            self._logger.info(f"Container '{container_id}' removed")
        
        except Exception as e:
            self._logger.error(f"Failed to remove container '{container_id}': {e}")
            raise

    def list_containers(self, all_containers: bool = False):
        """
        List containers.

        :param all_containers: Include stopped containers if True.
        :return: List of container objects.
        """
        
        try:
            containers = self._client.containers.list(all = all_containers)
            self._logger.info(f"Listed containers (all = {all_containers}): {[c.id for c in containers]}")
            return containers
        
        except Exception as e:
            self._logger.error(f"Failed to list containers: {e}")
            raise
