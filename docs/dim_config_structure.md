# dim config structure

## dim config explained

```
.
└── dim_config [required]
    ├── owner [required] - information regarding who "owns" this table (not used for alerting). Meant to be used to make it easier to contact the owner.
    │   ├── email [required] - owner's email
    │   └── slack [optional] - owner's slack handle
    ├── slack_alerts [optional] - slack alerting options, if not provided no alerts will be sent out.
    │   ├── enabled [required] - true or false, used to enable or disable slack alerts.
    │   └── notify [required]
    │       └── channels [required] - a list of slack channels to notify about any failed tests.
    ├── tier [required] - Demonstrates how critical the table is.
    └── dim_tests [required] - a list of dim tests to run on the corresponding table.
        ├── type [required] - dim test type, must be defined inside `dim/models/dim_check_type/`
        └── params [required] - test dependant, provides additional information to format sql template used to execute the test. See `docs/dim_tests` for test specific settings.
```

### Example `dim_config.yaml`

```yaml
dim_config:
  owner:
    email: [owner_email]
    slack: [owner_slack_handle]
  slack_alerts:
    enabled: true
    notify:
      channels:
        - [slack_channel]
  tier: tier_3
  dim_tests:
    - type: table_row_count
      params:
        condition: ">= 1"
    - type: not_null
      params:
        condition: "> 0"
        columns:
          - project_id
          - dataset
    - type: uniqueness
      params:
        columns:
          - project_id
    - type: column_length
      params:
        columns:
          - project_id
        condition: "<> 2"
    - type: value_in_set
      params:
        columns:
          - project_id
        expected_values:
          - data-monitoring-dev
          - moz-fx-data-shared-prod
    - type: custom_sql_metric
      params:
        sql: |
              SELECT COUNT(*) AS total_count
              FROM `[project_id].[dataset].[table]`
              WHERE
                user_type = 'amazing'
        condition: total_count > 3000
```