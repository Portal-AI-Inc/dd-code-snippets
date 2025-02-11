CREATIVE_FORMAT = "mp4"
THUMBNAIL_FORMAT = "jpg"


@dg.op
def merge_videos(
    context: dg.OpExecutionContext,
    pg_warehouse_resource: PGWarehouseResource,
    natural_selection_storage: NaturalSelectionStorage,
    merge_video_resource: MergeVideoResource,
    combination_id: str,
    image_urls: List[str],
) -> Combination:
    context.log.info(f"merging videos: {image_urls} for {combination_id}")
    combination, generation = _get_combination_generation(pg_warehouse_resource, combination_id)
    context.log.info(f"starting merge_video with features={combination.features}")
    current_path = os.path.dirname(os.path.abspath(__file__))
    filename = f"{uuid4()}"  # replace uuid with hashed features to enable caching
    creative_local_path = f"{current_path}/{filename}.{CREATIVE_FORMAT}"
    thumbnail_local_path = f"{current_path}/{filename}.{THUMBNAIL_FORMAT}"
    merge_video_resource.merge_videos(combination, image_urls, creative_local_path)
    write_video_thumbnail(creative_local_path, thumbnail_local_path)
    sku_path = f"selection/{generation.integration_id}/{generation.name}/{combination.features.sku}"
    creative_path = f"{sku_path}/reels/{filename}.{CREATIVE_FORMAT}"
    thumbnail_path = f"{sku_path}/thumbnails/{filename}.{THUMBNAIL_FORMAT}"
    creative_url = natural_selection_storage.save_filepath_s3(creative_local_path, creative_path)
    thumbnail_url = natural_selection_storage.save_filepath_s3(thumbnail_local_path, thumbnail_path)
    os.remove(creative_local_path)
    os.remove(thumbnail_local_path)
    context.log.info(
        f"Ending merge_video for combination_id={combination_id}. \n"
        f"creative_url = {creative_url.replace(' ', '%20')}. \n"
        f"thumbnail_url = {thumbnail_url.replace(' ', '%20')}."
    )
    combination.creative_url = creative_url
    combination.thumbnail_url = thumbnail_url
    return combination
