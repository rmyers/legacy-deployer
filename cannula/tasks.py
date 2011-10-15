from celery.decorators import task

from cannula.conf import api

@task()
def add(x, y):
    import time
    time.sleep(5)
    return x + y

def blah(x, y):
    return x + y

@task()
def deploy_project(group, project, cluster):
    # grab the latest deployment
    deployment = api.deployments.get(group, project, cluster)
    deployment.deploy_project()