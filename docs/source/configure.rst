Configure Applications
======================

Applications define basic routing and runtime setup in a yaml file located
in the projects root directory. Multiple handlers can be used in a project
which will spawn separate processes to handle each. The syntax is pretty
loose allowing you to create your own custom settings to define. This file
also can be used to setup cron jobs and run daemons in the user space such
as memcached.

app.yaml file
-------------

Sample app.yaml file::

    # optional domain to listen on
    domain: localhost:8000
    # optional version string
    version: 1.0
    # runtime (ruby, python, php, java)
    runtime: cannula.runtime.Python
    api_version: 1
    
    # setup some defaults to pass to handlers
    gunicorn_defaults: 
      workers: 2
      worker-class: sync
      worker-connections: 1000
      max_requests: 0
      timeout: 30
      keepalive: 2
      
    # Main wsgi handlers and static file definitions
    # Each unique 'worker' handler will setup a separate process
    handlers:
    # static files (less greedy urls should come first!)
    - url: /static
      static_dir: static
    
    # Main site handler will match everything else
    - url: /
      worker: cannula.worker.gunicorn_django
      settings: settings
      defaults: gunicorn_defaults
    
    # Cron Jobs
    cron:
    # run a simple bash script
    - task: bash mycron.sh
      schedule: */5 * * * *
    # run the task with the virtual env setup by the runtime
    # only python support so far
    - task: python mycron.py
      schedule: 0 2 * * *