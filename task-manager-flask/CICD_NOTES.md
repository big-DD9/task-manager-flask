# CI/CD Notes: GitHub Actions

This documents the `.github/workflows/ci.yml` file - what it does, why each
part exists, and what you'll see happen on GitHub once it's pushed.

---

## The big picture

**CI** (Continuous Integration) means: every time code changes, automatically
check that it still works - in our case, running the full test suite.

**CD** (Continuous Deployment/Delivery) means: automatically package up
working code so it's ready to ship - in our case, building a Docker image
and publishing it somewhere it can be pulled from later.

We're doing both here, but stopping short of an actual deployment (that's
Phase 3, once the AWS account situation is sorted) - so think of this as
"CI, plus CD up to the point of having a ready-to-deploy image sitting in
a registry, waiting."

---

## Why GitHub Container Registry (ghcr.io) instead of Docker Hub or AWS ECR

This was a deliberate choice given where things stand right now:

- **Docker Hub** has pull rate limits on the free tier and would need a
  separate account/login secret configured
- **AWS ECR** would need... an AWS account, which is exactly what's
  currently blocked
- **GitHub Container Registry** is free, and since the code is already on
  GitHub, authentication is automatic - no new account, no secrets to
  configure by hand

This means once your AWS account situation is resolved, Phase 3 becomes
"pull the already-built image from ghcr.io onto EC2" rather than "figure
out how to build it there from scratch" - the hard part is already solved
and automated.

---

## Walking through `ci.yml`

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```
This defines *when* the workflow runs: any push to `main`, and any pull
request targeting `main`. If you ever start using feature branches and PRs
(rather than pushing straight to main), this means tests run automatically
before you even merge - catching problems before they land on main at all.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
```
A "job" is a set of steps that run together on a fresh virtual machine -
`ubuntu-latest` here means GitHub spins up a brand new, clean Ubuntu Linux
machine just for this run, does the work, then throws it away. Every run
starts from zero, so there's no risk of "works because of leftover state
from last time."

```yaml
      - name: Check out the repo
        uses: actions/checkout@v4
```
The fresh virtual machine starts completely empty - this step is what
actually copies your repo's code onto it. `actions/checkout` is an
official, pre-built GitHub Action (a reusable step) that does this.

```yaml
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
          cache-dependency-path: requirements-dev.txt
```
Installs Python 3.12 on that clean machine. The `cache` settings mean:
remember the downloaded packages between workflow runs, keyed to whether
`requirements-dev.txt` has changed. If you haven't touched your
dependencies since the last push, this step becomes nearly instant instead
of re-downloading everything from PyPI every single time.

```yaml
      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Run tests
        run: python -m pytest tests/ -v
```
The actual point of the "test" job - install everything needed (including
`pytest`, which is why we use `requirements-dev.txt` here specifically,
not the lean `requirements.txt`), then run your full test suite. If any of
the 15 tests fail, this step fails, and GitHub marks the whole run as
failed - which is exactly the visual "red X" you'd see next to a bad
commit, versus a green checkmark for one that's clean.

```yaml
  build-and-push:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```
A second, separate job. `needs: test` means this one won't even start
unless the `test` job finished successfully first - no point building and
publishing an image from code that doesn't pass its own tests. The `if`
condition adds a second gate: only run this on actual pushes to `main`,
never on pull requests. This is intentional - a PR might contain
experimental or incomplete code, and we don't want that accidentally
published as if it were a real release.

```yaml
    permissions:
      contents: read
      packages: write
```
By default, GitHub Actions jobs get fairly limited permissions for
security reasons. This explicitly grants the one extra permission this job
actually needs - the ability to publish (`write`) to GitHub Packages
(where container images live). Being explicit about exactly what
permissions a job needs, rather than granting broad access, is a security
best practice worth knowing for interviews.

```yaml
      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
```
`github.actor` is whoever (or whatever) triggered this workflow run -
usually you, pushing a commit. `secrets.GITHUB_TOKEN` is a temporary,
automatically-generated credential that GitHub creates fresh for every
single workflow run and destroys afterward - you never had to create or
store this yourself, which is exactly why no manual registry account/login
was needed for this part.

```yaml
      - name: Build and push image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/task-manager-flask:latest
            ghcr.io/${{ github.repository_owner }}/task-manager-flask:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```
This is the actual build+publish step, using your existing `Dockerfile` -
the same one tested locally with Docker Desktop. `context: .` means "build
using the current repo root," same as `docker build .` would locally.

Two tags get pushed for every successful build: `latest` (always the
newest version) and one tagged with the exact commit hash
(`github.sha`) - a permanent, specific snapshot. This distinction matters
later: `latest` is handy for quick manual testing, but a real deployment
should reference a specific SHA-tagged image, not `latest` - so that a new
push to main can never accidentally change what's running in production
without you deliberately redeploying.

The `cache-from`/`cache-to` lines apply the same layer-caching concept
from the Dockerfile itself (remember: copy requirements before code, so
unchanged dependency layers get reused) - but extended across separate CI
runs, using GitHub's own cache storage (`type=gha`). Without this, every
single CI run would rebuild everything from scratch even if nothing
dependency-related changed.

---

## What you'll actually see on GitHub after this is pushed

1. Go to your repo → the **Actions** tab - you'll see this workflow listed,
   with a run for this exact push
2. Click into it to watch both jobs execute in something close to real
   time, with full logs for each step
3. Once `build-and-push` finishes, go to your repo's main page → look for
   **Packages** in the right sidebar - your published Docker image will be
   listed there, pullable by anyone with:
   ```
   docker pull ghcr.io/big-dd9/task-manager-flask:latest
   ```
4. The badge added to the top of `README.md` will show green ("passing")
   or red ("failing") based on the most recent run on `main` - this is a
   real, live status, not just decoration; it updates automatically.

---

## What this sets up for Phase 3

Once your AWS account situation is sorted, deploying becomes: SSH into
EC2, run `docker pull ghcr.io/big-dd9/task-manager-flask:<sha>`, then
`docker run` it (or use it inside a `docker-compose.yml` on the server
pointed at RDS instead of a local Postgres container) - no building
required on the server itself, since GitHub already built and tested the
exact image you'd be deploying.
