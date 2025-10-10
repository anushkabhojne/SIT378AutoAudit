"""
Trivy Vulnerability Scanner Integration Module

This module provides comprehensive integration with Aqua Security's Trivy scanner,
implementing subprocess management, output parsing, database updates, caching
optimisation, and error handling for enterprise-grade vulnerability detection.

The implementation supports multiple scanning modes, various output formats, and
advanced configuration options while maintaining high performance and reliability
for CI/CD pipeline integration.

Author: Senior Lead, AutoAudit
"""

import subprocess
import json
import os
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import tempfile
import shutil

from utils.logger import get_logger
from utils.config import get_config, ScanningProfile

from utils.exceptions import (
    ScannerExecutionError,
    ScannerTimeoutError,
    ScannerNotFoundError,
    DatabaseUpdateError,
    InvalidImageError
)


logger = get_logger(__name__)


@dataclass
class ScanResult:
    """
    Comprehensive data structure for Trivy scan results.
    
    This class encapsulates all vulnerability data, metadata, and context
    information from a Trivy scanning operation.
    """
    
    #Scanning the identification and metadata
    scan_id: str
    image_name: str
    image_digest: str
    scan_timestamp: datetime
    scanner_version: str
    
    #Vulnerability findings
    vulnerabilities: List[Dict[str, Any]] = field(default_factory = list)
    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    unknown_count: int = 0
    
    #Secret detection results
    secrets: List[Dict[str, Any]] = field(default_factory = list)
    secret_count: int = 0
    
    #Misconfiguration findings
    misconfigurations: List[Dict[str, Any]] = field(default_factory = list)
    misconfiguration_count: int = 0
    
    #Performance metrics
    scan_duration_seconds: float = 0.0
    database_version: Optional[str] = None
    
    #Error information
    scan_errors: List[str] = field(default_factory = list)
    warnings: List[str] = field(default_factory = list)
    
    #Additional metadata
    operating_system: Optional[str] = None
    architecture: Optional[str] = None
    packages: List[Dict[str, Any]] = field(default_factory = list)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converting the scan's result to the dictionary format for serialisation.
        
        Returns:
            Dict[str, Any]: Complete scan result as dictionary
        """
        
        return {
            'scan_id': self.scan_id,
            'image_name': self.image_name,
            'image_digest': self.image_digest,
            'scan_timestamp': self.scan_timestamp.isoformat(),
            'scanner_version': self.scanner_version,
            
            'summary': {
                'total_vulnerabilities': self.total_vulnerabilities,
                'critical': self.critical_count,
                'high': self.high_count,
                'medium': self.medium_count,
                'low': self.low_count,
                'unknown': self.unknown_count,
                'secrets': self.secret_count,
                'misconfigurations': self.misconfiguration_count
            },

            'vulnerabilities': self.vulnerabilities,
            'secrets': self.secrets,
            'misconfigurations': self.misconfigurations,
            
            'performance': {
                'scan_duration_seconds': self.scan_duration_seconds,
                'database_version': self.database_version
            },

            'metadata': {
                'operating_system': self.operating_system,
                'architecture': self.architecture,
                'packages': self.packages
            },

            'errors': self.scan_errors,
            'warnings': self.warnings
        }


class TrivyScanner:
    """
    Enterprise-grade Trivy scanner integration with advanced features.
    
    This class provides comprehensive vulnerability scanning capabilities with
    support for caching, parallel execution, database management, and extensive
    error handling suitable for production CI/CD pipelines.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialising the Trivy scanner with configuration.
        
        Args:
            config: Optional configuration manager instance (uses global if None)
        """

        self.config = config or get_config()
        self.scanner_config = self.config.scanner
        
        #Validating the scanner binary exists
        self._validate_scanner_installation()
        
        #Initialising the cache directory
        self.cache_dir = Path(os.environ.get('TRIVY_CACHE_DIR', '/tmp/trivy-cache'))
        self.cache_dir.mkdir(parents = True, exist_ok = True)
        
        #Initialising the metrics
        self.scan_count = 0
        self.total_scan_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        
        logger.info(
            "TrivyScanner initialised successfully",
            
            extra = {'custom_fields': {
                'scanner_path': self.scanner_config.scanner_binary_path,
                'cache_dir': str(self.cache_dir),
                'cache_enabled': self.scanner_config.cache_enabled
            }}
        )
    
    def _validate_scanner_installation(self) -> None:
        """
        Validating the Trivy scanner installation and version.
        
        Raises:
            ScannerNotFoundError: If scanner binary is not found or not executable
        """
        
        scanner_path = Path(self.scanner_config.scanner_binary_path)
        
        if not scanner_path.exists():
            
            raise ScannerNotFoundError(
                f"Trivy scanner not found at {scanner_path}. "
                "Please install Trivy: https://aquasecurity.github.io/trivy/"
            )
        
        if not os.access(scanner_path, os.X_OK):
            
            raise ScannerNotFoundError(
                f"Trivy scanner at {scanner_path} is not executable"
            )
        
        #Verifying the scanner's version
        try:
            result = subprocess.run(
                [str(scanner_path), '--version'],
                capture_output = True,
                text = True,
                timeout = 10
            )

            version_output = result.stdout.strip()
            logger.info(f"Trivy scanner validation successful: {version_output}")

        except subprocess.TimeoutExpired:
            raise ScannerNotFoundError("Trivy scanner version check timed out")
        
        except Exception as e:
            raise ScannerNotFoundError(f"Failed to validate Trivy installation: {str(e)}")
    
    def scan_image(
        self,
        image_name: str,
        image_tag: str = 'latest',
        scan_id: Optional[str] = None,
        use_cache: Optional[bool] = None
    ) -> ScanResult:
        
        """
        Performing comprehensive vulnerability scan on container image.
        
        This method orchestrates the complete scanning workflow including cache
        checking, scanner execution, output parsing, and result processing.
        
        Args:
            image_name: Container image name (e.g., 'autoaudit/api-service')
            image_tag: Image tag to scan (default: 'latest')
            scan_id: Optional unique identifier for this scan
            use_cache: Override global cache setting for this scan
            
        Returns:
            ScanResult: Comprehensive scan results with vulnerability data
            
        Raises:
            InvalidImageError: If image name is invalid or image cannot be found
            ScannerExecutionError: If scanner execution fails
            ScannerTimeoutError: If scan exceeds timeout threshold
        """
        start_time = time.time()
        
        #Generating a scan ID, if not provided
        if scan_id is None:
            scan_id = self._generate_scan_id(image_name, image_tag)
        
        #Constructing the full image reference
        full_image = f"{image_name}:{image_tag}"
        
        logger.info(
            f"Initiating vulnerability scan for {full_image}",
            
            extra = {'custom_fields': {
                'scan_id': scan_id,
                'image': full_image,
                'scanning_profile': self.scanner_config.scanning_profile.value
            }}
        )
        
        #Checking the cache, if enabled
        use_cache = use_cache if use_cache is not None else self.scanner_config.cache_enabled
        
        if use_cache:
            cached_result = self._check_cache(full_image)
            
            if cached_result:
                logger.info(f"Cache hit for {full_image}, returning cached results")
                self.cache_hits += 1
                return cached_result
            
            self.cache_misses += 1
        
        #Verifying if the image exists and is accessible
        self._verify_image_accessibility(full_image)
        
        #Executing the Trivy scanner
        try:
            raw_output = self._execute_scanner(full_image, scan_id)
            
            #Parsing the scanner's output
            scan_result = self._parse_scanner_output(
                raw_output,
                scan_id,
                full_image,
                start_time
            )
            
            #Caching the result, if enabled
            if use_cache:
                self._cache_result(full_image, scan_result)
            
            #Updating the metrics
            self.scan_count += 1
            scan_duration = time.time() - start_time
            self.total_scan_time += scan_duration
            scan_result.scan_duration_seconds = scan_duration
            
            logger.info(
                f"Scan completed successfully for {full_image}",
                
                extra = {
                    'custom_fields': {
                        'scan_id': scan_id,
                        'duration_seconds': scan_duration,
                        'total_vulnerabilities': scan_result.total_vulnerabilities,
                        'critical_count': scan_result.critical_count,
                        'high_count': scan_result.high_count
                    },

                    'performance_metrics': {
                        'scan_duration': scan_duration,
                        'vulnerabilities_per_second': scan_result.total_vulnerabilities / scan_duration if scan_duration > 0 else 0
                    }
                }
            )
            
            return scan_result
            
        except subprocess.TimeoutExpired:
            error_msg = f"Scanner timeout exceeded ({self.scanner_config.scanner_timeout}s) for {full_image}"
            logger.error(error_msg, extra = {'custom_fields': {'scan_id': scan_id}})
            raise ScannerTimeoutError(error_msg)
        
        except subprocess.CalledProcessError as e:
            error_msg = f"Scanner execution failed for {full_image}: {e.stderr}"
            logger.error(error_msg, extra = {'custom_fields': {'scan_id': scan_id, 'return_code': e.returncode}})
            raise ScannerExecutionError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error during scan of {full_image}: {str(e)}"
            logger.error(error_msg, exc_info = True, extra = {'custom_fields': {'scan_id': scan_id}})
            raise ScannerExecutionError(error_msg)
    
    def _verify_image_accessibility(self, image: str) -> None:
        """
        Verifying if the container image exists and is accessible.
        
        Args:
            image: Full image reference to verify
            
        Raises:
            InvalidImageError: If image cannot be accessed
        """
        try:
            #Using docker inspect to verify the image's accessibility
            result = subprocess.run(
                ['docker', 'inspect', image],
                capture_output = True,
                text = True,
                timeout = 30
            )
            
            if result.returncode != 0:
                
                #Trying pulling the image, if not found locally
                logger.info(f"Image {image} not found locally, attempting pull")
                
                pull_result = subprocess.run(
                    ['docker', 'pull', image],
                    capture_output = True,
                    text = True,
                    timeout = 300
                )
                
                if pull_result.returncode != 0:
                    
                    raise InvalidImageError(
                        f"Failed to pull image {image}: {pull_result.stderr}"
                    )
                    
        except subprocess.TimeoutExpired:
            raise InvalidImageError(f"Timeout while verifying image {image}")
        
        except FileNotFoundError:
            logger.warning("Docker CLI not found, skipping image verification")
    
    def _execute_scanner(self, image: str, scan_id: str) -> Dict[str, Any]:
        """
        Executing the Trivy scanner with the configured parameters.
        
        Args:
            image: Full image reference to scan
            scan_id: Unique scan identifier for logging
            
        Returns:
            Dict[str, Any]: Parsed JSON output from Trivy scanner
            
        Raises:
            subprocess.CalledProcessError: If scanner execution fails
            subprocess.TimeoutExpired: If execution exceeds timeout
        """
        #Constructing the scanner command with all options
        scanner_cmd = self._build_scanner_command(image)
        
        logger.debug(
            f"Executing scanner command for {image}",
            
            extra = {'custom_fields': {
                'scan_id': scan_id,
                'command': ' '.join(scanner_cmd)
            }}
        )
        
        #Executing the scanner with timeout
        result = subprocess.run(
            scanner_cmd,
            capture_output = True,
            text = True,
            timeout = self.scanner_config.scanner_timeout,
            env = self._get_scanner_environment()
        )
        
        #Checking for execution errors
        if result.returncode != 0:
            
            logger.error(
                f"Scanner returned non-zero exit code: {result.returncode}",
                
                extra = {'custom_fields': {
                    'scan_id': scan_id,
                    'stderr': result.stderr,
                    'stdout': result.stdout
                }}
            )
            raise subprocess.CalledProcessError(
                result.returncode,
                scanner_cmd,
                result.stdout,
                result.stderr
            )
        
        #Parsing the JSON output
        try:
            return json.loads(result.stdout)
        
        except json.JSONDecodeError as e:
            
            logger.error(
                f"Failed to parse scanner JSON output: {str(e)}",
                extra={'custom_fields': {
                    'scan_id': scan_id,
                    'output_preview': result.stdout[:500]
                }}
            )

            raise ScannerExecutionError(f"Invalid JSON output from scanner: {str(e)}")
    
    def _build_scanner_command(self, image: str) -> List[str]:
        """
        Building the complete Trivy scanner command with all the configured options.
        
        Args:
            image: Full image reference to scan
            
        Returns:
            List[str]: Complete command line arguments for scanner execution
        """

        cmd = [
            self.scanner_config.scanner_binary_path,
            'image',
            '--format', 'json',
            '--timeout', f'{self.scanner_config.scanner_timeout}s',
        ]
        
        #Adding severity filtering
        if self.scanner_config.severity_threshold != 'UNKNOWN':
            severities = self._get_severity_list()
            cmd.extend(['--severity', ','.join(severities)])
        
        #Adding scanning options based on profile
        if self.scanner_config.scanning_profile == ScanningProfile.FAST:
            cmd.extend(['--scanners', 'vuln'])
        
        elif self.scanner_config.scanning_profile == ScanningProfile.THOROUGH:
            cmd.extend(['--scanners', 'vuln,secret,config'])
            cmd.append('--skip-dirs')
            cmd.append('/usr/share/doc,/usr/share/man')
        
        else:  #BALANCED or COMPLIANCE
            cmd.extend(['--scanners', 'vuln,secret'])
        
        #Adding secret scanning, if enabled
        if self.scanner_config.scan_secrets:
            
            if '--scanners' not in cmd:
                cmd.extend(['--scanners', 'secret'])
        
        #Adding misconfiguration scanning, if enabled
        if self.scanner_config.scan_misconfigurations:
            
            if '--scanners' in cmd:
                scanner_idx = cmd.index('--scanners')
                cmd[scanner_idx + 1] += ',config'
            
            else:
                cmd.extend(['--scanners', 'config'])
        
        #Adding the cache directory
        if self.scanner_config.cache_enabled:
            cmd.extend(['--cache-dir', str(self.cache_dir)])
        
        else:
            cmd.append('--no-progress')
        
        #Adding the vulnerability database path
        cmd.extend(['--cache-dir', self.scanner_config.vulnerability_db_path])
        
        #Adding the registry options
        if self.scanner_config.skip_tls_verify:
            cmd.append('--insecure')
        
        #Adding the image reference
        cmd.append(image)
        
        return cmd
    
    def _get_severity_list(self) -> List[str]:
        """
        Getting a list of severity levels to scan based on threshold.
        
        Returns:
            List[str]: List of severity levels to include in scan
        """
        
        all_severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']
        threshold_index = all_severities.index(self.scanner_config.severity_threshold)
        return all_severities[:threshold_index + 1]
    
    def _get_scanner_environment(self) -> Dict[str, str]:
        """
        Getting the environment variables for the scanner's execution.
        
        Returns:
            Dict[str, str]: Environment variables dictionary
        """
        
        env = os.environ.copy()
        
        #Setting Trivy-specific environment variables
        env['TRIVY_CACHE_DIR'] = str(self.cache_dir)
        env['TRIVY_NO_PROGRESS'] = 'true'
        
        #Setting the timeout
        env['TRIVY_TIMEOUT'] = f'{self.scanner_config.scanner_timeout}s'
        
        #Disabling the unnecessary features for efficient performance
        env['TRIVY_SKIP_FILES'] = '/usr/share/doc/*,/usr/share/man/*'
        
        return env
    
    def _parse_scanner_output(
        self,
        output: Dict[str, Any],
        scan_id: str,
        image: str,
        start_time: float
    ) -> ScanResult:
        
        """
        Parsing the Trivy JSON output into a structured ScanResult.
        
        Args:
            output: Raw JSON output from Trivy scanner
            scan_id: Unique scan identifier
            image: Full image reference
            start_time: Scan start timestamp for duration calculation
            
        Returns:
            ScanResult: Structured scan result object
        """

        #Extracting the metadata
        metadata = output.get('Metadata', {})
        
        #Extracting the results from all targets or layers
        all_vulnerabilities = []
        all_secrets = []
        all_misconfigurations = []
        
        for result in output.get('Results', []):
            
            #Extracting the vulnerabilities
            vulns = result.get('Vulnerabilities', [])
            all_vulnerabilities.extend(vulns)
            
            #Extracting the secrets
            secrets = result.get('Secrets', [])
            all_secrets.extend(secrets)
            
            #Extracting the misconfigurations
            misconfigs = result.get('Misconfigurations', [])
            all_misconfigurations.extend(misconfigs)
        
        #Counting the vulnerabilities by severity
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'UNKNOWN': 0
        }
        
        for vuln in all_vulnerabilities:
            severity = vuln.get('Severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        #Creating the ScanResult object
        scan_result = ScanResult(
            scan_id = scan_id,
            image_name = image.split(':')[0],
            image_digest = metadata.get('ImageID', ''),
            scan_timestamp = datetime.now(),
            scanner_version = self.scanner_config.scanner_version,
            vulnerabilities = all_vulnerabilities,
            total_vulnerabilities = len(all_vulnerabilities),
            critical_count = severity_counts['CRITICAL'],
            high_count = severity_counts['HIGH'],
            medium_count = severity_counts['MEDIUM'],
            low_count = severity_counts['LOW'],
            unknown_count = severity_counts['UNKNOWN'],
            secrets = all_secrets,
            secret_count = len(all_secrets),
            misconfigurations = all_misconfigurations,
            misconfiguration_count = len(all_misconfigurations),
            database_version = metadata.get('Version', ''),
            scan_duration_seconds = time.time() - start_time
        )
        
        return scan_result
    
    def _generate_scan_id(self, image_name: str, image_tag: str) -> str:
        """
        Generating the unique scan identifier.
        
        Args:
            image_name: Container image name
            image_tag: Image tag
            
        Returns:
            str: Unique scan identifier
        """

        timestamp = datetime.now().isoformat()
        content = f"{image_name}:{image_tag}:{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _check_cache(self, image: str) -> Optional[ScanResult]:
        """
        Checking if the cached scan results exist and are valid.
        
        Args:
            image: Full image reference
            
        Returns:
            Optional[ScanResult]: Cached results if valid, None otherwise
        """
        
        cache_file = self.cache_dir / f"{self._get_cache_key(image)}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            #Checking the cache age
            cache_age = time.time() - cache_file.stat().st_mtime
            
            if cache_age > self.scanner_config.cache_ttl:
                logger.debug(f"Cache expired for {image}, age: {cache_age}s")
                cache_file.unlink()
                return None
            
            #Loading the cached result
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            #Reconstructing the ScanResult from cached data
            logger.debug(f"Valid cache found for {image}")
            
            #Placeholder - full reconstruction needed
            return None  
            
        except Exception as e:
            logger.warning(f"Failed to load cache for {image}: {str(e)}")
            return None
    
    def _cache_result(self, image: str, result: ScanResult) -> None:
        """
        Cache scan results for future use.
        
        Args:
            image: Full image reference
            result: Scan result to cache
        """
        
        try:
            cache_file = self.cache_dir / f"{self._get_cache_key(image)}.json"
            
            with open(cache_file, 'w') as f:
                json.dump(result.to_dict(), f, indent = 2)
            
            logger.debug(f"Cached scan result for {image}")
        
        except Exception as e:
            logger.warning(f"Failed to cache result for {image}: {str(e)}")
    
    def _get_cache_key(self, image: str) -> str:
        """
        Generating the cache key from image reference.
        
        Args:
            image: Full image reference
            
        Returns:
            str: Cache key for this image
        """
        
        return hashlib.sha256(image.encode()).hexdigest()
    
    def update_vulnerability_database(self) -> bool:
        """
        Updating the Trivy vulnerability database to the latest version.
        
        Returns:
            bool: True if update successful, False otherwise
            
        Raises:
            DatabaseUpdateError: If database update fails critically
        """
        
        logger.info("Initiating vulnerability database update")
        
        try:
            cmd = [
                self.scanner_config.scanner_binary_path,
                'image',
                '--download-db-only',
                '--cache-dir', self.scanner_config.vulnerability_db_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output = True,
                text = True,
                timeout = 600  #10 minute timeout for database download
            )
            
            if result.returncode == 0:
                logger.info("Vulnerability database updated successfully")
                return True
            
            else:
                logger.error(f"Database update failed: {result.stderr}")
                raise DatabaseUpdateError(f"Failed to update database: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            error_msg = "Database update timed out after 10 minutes"
            logger.error(error_msg)
            raise DatabaseUpdateError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error during database update: {str(e)}"
            logger.error(error_msg, exc_info = True)
            raise DatabaseUpdateError(error_msg)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Getting the scanner performance metrics.
        
        Returns:
            Dict[str, Any]: Performance metrics dictionary
        """
        return {
            'total_scans': self.scan_count,
            'total_scan_time_seconds': self.total_scan_time,
            'average_scan_time_seconds': self.total_scan_time / self.scan_count if self.scan_count > 0 else 0,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }