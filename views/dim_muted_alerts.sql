CREATE VIEW
    `data-monitoring-dev.dim.dim_muted_alerts`
AS
SELECT
  *
FROM `data-monitoring-dev.dim.dim_muted_alerts_v1`
LEFT JOIN `data-monitoring-dev.dim.dim_muted_alerts_extra_info`
  USING(project_id, dataset, `table`, date_partition)