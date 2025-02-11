import json
from datetime import datetime
from logging import Logger
from typing import Optional
from urllib.parse import urljoin
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from common import model_utils
from common.openai_client import AssistantsService
from common.openai_client import ChatCompletionService
from common.openai_client import EmbeddingService
from dagster import ConfigurableResource
from dagster import InitResourceContext
from dagster import ResourceDependency
from dagster import get_dagster_logger
from exa_py import Exa
from pydantic import PrivateAttr
from resources.pg_warehouse_resource import XLAUNCH_DB
from resources.pg_warehouse_resource import PGWarehouseResource
from resources.secret_manager_resource import SecretManagerResource
from video_gen_v2.types.combination import Combination
from video_gen_v2.types.combination_features import CombinationFeatures
from video_gen_v2.types.combination_texts import CombinationTexts
from video_gen_v2.types.queries import get_generation
from video_gen_v2.types.queries import update_generation
from video_gen_v2.types.song import Song


def find_competitors(business_website: str, num_results: int = 10):
    exa_client = Exa(api_key="....")
    # Extract base domain from URL
    business_website = (
        "https://" + business_website
        if not business_website.startswith("http")
        else business_website
    )
    parsed_url = urlparse(business_website)
    base_domain = parsed_url.netloc.replace("www.", "")

    response = exa_client.find_similar_and_contents(
        url=business_website,
        exclude_domains=[base_domain, "wikipedia.org"],
        num_results=num_results,
        summary={
            "query": f"Why is this company a competitor of {base_domain}? What are their unique selling points?"
        },
        text={"max_characters": 10000},
    )
    # Convert response to serializable format
    return [
        {"title": result.title, "url": result.url, "text": result.text, "summary": result.summary}
        for result in response.results
    ]


def search_internet(query: str, num_results: int = 5, *args, **kwargs):
    exa_client = Exa(api_key="....")
    response = exa_client.search_and_contents(
        query=query,
        type="auto",
        num_results=num_results,
        text={"max_characters": 10000},
        livecrawl="always",
        *args,
        **kwargs,
    )
    # Convert response to serializable format
    return [
        {"title": result.title, "url": result.url, "text": result.text}
        for result in response.results
    ]


class VoxResource(ConfigurableResource):
    secret_manager: ResourceDependency[SecretManagerResource]
    pg_warehouse_resource: ResourceDependency[PGWarehouseResource]
    _logger: Logger = PrivateAttr()
    _openai_api_key: str = PrivateAttr()
    _song_vector_map: dict[str, list[float]] = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext):
        self._logger = get_dagster_logger()
        self._openai_api_key = self.secret_manager.get_secret("OPENAI_API_KEY")
        self._song_vector_map = {}

    def _update_generation(self, generation_id: str, product_data: dict):
        ....
        update_generation(self.pg_warehouse_resource, generation)

    def get_combinations(
        self, generation_id: str, product_url: str, source_image_urls: list[str] = []
    ):
        ....
        return combinations

    def _extract_data_from_website(self, url: str, image_urls: list[str] = []):
        ....

    def _fetch_website_content(self, url: str, image_urls: list[str] = []):
        ....

    def _get_product_metadata(self, website_content, url):
        ....

    def _analyze_product_images(
        self, images_url: list[str], product_description: Optional[str] = None
    ):
        chat_service = ChatCompletionService(self._openai_api_key)

        system_prompt = """
        You are an expert in product photography analysis. Your task is to select the best product image
        for an advertisement where the product needs to be isolated from its background.
        If there are images of multiple products, use the product description parsed from it's website to select the best image in addition to the requirements below.

        Requirements for the ideal image:
        1. Must be a clear frontal view of the product
        2. Product should be well-lit and in focus
        3. Minimal background distractions (avoid images animals, or complex backgrounds)
        4. Images with humans are strictly not acceptable
        4. Product should be centered in the frame
        5. Entire product should be visible
        6. The image of just the brand logo is not acceptable
        7. Use the product description to determine if the product is a bundle or a single item, if it is a bundle, prefer the image of the bundle and if it's not a bundle, select the image of the single item

        Analyze the given image URLs and return a JSON with the image URL of the best image and a brief explanation.
        OUTPUT FORMAT:
        ```json
        {
        "image_url": "[URL of the best image]",
        "explanation": "[Brief explanation of why this image is the best]"
        }
        ```
        """
        prompt = f"""Select the best image that meets our requirements for background removal and animation
        Images: {images_url}
        """
        if product_description:
            prompt += f"Use the product description as well to select the best image: {product_description}"
        try:
            response = chat_service.make_completion_call(
                prompt, system_prompt, images_url=images_url, max_tokens=1000, ensure_json=True
            )
        except Exception as e:
            raise ValueError(f"Error analyzing product images: {str(e)}")
        if "image_url" not in response:
            raise ValueError("No image URL found in the response")
        if "explanation" in response:
            self._logger.info(f"Explanation for the best image: {response['explanation']}")
        return response["image_url"]

    def _get_business_research(
        self,
        business_name,
        business_website,
        product_name_or_list=None,
        theme=None,
        top_audience_categories=None,
    ):
        ...

    def _run_assistant(self, user_message, assistant_id, images=None):
        function_map = {"find_competitors": find_competitors, "search_internet": search_internet}
        assistant = AssistantsService(
            api_key=self._openai_api_key, assistant_id=assistant_id, function_map=function_map
        )
        thread_id = assistant.create_thread()
        responses = []
        for response in assistant.run_assistant(thread_id, user_message, assistant_id, images):
            responses.append(response)
        return responses

    def _get_top_audiences(self, business_research, product_description):
        chat_service = ChatCompletionService(self._openai_api_key)
        system_prompt = """
        
        PORTAL AI SECRET PROMPT
        
        """
        business_research_str = [
            f"{key.upper()}: {value}" for key, value in business_research.items()
        ]
        business_research_str = "\n".join(business_research_str)

        prompt = f"""
        {business_research_str}
        Product Description: {product_description}
        """
        response = chat_service.make_completion_call(
            prompt, system_prompt, max_tokens=10000, ensure_json=True
        )
        return response.get("audiences", [])

    def _get_background_image_prompt(self, audience, image_url):
        chat_service = ChatCompletionService(self._openai_api_key)
        system_prompt = """
        PORTAL AI SECRET PROMPT
        """
        audience_str = [
            f"{key.upper()}: {value}" for key, value in audience.items() if key != "platform"
        ]
        audience_str = "\n".join(audience_str)
        prompt = f"{audience_str}"
        response = chat_service.make_completion_call(
            # prompt, system_prompt, max_tokens=3000, ensure_json=True, images_url=[image_url]
            prompt,
            system_prompt,
            max_tokens=3000,
            ensure_json=True,
        )
        self._logger.info(f"Background image prompt: {response.get('prompt', '')}")
        return response.get("prompt", "")

    def _get_miscellaneous_data(self, audience, product_description, business_research):
        chat_service = ChatCompletionService(self._openai_api_key)
        system_prompt = """
        PORTAL AI SECRET PROMPT
        """
        audience_str = [
            f"{key.upper()}: {value}" for key, value in audience.items() if key != "platform"
        ]
        prompt = f"""
        Business Overview: {business_research.get('business_overview')}
        Product Description: {product_description}
        {audience_str}
        """
        response = chat_service.make_completion_call(
            prompt, system_prompt, max_tokens=4000, ensure_json=True
        )
        return response

    def _load_song_vector_map(self):
        if self._song_vector_map:
            return
        query = """
                SELECT *
                FROM song"""
        songs = self.pg_warehouse_resource.read_sql_pydantic(
            db_name=XLAUNCH_DB, sql=query, model_cls=Song
        )
        self._song_vector_map = {
            song.id: model_utils.parse_vector(song.prompt_vector) for song in songs
        }

    def _get_relevant_song_id(self, background_music_prompt):
        self._load_song_vector_map()
        embedding_client = EmbeddingService(self._openai_api_key)
        song_vector = embedding_client.get_embedding(background_music_prompt)
        song_id = model_utils.find_k_nearest_vectors(song_vector, self._song_vector_map)[0][0]
        return song_id
