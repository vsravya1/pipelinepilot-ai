# PipelinePilot AI

PipelinePilot AI is a multi-agent DataOps production support assistant for new and existing data pipelines.

It helps data teams:
- create new pipeline readiness tasks
- investigate production support issues
- run data quality checks
- recommend safe fixes
- create GitLab actions with human approval
- store task and conversation history in MongoDB

## Project Goal

This project is being built for the Google Cloud Rapid Agent Hackathon.

## Track

Fivetran

## Core Integrations

- Gemini / Google Cloud Agent Builder
- Fivetran MCP
- MongoDB MCP
- GitLab
- Flask

## Agent Workflow

1. User creates a task.
2. Supervisor Agent creates a plan.
3. Specialist agents handle new job creation, production support, or data quality.
4. Fivetran is used for pipeline health and sync context.
5. MongoDB stores task history and conversations.
6. GitLab action is created after human approval.

## Status

Work in progress.
