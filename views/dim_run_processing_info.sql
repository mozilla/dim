CREATE VIEW
`data-monitoring-dev.dim.dim_run_processing_info`
AS
SELECT
  *,
  (total_bytes_processed / (1024 * 1024 * 1024) / 1000) * 5 AS usd_cost_estimate,
FROM `data-monitoring-dev.dim.dim_run_processing_info_v1`
