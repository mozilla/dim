import json
from textwrap import dedent
from typing import Any, Dict

import attr
import jinja2
import yaml


def prepare_params(
    project_id,
    dataset,
    table,
    *,
    dim_config,
    alert_muted,
    check_params,
    run_uuid,
    date_partition,
):
    query_params = {
        **attr.asdict(check_params),
        "owner": json.dumps(attr.asdict(dim_config.owner)),
        "alert_enabled": dim_config.slack_alerts.enabled,
        "alert_muted": alert_muted,
        "partition": date_partition,
        "run_id": run_uuid,
        "tier": dim_config.tier,
        "partition_field": dim_config.partition_field,
    }

    if user_sql := query_params.get("sql"):
        templated_fields = {
            "project_id": project_id,
            "dataset": dataset,
            "table": table,
            "date_partition": date_partition,
        }

        user_sql_template = jinja2.Environment().from_string(user_sql)
        rendered_user_sql = user_sql_template.render(**templated_fields)
        query_params["sql"] = dedent(rendered_user_sql)

    return query_params


def read_config(config_path: str) -> Dict[Any, Any]:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config
