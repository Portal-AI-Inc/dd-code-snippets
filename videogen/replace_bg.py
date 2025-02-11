from typing import Generator

import dagster as dg
from dagster import OpExecutionContext
from dagster import op
from instrument import sentry
from resources.cloudwatch_metrics_resource_v2 import CloudwatchMetricsResourceV2
from resources.pg_warehouse_resource import PGWarehouseResource
from resources.videogen.segmind_resource import SegmindResource
from video_gen_v2.retry_policy import VIDEO_GEN_RETRY_POLICY
from video_gen_v2.types.combination import Combination

SCENES_PER_COMBINATION = 5
TIMEOUT_REPLACE_BG = 60 * 5


@dg.op(out=dg.DynamicOut(Combination))
def generate_replace_bg_ops(
    context: dg.OpExecutionContext,
    pg_warehouse_resource: PGWarehouseResource,
    combination_id: str,
) -> Generator[dg.DynamicOutput[Combination], None, None]:
    context.log.info(f"generating replace_bg ops for {combination_id=}")
    query = f"select * from combination where id = '{combination_id}'"
    combination = pg_warehouse_resource.read_one_sql_pydantic(query, model_cls=Combination)
    for i in range(SCENES_PER_COMBINATION):
        yield dg.DynamicOutput(combination, mapping_key=f"{i + 1}")


@op(retry_policy=VIDEO_GEN_RETRY_POLICY)
@sentry.capture_exceptions
async def replace_bg(
    context: OpExecutionContext,
    segmind_resource: SegmindResource,
    cloudwatch_metrics_resource_v2: CloudwatchMetricsResourceV2,
    combination: Combination,
) -> str:
    context.log.info(f"Replacing background for {combination.id=}")
    ex_unit = cloudwatch_metrics_resource_v2.create_track_execution_unit()
    features = combination.features
    image_url = segmind_resource.replace_bg(
        features.source_image_url,
        features.background_prompt,
        timeout=TIMEOUT_REPLACE_BG,
    )
    context.log.info(f"Background replaced: {image_url}")
    ex_unit.track_success("replace_bg")
    return image_url
