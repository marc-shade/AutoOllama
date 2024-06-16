def find_all_scenes(discussion_history: str) -> List[str]:
    """
    Finds all potential scenes to illustrate from the discussion history,
    considering user input and AI agent requests.

    :param discussion_history: The entire discussion history.
    :return: A list of all potential scenes to illustrate.
    """
    all_scenes = []

    # 1. Check for user input image requests
    user_image_request_pattern = r"(?:Images?|Illustrations?|Visuals?):\s*(.*?)\n\n" # Expanded pattern
    user_image_requests = re.findall(user_image_request_pattern, discussion_history, re.DOTALL)
    for user_image_request in user_image_requests:
        all_scenes.extend(re.split(r'\d+\.\s', user_image_request.strip())) # Split by numbered list items

    # 2. Check for AI agent image requests
    ai_image_request_pattern = r"!\[Image Request]\((.*?)\)"
    ai_image_requests = re.findall(ai_image_request_pattern, discussion_history)
    all_scenes.extend(ai_image_requests)

    # Remove empty strings and duplicates
    all_scenes = [scene.strip() for scene in all_scenes if scene.strip()]
    all_scenes = list(set(all_scenes))

    return all_scenes
