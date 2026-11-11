"""Choose one reproducible morning slot per local date without idle runners."""

from datetime import datetime, timedelta, timezone
import hashlib
import os

LOCAL_TZ = timezone(timedelta(hours=8))
SCHEDULES = tuple(f'{minute} {hour} * * *' for hour in (1, 2, 3) for minute in (7, 22, 37, 52))


def selected_schedule(day, repository):
    # Reproducible pseudo-random selection: separate invocations agree on one slot.
    seed = f'{repository}:{day.isoformat()}:morning-v1'.encode('utf-8')
    index = int.from_bytes(hashlib.sha256(seed).digest()[:8], 'big') % len(SCHEDULES)
    return SCHEDULES[index]


def should_run(event_name, event_schedule, now, repository):
    if event_name == 'workflow_dispatch':
        return True
    if event_name != 'schedule':
        return False
    local = now.astimezone(LOCAL_TZ)
    if not 9 <= local.hour < 12:
        return False
    return event_schedule == selected_schedule(local.date(), repository)


def main():
    now = datetime.now(LOCAL_TZ)
    repository = os.environ['GITHUB_REPOSITORY']
    event_name = os.environ['GITHUB_EVENT_NAME']
    run = should_run(event_name, os.environ.get('EVENT_SCHEDULE', ''), now, repository)
    if event_name == 'schedule':
        minute, hour, *_ = selected_schedule(now.date(), repository).split()
        print(f'Today selected {int(hour) + 8:02d}:{int(minute):02d} UTC+8; run={run}')
    else:
        print(f'Manual run: bypass morning selection; run={run}')
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        output.write(f'run={str(run).lower()}\n')


if __name__ == '__main__':
    main()
