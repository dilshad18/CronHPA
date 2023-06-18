import datetime
import time
from croniter import croniter
from kubernetes import client, config
import kopf

# Load the Kubernetes config from the default location.
config.load_kube_config(config_file="~/.kube/config")
# config.load_incluster_config()


@kopf.daemon("example.com", "v1", "hpascaler")
async def hpascaler_daemon(body, **kwargs):
    namespace = body["spec"]["namespace"]
    hpa_name = body["spec"]["hpaName"]
    schedule_start = body["spec"]["scheduleStart"]["cronExpression"]
    schedule_end = body["spec"]["scheduleEnd"]["cronExpression"]
    min_replicas_start = body["spec"]["scheduleStart"]["minReplicas"]
    max_replicas_start = body["spec"]["scheduleStart"]["maxReplicas"]
    min_replicas_end = body["spec"]["scheduleEnd"]["minReplicas"]
    max_replicas_end = body["spec"]["scheduleEnd"]["maxReplicas"]

    run_background_jobs(
        namespace,
        hpa_name,
        schedule_start,
        schedule_end,
        min_replicas_start,
        max_replicas_start,
        min_replicas_end,
        max_replicas_end,
    )


def run_background_jobs(
    namespace,
    hpa_name,
    schedule_start,
    schedule_end,
    min_replicas_start,
    max_replicas_start,
    min_replicas_end,
    max_replicas_end,
):
        
    while True:
        current_time = datetime.datetime.now()

        start_cron = croniter(schedule_start)
        end_cron = croniter(schedule_end)

        next_start_time = start_cron.get_next(datetime.datetime)
        next_end_time = end_cron.get_next(datetime.datetime)

        if current_time >= next_start_time and current_time < next_end_time:
            schedule_scale_up(namespace, hpa_name, min_replicas_start, max_replicas_start)
        else:
            schedule_scale_down(namespace, hpa_name, min_replicas_end, max_replicas_end)

        # Wait for a specific duration before checking the time again
        time.sleep(60)  # Adjust the duration as needed
    
        # Sleep until the next cron time
        sleep_time = min(next_start_time, next_end_time) - datetime.datetime.now()
        sleep_seconds = sleep_time.total_seconds()
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)


def schedule_scale_up(namespace, hpa_name, min_replicas, max_replicas):
    # Scale the HPA up.
    api = client.AutoscalingV2Api()
    api.patch_namespaced_horizontal_pod_autoscaler(
        name=hpa_name,
        namespace=namespace,
        body={"spec": {"minReplicas": min_replicas, "maxReplicas": max_replicas}},
    )

    # Log the event.
    kopf.event(
        type='ScalingUpScheduled',
        reason="ScalingUp",
        message=f"Scheduled scaling up for {hpa_name} at {datetime.datetime.now()}",
        objs={},
    )


def schedule_scale_down(namespace, hpa_name, min_replicas, max_replicas):
    # Scale the HPA down.
    api = client.AutoscalingV2Api()
    api.patch_namespaced_horizontal_pod_autoscaler(
        name=hpa_name,
        namespace=namespace,
        body={"spec": {"minReplicas": min_replicas, "maxReplicas": max_replicas}},
    )

    # Log the event.
    kopf.event(
        type='ScalingDownScheduled',
        reason="ScalingDown",
        message=f"Scheduled scaling down for {hpa_name} at {datetime.datetime.now()}",
        objs={},
    )


@kopf.on.update("example.com", "v1", "hpascaler")
def hpascaler_update(body, **kwargs):
    start_changed = kopf.diff(body, previous=None).get("spec", {}).get("scheduleStart")
    stop_changed = kopf.diff(body, previous=None).get("spec", {}).get("scheduleEnd")

    if start_changed:
        # Handle update logic for 'scheduleStart' field
        schedule_start = body["spec"]["scheduleStart"]["cronExpression"]
        min_replicas_start = body["spec"]["scheduleStart"]["minReplicas"]
        max_replicas_start = body["spec"]["scheduleStart"]["maxReplicas"]

        # Update the schedule for scaling up
        schedule_scale_up(
            body["spec"]["namespace"],
            body["spec"]["hpaName"],
            min_replicas_start,
            max_replicas_start,
        )

    if stop_changed:
        # Handle update logic for 'scheduleEnd' field
        schedule_end = body["spec"]["scheduleEnd"]["cronExpression"]
        min_replicas_end = body["spec"]["scheduleEnd"]["minReplicas"]
        max_replicas_end = body["spec"]["scheduleEnd"]["maxReplicas"]

        # Update the schedule for scaling down
        schedule_scale_down(
            body["spec"]["namespace"],
            body["spec"]["hpaName"],
            min_replicas_end,
            max_replicas_end,
        )


@kopf.on.delete("example.com", "v1", "hpascaler")
def hpascaler_delete(body, **kwargs):
    # Clear all the scheduled timers.
    schedule_start = body['spec']['scheduleStart']
    schedule_end = body['spec']['scheduleEnd']
    clear_timers(namespace=body['metadata']['namespace'], schedule_start=schedule_start, schedule_end=schedule_end)


def clear_timers(namespace: str, schedule_start: dict, schedule_end: dict):
    kopf.timer(schedule_start['cronExpression'], name='hpascaler', labels={'managed-by': 'hpascaler'}, idle=None, deleted=True)
    kopf.timer(schedule_end['cronExpression'], name='hpascaler', labels={'managed-by': 'hpascaler'}, idle=None, deleted=True)


if __name__ == "__main__":
    kopf.run()
