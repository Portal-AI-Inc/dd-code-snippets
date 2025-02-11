import tempfile
import time
import uuid
from datetime import datetime
from datetime import timedelta
from enum import Enum
from logging import Logger
from typing import List
from typing import Optional

import numpy as np
import pycountry
import requests
from dagster import ConfigurableResource
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.advideo import AdVideo
from facebook_business.adobjects.campaign import Campaign
from pydantic import Field
from pydantic import PrivateAttr
from pydantic.v1 import BaseModel
from video_gen_v2.types.combination import Combination

DEFAULT_TARGETING_COUNTRY = ["US", "CA"]


class MetaAdsIntegration(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    access_token: str
    token_type: str
    meta_business_id: Optional[str]
    meta_business_name: str
    meta_adaccount_id: str
    meta_adaccount_name: str
    pixel_id: Optional[str]
    page_id: Optional[str]
    instagram_actor_id: Optional[str]
    publisher_platforms: List[str]
    facebook_positions: List[str]
    instagram_positions: List[str]
    audience_network_positions: List[str]
    messenger_positions: List[str]
    device_platforms: List[str]
    custom_audiences: List[str]


class PublisherPlatform(Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    AUDIENCE_NETWORK = "audience_network"
    MESSENGER = "messenger"


class DevicePlatforms(Enum):
    DESKTOP = "desktop"  # Desktop devices
    MOBILE = "mobile"  # Mobile devices
    CONNECTED_TV = "connected_tv"  # Connected TV devices


class FacebookPosition(Enum):
    FEED = "feed"  # Facebook Feed
    BIZ_DISCO_FEED = "biz_disco_feed"  # Facebook Business Discovery Feed
    FACEBOOK_REELS = "facebook_reels"  # Facebook Reels
    FACEBOOK_REELS_OVERLAY = "facebook_reels_overlay"  # Facebook Reels Overlay
    PROFILE_FEED = "profile_feed"  # Facebook Profile Feed
    RIGHT_HAND_COLUMN = "right_hand_column"  # Facebook Right Column
    VIDEO_FEEDS = "video_feeds"  # Facebook Video Feeds
    INSTREAM_VIDEO = "instream_video"  # Facebook In-Stream Videos
    MARKETPLACE = "marketplace"  # Facebook Marketplace
    STORY = "story"  # Facebook Stories
    SEARCH = "search"  # Facebook Search Results


class InstagramPosition(Enum):
    STREAM = "stream"  # Instagram Feed
    IG_SEARCH = "ig_search"  # Instagram Search Results
    STORY = "story"  # Instagram Stories
    EXPLORE = "explore"  # Instagram Explore
    REELS = "reels"  # Instagram Reels
    EXPLORE_HOME = "explore_home"  # Instagram Explore Home
    PROFILE_FEED = "profile_feed"  # Instagram Profile Feed
    PROFILE_REELS = "profile_reels"  # Instagram Profile Reels


class AudienceNetworkPosition(Enum):
    CLASSIC = "classic"  # Audience Network Native, Banner, and Interstitial
    REWARDED_VIDEO = "rewarded_video"  # Audience Network Rewarded Videos


class MessengerPosition(Enum):
    MESSENGER_HOME = "messenger_home"  # Messenger Inbox
    STORY = "story"  # Messenger Stories
    SPONSORED_MESSAGES = "sponsored_messages"  # Messenger Sponsored Messages


DEFAULT_FACEBOOK_CONFIG = {
    "publisher_platforms": [PublisherPlatform.FACEBOOK, PublisherPlatform.MESSENGER],
    "facebook_positions": [p for p in FacebookPosition],
    "instagram_positions": None,
    "audience_network_positions": None,
    "messenger_positions": [MessengerPosition.STORY],
}

DEFAULT_INSTAGRAM_CONFIG = {
    "publisher_platforms": [PublisherPlatform.INSTAGRAM],
    "facebook_positions": None,
    "instagram_positions": [p for p in InstagramPosition],
    "audience_network_positions": None,
    "messenger_positions": None,
}


# use None for advantage+ placements
DEFAULT_BOTH_PLATFORMS_CONFIG = {
    "publisher_platforms": None,
    "facebook_positions": None,
    "instagram_positions": None,
    "audience_network_positions": None,
    "messenger_positions": None,
}


class MetaAdsResource(ConfigurableResource):
    _logger: Logger = PrivateAttr()

    def launch_campaign(self, ad_account_id: str) -> str:
        date = time.strftime("%Y-%m-%d")
        campaign_name = f"Portal {date}"
        campaign = Campaign(parent_id=f"act_{ad_account_id}")
        campaign.update(
            {
                "name": campaign_name,
                "objective": Campaign.Objective.outcome_sales,
                "status": "ACTIVE",
                "special_ad_categories": ["NONE"],
                "advantages_plus_creative": True,
                "smart_promotion_type": "SMART_PROMOTION_TYPE",
            }
        )
        campaign.remote_create()
        return campaign.get_id()

    def launch_ad(
        self, meta_ads: MetaAdsIntegration, combination: Combination, daily_budget_usd: float
    ):
        countries = (
            combination.features.countries
            if combination.features.countries
            else DEFAULT_TARGETING_COUNTRY
        )
        platform_config = self._get_platform_config("both")
        ad_set_id = self._create_ad_set(
            ad_account_id=meta_ads.meta_adaccount_id,
            campaign_id=meta_ads.meta_adaccount_id,
            page_id=meta_ads.page_id,
            shop_product_id=combination.shop_product_id,
            pixel_id=meta_ads.pixel_id,
            daily_budget_usd=daily_budget_usd,
            countries=countries,
            gender=combination.features.gender,
            start_time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
            end_time=datetime.now() + timedelta(days=7),
            publisher_platforms=platform_config["publisher_platforms"],
            facebook_positions=platform_config["facebook_positions"],
            instagram_positions=platform_config["instagram_positions"],
            audience_network_positions=platform_config["audience_network_positions"],
            messenger_positions=platform_config["messenger_positions"],
        )

        video_id = self._upload_video(meta_ads.meta_adaccount_id, combination.creative_url)
        image_hash = self._upload_image(meta_ads.meta_adaccount_id, combination.thumbnail_url)

        # Create ad creative
        creative_id = self._create_ad_creative(
            meta_ads.meta_adaccount_id,
            video_id,
            image_hash,
            ad_title=combination.features.headline,
            ad_message=combination.features.primary_text,
            ad_description=combination.features.description,
            website_url=combination.product_url,
            page_id=meta_ads.page_id,
            sku_name=combination.features.sku,
            instagram_actor_id=meta_ads.page_id,
            shop_product_id=combination.shop_product_id,
        )

        # Create ad
        ad_id = self._create_ad(
            meta_ads.meta_adaccount_id, ad_set_id, creative_id, combination.features.sku
        )
        return ad_id

    def _create_ad_set(
        self,
        ad_account_id: str,
        campaign_id: str,
        page_id: str,
        shop_product_id: str,
        pixel_id: str,
        daily_budget_usd: float,
        countries,
        gender,
        start_time,
        end_time,
        publisher_platforms=None,
        device_platforms=None,
        facebook_positions=None,
        instagram_positions=None,
        audience_network_positions=None,
        messenger_positions=None,
    ):
        ...
        
    def _convert_to_country_code(self, country):
        ....

    def _get_platform_config(self, platform: str = "both"):
        ...

    def _upload_video(self, ad_account_id, video_url):
        ...

    def _upload_image(self, ad_account_id, image_url):
        ...

    def _create_ad_creative(
        self,
        ad_account_id,
        video_id,
        image_hash,
        ad_title,
        ad_message,
        ad_description,
        website_url,
        page_id,
        sku_name,
        instagram_actor_id=None,
        shop_product_id=None,
        link_click_campaign=False,
    ):
        ...

    def _create_ad(self, ad_account_id, ad_set_id, creative_id, sku_name):
        ad = Ad(parent_id=f"act_{ad_account_id}")
        ad_name = f"{sku_name} - Ad"
        ad.update(
            {
                "name": ad_name,
                "adset_id": ad_set_id,
                "creative": {"creative_id": creative_id},
                "status": "ACTIVE",
            }
        )
        ad.remote_create()
        self._logger.info(f"Ad deployed: {ad_name}")
        return ad.get_id()
