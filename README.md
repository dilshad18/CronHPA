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

## The code is organized as follows:

- **Importing the required modules:** The necessary modules for interacting with Kubernetes, managing cron schedules, and using the Kopf framework are imported.

- **Defining the hpascaler_daemon function:** This function serves as the entry point for the operator. It runs as a daemon and handles the scaling operations based on the specified schedules in the 
  Custom Resource (CR) object.

- **The run_background_jobs function:** This function is called by the hpascaler_daemon function and contains the main logic for scheduling the scaling operations. It runs in an infinite loop, checking 
  the current time against the cron schedules and performing the appropriate scaling action.

- **The schedule_scale_up and schedule_scale_down functions:** These functions handle scaling up and scaling down the specified HPA by updating the minReplicas and maxReplicas fields.

- **The hpascaler_update function:** This function is triggered when the CR object is updated. It checks if the scheduleStart or scheduleEnd fields have changed and performs the necessary updates to the 
  scaling schedules.

- **The hpascaler_delete function:** This function is triggered when the CR object is deleted. It clears any scheduled timers associated with the CR object.

- **The clear_timers function:** This function is called by hpascaler_delete to clear the scheduled timers based on the specified schedules.

- **The main code block:** This block executes the kopf.run() function to start the operator.

