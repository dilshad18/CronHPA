# hpascaler

`hpascaler` is a Kubernetes operator that allows you to schedule scaling actions for Horizontal Pod Autoscalers (HPAs) based on cron expressions. It provides a declarative way to define scaling configurations and automatically adjusts the min/max replicas of HPAs according to the specified schedules.

## Features

- Schedule scaling actions for HPAs based on cron expressions.
- Dynamically adjust the min/max replicas of HPAs.
- Simple declarative configuration.

## Prerequisites

- Python 3.6 or higher.
- Kopf
- Kubernetes 
- Kubernetes cluster with RBAC enabled.
- Access to the Kubernetes cluster (either through `kubectl` or in-cluster configuration).


