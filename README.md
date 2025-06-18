With `libmamba < 2.1.0`, upsert-kernel-env.py successfully detects
when the environment already matches the conda-lock.yml as expected,
i.e. the following succeeds:

```
podman build --format=docker -t repro:dev . && podman run --rm -it localhost/repro:dev
```

If you open the `Dockerfile`, then uncomment out the libmamba upgrade:
```
RUN conda install libmamba=2.3.0
```
and re-run the command above, it will fail.
