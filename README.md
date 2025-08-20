# AWS SSO Helper

A Python tool that automates AWS Single Sign-On (SSO) login and manages AWS CLI profiles for multiple accounts and roles.

**🎯 Main Benefit**: No more manual editing of `.aws/config` and `.aws/credentials` files! This tool automatically handles all the complex SSO credential management so you don't have to mess with AWS configuration files.

## Overview

AWS SSO Helper streamlines the process of:
- Logging into AWS SSO
- Retrieving credentials for all available accounts and roles
- Setting up AWS CLI profiles automatically
- Providing direct console URLs for easy access

## Features

- 🔐 **Automated SSO Login**: Handles the AWS SSO login process
- 📋 **Multi-Account Support**: Works with multiple AWS accounts and roles
- ⚙️ **Profile Management**: Automatically creates and updates AWS CLI profiles
- 🌐 **Console URLs**: Generates direct links to AWS console for each account/role
- 🔧 **Configurable**: All settings externalized to configuration file
- 📁 **Cross-Platform**: Works on Windows, macOS, and Linux

## Prerequisites

1. **AWS CLI v2**: Install from [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
2. **Python 3.7+**: Download from [python.org](https://www.python.org/downloads/)
3. **Python Dependencies**: Install via requirements.txt (see Installation section)
4. **AWS SSO Configuration**: Your AWS SSO must be configured in `~/.aws/config`

## Initial AWS SSO Setup

Before using this tool, ensure you have AWS SSO configured in your `~/.aws/config` file:

```ini
[profile sso_profile]
sso_start_url = https://your-sso-portal.awsapps.com/start
sso_region = us-east-1
region = us-east-1
output = json
```

Replace `https://your-sso-portal.awsapps.com/start` with your organization's SSO start URL.

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd aws-sso-helper
```

2. **Create a virtual environment (recommended)**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure the tool**:

**Windows:**
```cmd
copy config.ini.example config.ini
```

**Linux/macOS:**
```bash
cp config.ini.example config.ini
```

Then edit `config.ini` to match your AWS SSO setup

## Configuration

The repository includes a `config.ini.example` file with sample configuration. Copy this file to create your own configuration:

**Windows:**
```cmd
copy config.ini.example config.ini
```

**Linux/macOS:**
```bash
cp config.ini.example config.ini
```

**Important**: The `config.ini` file contains sensitive information and is excluded from version control. Always use the example file as a template.

Modify the `config.ini` file to match your AWS SSO setup:

```ini
[aws]
sso_profile = sso_profile
sso_start_url = https://your-sso-portal.awsapps.com/start
sso_region = us-east-1
default_region = us-east-1
output_format = json

[paths]
aws_folder_name = .aws
config_file = config
credentials_file = credentials
sso_cache_folder = sso/cache
```

### Configuration Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `sso_profile` | Profile name in your AWS config | `sso_profile` |
| `sso_start_url` | Your organization's SSO start URL | `https://company.awsapps.com/start` |
| `sso_region` | AWS region for SSO | `us-east-1` |
| `default_region` | Default AWS region for profiles | `us-east-1` |
| `output_format` | AWS CLI output format | `json` |

## Usage

### Basic Usage

Run the tool with default configuration:
```bash
python aws_sso_helper.py
```

### Custom Configuration

Use a custom configuration file:
```bash
python aws_sso_helper.py my_custom_config.ini
```

### Typical Workflow

1. **Run the tool**:
   ```bash
   python aws_sso_helper.py
   ```

2. **Complete SSO login**: A browser window will open for you to authenticate

3. **Review output**: The tool will display:
   - Progress of credential retrieval
   - Direct console URLs for each account/role
   - Commands to set AWS profiles

4. **Choose and set your profile**:
   
   **For Multiple Accounts**: The tool will display all available accounts and roles. Choose the appropriate profile for your current task:
   ```cmd
   set AWS_DEFAULT_PROFILE=sso-123456789012-AWSAdministratorAccess
   ```
   
   **For Single Account**: If you only have access to one account, simply use the provided command:
   ```cmd
   set AWS_DEFAULT_PROFILE=sso-123456789012-PowerUserAccess
   ```

5. **Verify your setup**:
   ```bash
   aws sts get-caller-identity
   ```
   This should display your current AWS account and role information.

## Working with Multiple Accounts

If you have access to multiple AWS accounts (as shown in the example output), you can:

### Switch Between Accounts

**Windows:**
```cmd
# Switch to a specific account
set AWS_DEFAULT_PROFILE=sso-123456789012-AWSAdministratorAccess

# Verify the switch
aws sts get-caller-identity
```

**Linux/macOS:**
```bash
# Switch to a specific account
export AWS_DEFAULT_PROFILE=sso-123456789012-AWSAdministratorAccess

# Verify the switch
aws sts get-caller-identity
```

### Use Profile-Specific Commands

Instead of setting a default profile, you can specify the profile for individual commands:
```bash
aws s3 ls --profile sso-123456789012-AWSAdministratorAccess
aws ec2 describe-instances --profile sso-987654321098-AWSAdministratorAccess
```

### Access AWS Console

Click any of the provided console URLs to directly access the AWS Console for that specific account/role combination.

## How It Works

### Architecture

The tool consists of several components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AWSConfig     │    │  AWSPathManager  │    │SSOTokenManager  │
│                 │    │                  │    │                 │
│ • Configuration │    │ • Path handling  │    │ • Token cache   │
│ • Settings      │    │ • File locations │    │ • SSO tokens    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │  AWSSSOManager      │
                    │                     │
                    │ • Main orchestrator │
                    │ • SSO login         │
                    │ • Profile setup     │
                    └─────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │ AWSProfileManager   │
                    │                     │
                    │ • Profile creation  │
                    │ • Credential mgmt   │
                    └─────────────────────┘
```

### Process Flow

1. **Configuration Loading**: Reads settings from `config.ini`
2. **SSO Login**: Initiates `aws sso login` using configured profile
3. **Token Retrieval**: Extracts access token from SSO cache
4. **Account Discovery**: Lists all accessible AWS accounts
5. **Role Discovery**: Enumerates roles for each account
6. **Credential Retrieval**: Obtains temporary credentials for each role
7. **Profile Creation**: Updates `~/.aws/config` and `~/.aws/credentials`
8. **Output Generation**: Provides console URLs and profile commands

### File Structure

After running, your AWS directory structure will look like:

```
~/.aws/
├── config              # Profile configurations
├── credentials         # Temporary credentials
└── sso/
    └── cache/
        └── *.json     # SSO token cache files
```

### Generated Profiles

The tool creates profiles with the naming convention:
```
sso-{account-id}-{role-name}
```

Examples:
- `sso-123456789012-PowerUserAccess`
- `sso-123456789012-ReadOnlyAccess`
- `sso-987654321098-AdministratorAccess`

## Troubleshooting

### Common Issues

#### 1. SSO Login Fails
```
Error: AWS SSO login failed
```
**Solutions**:
- Verify AWS CLI v2 is installed
- Check your `sso_profile` exists in `~/.aws/config`
- Ensure SSO start URL is correct

#### 2. No Cache Files Found
```
Error: No SSO cache files found
```
**Solutions**:
- Run `aws sso login --profile your-profile` manually first
- Check if `~/.aws/sso/cache/` directory exists
- Verify you completed the browser authentication

#### 3. Configuration File Missing
```
Error: Configuration file config.ini not found
```
**Solutions**:
- Create `config.ini` in the same directory as the script
- Use absolute path: `python aws_sso_helper.py /path/to/config.ini`

#### 4. Permission Denied
```
Error: Permission denied writing to credentials file
```
**Solutions**:
- Check file permissions on `~/.aws/` directory
- Run with appropriate user permissions
- Ensure AWS directory is not read-only

### Debug Mode

For troubleshooting, you can modify the script to add debug output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Validation

Verify your setup works by:

1. **List profiles**:
   ```bash
   aws configure list-profiles
   ```

2. **Test a profile**:
   ```bash
   aws sts get-caller-identity --profile sso-123456789012-PowerUserAccess
   ```

3. **Check profile details**:
   ```bash
   aws configure list --profile sso-123456789012-PowerUserAccess
   ```

## Security Considerations

- **Temporary Credentials**: All credentials are temporary and will expire
- **Local Storage**: Credentials are stored locally in `~/.aws/credentials`
- **Token Cache**: SSO tokens are cached locally by AWS CLI
- **File Permissions**: Ensure proper file permissions on AWS configuration files

## Best Practices

1. **Regular Re-authentication**: Run the tool periodically as SSO sessions expire
2. **Profile Naming**: Use the generated profile names for consistency
3. **Multiple Environments**: Use different config files for different environments
4. **Backup**: Keep a backup of your original AWS configuration files

## Example Output

### Multiple Accounts Scenario
```
Initiating AWS SSO login. Please complete the login process in your browser.
Attempting to automatically open the SSO authorization page in your default browser.
If the browser does not open or you wish to use a different device to authorize this request, open the following URL:

https://your-sso-portal.awsapps.com/start/#/device

Then enter the code:

ABCD-EFGH
Successfully logged into Start URL: https://your-sso-portal.awsapps.com/start
Got credentials for Account ID: 123456789012, Role: AWSAdministratorAccess
Updated profile: sso-123456789012-AWSAdministratorAccess
Got credentials for Account ID: 987654321098, Role: AWSAdministratorAccess
Updated profile: sso-987654321098-AWSAdministratorAccess

Direct URLs to the console:

https://your-sso-portal.awsapps.com/start/#/console?account_id=123456789012&role_name=AWSAdministratorAccess
https://your-sso-portal.awsapps.com/start/#/console?account_id=987654321098&role_name=AWSAdministratorAccess

Cut paste one of following to set profile:

set AWS_DEFAULT_PROFILE=sso-123456789012-AWSAdministratorAccess
set AWS_DEFAULT_PROFILE=sso-987654321098-AWSAdministratorAccess
```

**What to do next:**
1. Choose the account you want to work with
2. Copy and paste the corresponding `set AWS_DEFAULT_PROFILE=...` command
3. Run `aws sts get-caller-identity` to verify you're using the correct account

### Single Account Scenario
If you only have access to one account, you'll see fewer profiles listed, and you can simply use the single provided command to set your profile.

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review AWS SSO documentation
3. Open an issue in the repository
4. Ensure you have the latest version of AWS CLI v2

---

**Note**: This tool requires AWS CLI v2 and will not work with AWS CLI v1. Make sure you have the correct version installed and configured.