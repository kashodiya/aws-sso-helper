#!/usr/bin/env python3
"""
AWS SSO Helper - Automates AWS SSO login and profile management
"""

import subprocess
import json
import os
import boto3
import configparser
import sys
from pathlib import Path
from typing import List, Tuple, Optional


class AWSConfig:
    """Configuration manager for AWS SSO settings"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")
        self.config.read(self.config_file)
    
    @property
    def sso_profile(self) -> str:
        return self.config.get('aws', 'sso_profile')
    
    @property
    def sso_start_url(self) -> str:
        return self.config.get('aws', 'sso_start_url')
    
    @property
    def sso_region(self) -> str:
        return self.config.get('aws', 'sso_region')
    
    @property
    def default_region(self) -> str:
        return self.config.get('aws', 'default_region')
    
    @property
    def output_format(self) -> str:
        return self.config.get('aws', 'output_format')
    
    @property
    def aws_folder_name(self) -> str:
        return self.config.get('paths', 'aws_folder_name')
    
    @property
    def config_file_name(self) -> str:
        return self.config.get('paths', 'config_file')
    
    @property
    def credentials_file_name(self) -> str:
        return self.config.get('paths', 'credentials_file')
    
    @property
    def sso_cache_folder(self) -> str:
        return self.config.get('paths', 'sso_cache_folder')


class AWSPathManager:
    """Manages AWS file paths and directories"""
    
    def __init__(self, aws_config: AWSConfig):
        self.config = aws_config
        self._aws_folder = self._find_aws_folder()
    
    def _find_aws_folder(self) -> Path:
        """Find the AWS configuration folder"""
        home_dir = Path.home()
        aws_folder = home_dir / self.config.aws_folder_name
        
        if not aws_folder.exists():
            aws_folder.mkdir(parents=True, exist_ok=True)
        
        return aws_folder
    
    @property
    def aws_folder(self) -> Path:
        return self._aws_folder
    
    @property
    def config_file(self) -> Path:
        return self._aws_folder / self.config.config_file_name
    
    @property
    def credentials_file(self) -> Path:
        return self._aws_folder / self.config.credentials_file_name
    
    @property
    def sso_cache_dir(self) -> Path:
        return self._aws_folder / self.config.sso_cache_folder


class SSOTokenManager:
    """Manages SSO token retrieval and caching"""
    
    def __init__(self, path_manager: AWSPathManager):
        self.path_manager = path_manager
    
    def get_latest_access_token(self) -> str:
        """Retrieve the latest SSO access token from cache"""
        cache_dir = self.path_manager.sso_cache_dir
        
        if not cache_dir.exists():
            raise FileNotFoundError(f"SSO cache directory not found: {cache_dir}")
        
        cache_files = [f for f in cache_dir.iterdir() if f.suffix == '.json']
        
        if not cache_files:
            raise FileNotFoundError("No SSO cache files found")
        
        latest_cache = max(cache_files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_cache, 'r') as f:
            cached_data = json.load(f)
        
        return cached_data['accessToken']


class AWSProfileManager:
    """Manages AWS CLI profiles"""
    
    def __init__(self, aws_config: AWSConfig, path_manager: AWSPathManager):
        self.aws_config = aws_config
        self.path_manager = path_manager
    
    def update_profile(self, credentials: dict, account_id: str, role_name: str, profile_name: str):
        """Update AWS CLI config and credentials files"""
        self._update_config_file(profile_name)
        self._update_credentials_file(credentials, profile_name)
        print(f"Updated profile: {profile_name}")
    
    def _update_config_file(self, profile_name: str):
        """Update the AWS config file"""
        config = configparser.ConfigParser()
        config_file = self.path_manager.config_file
        
        if config_file.exists():
            config.read(config_file)
        
        config[f"profile {profile_name}"] = {
            "region": self.aws_config.default_region,
            "output": self.aws_config.output_format,
            "sso_start_url": self.aws_config.sso_start_url,
            "sso_region": self.aws_config.sso_region
        }
        
        with open(config_file, 'w') as f:
            config.write(f)
        
        print(f"Updated config file: {config_file}")
    
    def _update_credentials_file(self, credentials: dict, profile_name: str):
        """Update the AWS credentials file"""
        config = configparser.ConfigParser()
        credentials_file = self.path_manager.credentials_file
        
        if credentials_file.exists():
            config.read(credentials_file)
        
        config[profile_name] = {
            "aws_access_key_id": credentials['accessKeyId'],
            "aws_secret_access_key": credentials['secretAccessKey'],
            "aws_session_token": credentials['sessionToken']
        }
        
        with open(credentials_file, 'w') as f:
            config.write(f)
        
        print(f"Updated credentials file: {credentials_file}")


class AWSSSOManager:
    """Main AWS SSO management class"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.aws_config = AWSConfig(config_file)
        self.path_manager = AWSPathManager(self.aws_config)
        self.token_manager = SSOTokenManager(self.path_manager)
        self.profile_manager = AWSProfileManager(self.aws_config, self.path_manager)
    
    def login(self):
        """Perform AWS SSO login"""
        print("Initiating AWS SSO login. Please complete the login process in your browser.")
        try:
            subprocess.run(
                ["aws", "sso", "login", "--profile", self.aws_config.sso_profile], 
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AWS SSO login failed: {e}")
    
    def get_available_roles(self) -> List[Tuple[str, str]]:
        """Get all available roles from SSO"""
        access_token = self.token_manager.get_latest_access_token()
        sso = boto3.client('sso', region_name=self.aws_config.sso_region)
        
        accounts = sso.list_accounts(accessToken=access_token)
        available_roles = []
        
        for account in accounts['accountList']:
            roles = sso.list_account_roles(
                accessToken=access_token,
                accountId=account['accountId']
            )
            
            for role in roles['roleList']:
                available_roles.append((account['accountId'], role['roleName']))
        
        return available_roles
    
    def setup_profiles(self, available_roles: List[Tuple[str, str]]) -> List[str]:
        """Set up AWS CLI profiles for all available roles"""
        access_token = self.token_manager.get_latest_access_token()
        sso = boto3.client('sso', region_name=self.aws_config.sso_region)
        
        profile_names = []
        
        for account_id, role_name in available_roles:
            try:
                credentials = sso.get_role_credentials(
                    roleName=role_name,
                    accountId=account_id,
                    accessToken=access_token
                )['roleCredentials']
                
                if credentials:
                    print(f"Got credentials for Account ID: {account_id}, Role: {role_name}")
                    profile_name = f"sso-{account_id}-{role_name}"
                    profile_names.append(profile_name)
                    self.profile_manager.update_profile(credentials, account_id, role_name, profile_name)
            
            except Exception as e:
                print(f"Failed to get credentials for {account_id}/{role_name}: {e}")
        
        return profile_names
    
    def display_console_urls(self, available_roles: List[Tuple[str, str]]):
        """Display direct console URLs"""
        print("\nDirect URLs to the console:")
        print()
        for account_id, role_name in available_roles:
            url = f"{self.aws_config.sso_start_url}/#/console?account_id={account_id}&role_name={role_name}"
            print(url)
    
    def display_profile_commands(self, profile_names: List[str]):
        """Display commands to set AWS profiles"""
        print("\nCut paste one of following to set profile:")
        print()
        for profile_name in profile_names:
            print(f"set AWS_DEFAULT_PROFILE={profile_name}")
    
    def run(self):
        """Main execution method"""
        try:
            self.login()
            available_roles = self.get_available_roles()
            profile_names = self.setup_profiles(available_roles)
            
            self.display_console_urls(available_roles)
            self.display_profile_commands(profile_names)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.ini"
    
    sso_manager = AWSSSOManager(config_file)
    sso_manager.run()


if __name__ == "__main__":
    main()