-- adidas_social_snapshot_api: Public social-platform snapshots for the adidas brand.
SELECT
    platform,
        handle,
        date,
        audience_m,
        scale_metric_m,
        scale_metric_label,
        content_count,
        source,
        source_url
FROM adidas_social_snapshot
ORDER BY platform
