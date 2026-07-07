# Repository for REST API test automation course (advanced part)

## Running the tests

```bash
pytest tests
```

Swagger coverage recording is **off by default**, so the suite runs anywhere,
including Windows.

## Swagger coverage report

Generating the report has two requirements that Windows does not satisfy:

- A **Java runtime** — the swagger-coverage report generator is a Java CLI.
- A filesystem that allows `:` in paths — recorded requests are written to
  `swagger-coverage-output/<host:port>/`, and `:` is illegal in Windows paths.

For that reason the report is generated inside Docker (Linux) using the
dedicated `Dockerfile-sw-coverage` image. Recording is enabled by the
`--swagger-coverage` pytest flag (see `tests/conftest.py`), which that image
passes automatically.

### Generate the report

Build the coverage image:

```bash
docker build -f Dockerfile-sw-coverage -t dm-api-tests-coverage .
```

Run the suite with coverage enabled, mounting the project so the report is
written back to the host:

```bash
docker run --rm -v "$(pwd)":/app dm-api-tests-coverage
```

> **Git Bash on Windows:** prefix the run command with `MSYS_NO_PATHCONV=1` to
> stop Git Bash from rewriting the container path:
>
> ```bash
> MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app dm-api-tests-coverage
> ```

After the run, open the generated report:

```
swagger-coverage-dm-api-account.html
```

(The report filename comes from `writers.html.filename` in
`swagger-coverage-config-dm-api-reporter.json`.)

### Enabling coverage manually

If you run pytest in a Linux environment yourself (not via the image), enable
recording and report generation with the flag:

```bash
pytest tests --swagger-coverage
```
