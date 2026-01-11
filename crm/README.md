# CRM Celery Setup Guide

This guide explains how to set up Celery with Celery Beat for generating weekly CRM reports.

## Prerequisites

1. Python 3.8+
2. Django 3.2+
3. Redis server

## Installation Steps

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Required packages:
# - celery
# - django-celery-beat
# - redis
# - gql