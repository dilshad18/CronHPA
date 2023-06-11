import datetime
from typing import Tuple

import kopf
from kubernetes import client, config


# Load the Kubernetes config from the default location.
config.load_incluster_config()


@kopf.on.create('example.com', 'v1', 'hpascaler')
def create_handler(body, **kwargs):
    namespace = body['spec']['namespace']
    hpa_name = body['spec']['hpaName']
    cron_start = body['spec']['cronStart']
    cron_end = body['spec']['cronEnd']
    min_replicas_start = int(cron_start['minReplicas'])
    max_replicas_start = int(cron_start['maxReplicas'])
    min_replicas_end = int(cron_end['minReplicas'])
    max_replicas_end = int(cron_end['maxReplicas'])
    
    @kopf.timer(cron_start['cronExpression'], labels={'managed-by': 'hpascaler'})
    def scheduled_scale_up(namespace, hpa_name, min_replicas, max_replicas):
        # Scale the HPA up.
        api = client.AutoscalingV1Api()
        hpa = api.read_namespaced_horizontal_pod_autoscaler(name=hpa_name, namespace=namespace)
        hpa.spec.min_replicas = min_replicas
        hpa.spec.max_replicas = max_replicas
        hpa.spec.desired_replicas = max_replicas
        api.patch_namespaced_horizontal_pod_autoscaler(name=hpa_name, namespace=namespace, body=hpa)

        # Log the event.
        kopf.event(body, type='ScalingUpScheduled', reason='ScalingUp', message=f'Scheduled scaling up for {hpa_name} at {cron_start["cronExpression"]}.')

    @kopf.timer(cron_end['cronExpression'], labels={'managed-by': 'hpascaler'})
    def scheduled_scale_down(namespace, hpa_name, min_replicas, max_replicas):
        # Scale the HPA down.
        api = client.AutoscalingV1Api()
        hpa = api.read_namespaced_horizontal_pod_autoscaler(name=hpa_name, namespace=namespace)
        hpa.spec.min_replicas = min_replicas
        hpa.spec.max_replicas = max_replicas
        hpa.spec.desired_replicas = min_replicas
        api.patch_namespaced_horizontal_pod_autoscaler(name=hpa_name, namespace=namespace, body=hpa)

        # Log the event.
        kopf.event(body, type='ScalingDownScheduled', reason='ScalingDown', message=f'Scheduled scaling down for {hpa_name} at {cron_end["cronExpression"]}.')

    # Log the event.
    kopf.event(body, type='Initialization', reason='Initialization', message=f'Scaling configuration added for {hpa_name}.')
    return {'status': {'initialized': True}}


@kopf.on.delete('example.com', 'v1', 'hpascaler')
def delete_handler(body, **kwargs):
    # Clear all the scheduled timers.
    cron_start = body['spec']['cronStart']
    cron_end = body['spec']['cronEnd']
    clear_timers(namespace=body['metadata']['namespace'], cron_start=cron_start, cron_end=cron_end)

    # Log the event.
    kopf.event(body, type='Finalization', reason='Finalization', message='Scaling configuration removed.')
    return {'status': {'initialized': False}}


def clear_timers(namespace: str, cron_start: dict, cron_end: dict):
    kopf.timer(cron_start['cronExpression'], name='hpascaler', labels={'managed-by': 'hpascaler'}, idle=None, deleted=True)
    kopf.timer(cron_end['cronExpression'], name='hpascaler', labels={'managed-by': 'hpascaler'}, idle=None, deleted=True)
