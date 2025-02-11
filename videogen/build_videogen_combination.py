@dg.graph
def build_videogen_combination(combination_id: str) -> Combination:
    replace_bg_ops = generate_replace_bg_ops(combination_id)
    images = replace_bg_ops.map(replace_bg)
    validated_images = images.map(validate_image).collect()
    updated_combination = merge_videos(combination_id, validated_images)
    return update_combination(updated_combination)