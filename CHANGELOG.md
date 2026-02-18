# Changelog

All notable changes to the NWU Protocol project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Business Cooperation Lead Agent System** - Autonomous AI system that manages business operations 24/7 through 12 specialized agent types
  - Autonomous Business Cooperation Lead Agent for task analysis and delegation
  - Dynamic agent creation system with configurable capacity limits
  - Priority-based task queue with 10 priority levels
  - 12 specialized agent types: Sales, Marketing, Operations, Finance, Customer Service, Research, Development, QA, HR, Legal, Strategy, and Project Management
  - Backend integration with database models (BusinessAgent, BusinessTask)
  - REST API endpoints for agent and task management
  - Docker deployment configuration with environment-based controls
  - Comprehensive documentation (BUSINESS_AGENT_GUIDE.md, agent-business-lead/README.md)
  - System validation script (validate_business_agents.sh)
  - RabbitMQ integration for task submission

## Project History

This changelog was created on 2026-02-18. For changes prior to this date, please refer to the git commit history.
