# Terraform & Docker Provisioning Module

## Overview

This module generates Infrastructure-as-Code (IaC) templates for the Self-Service Provisioner Bot.

Based on the environment type requested by the developer, the module generates either a Docker Compose template or a Terraform configuration file.

## Supported Environments

- Docker
- AWS (Terraform)

## Module Structure

terraform_generator/
│
├── templates/
│   ├── docker.tpl
│   └── aws.tpl
│
├── generator.py
└── README.md

## Team Role

Member 3 - Terraform/Docker Lead

Responsibilities:
- Docker template generation
- Terraform template generation
- Infrastructure as Code (IaC)
- Environment provisioning support
### Sample Execution

Input:
docker
dev

Output:
Docker Compose template generated successfully.