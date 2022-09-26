# dim

#TODO: add project description here
#TODO: add getting started guide here

## Prerequisites

- python >= `3.10` < `3.11`
- docker

## Architecture design

### Diagram
TODO: add architecture diagram here

### Execution flow

1. Run docker image with command (command consists of: dataset/table to run tests for \[required\], specific tests types to execute, default is to run all defined tests \[optional\])
1. Check corresponding path exists (dim/gcp_project/dataset/table)
1. Validate matching configs on read time (this should be fine since they're very small)
1. Create corresponding test objects, this includes test execution and success parameters
1. Execute all tests and persist results in BQ (can be used to build Looker dashboard on top of this dim exeuction metadata)
1. If specified, perform post-test actions (like alerting)
1. Return test result to the caller and list of post-test action taken

# Other TODOs

## Add pre-commit checks

- *.md file linter
- *.py files (flake8 + black)
- *.yaml linter