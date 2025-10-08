"""
Configuration Loader

Loads configuration files and validates them against a schema.

Author: Senior Lead, AutoAudit
"""

import json
import yaml
import logging
from jsonschema import validate, ValidationError
from .schema import CONFIG_SCHEMA

class ConfigLoader:
    def __init__(self, config_path: str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config_path = config_path
        self._config = None

    def load(self):
        """
        Load and validate the configuration file.

        :return: Configuration dictionary.
        """
        
        try:
            
            with open(self._config_path, 'r') as f:
                
                if self._config_path.endswith('.json'):
                    self._config = json.load(f)
                
                elif self._config_path.endswith(('.yaml', '.yml')):
                    self._config = yaml.safe_load(f)
                
                else:
                    raise ValueError("Unsupported config file format")
            
            validate(instance=self._config, schema=CONFIG_SCHEMA)
            self._logger.info(f"Configuration loaded and validated from {self._config_path}")
            return self._config
        
        except (IOError, ValueError, ValidationError) as e:
            self._logger.error(f"Failed to load or validate configuration: {e}")
            raise
