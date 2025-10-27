from langchain_core.tools import tool
import requests
from functools import wraps
from typing import Callable, Any, Dict
from src.core.utils.settings import get_settings

# from src.core.utils.token_manager import inject_jwt_token

# request_domain = os.environ['TUTORNET_API_URL']
settings = get_settings()
request_domain = settings.service_api_url
def wrap_get_couse_list_service(wrapper_config : Dict[str, Any]):
    @tool
    def get_course_list(keyword: str) -> list:
        """
        Get the list of courses.

        Args:
            keyword (str): The keyword to search for.

        Returns:
            list: The list of courses matching the keyword, including id, title, description, image, rating, tutor, starting price etc.
        """
        try:
            # print(f"Searching courses with keyword: {keyword,request_domain,authorization}")
            #Wrapper config will contain the jwt token
            response = requests.get(f"{request_domain}/api/courses/search?query={keyword}", 
                                    headers={"Content-Type":"text","authorization":f"{wrapper_config['authorization']}"})
            return response.json()
        except Exception as e:
            return f"Error: {e}"
    return get_course_list



def wrap_get_couse_details_service(wrapper_config : Dict[str, Any]):
    @tool
    def get_course_details(course_id: str) -> object:
        """
        Get the details of a course.

        Args:
            course_id (str): The ID of the course to get details for.

        Returns:
            Json: The details of the course, including description, tutor info, attributes, variants with its price and availability, etc.
        """
        try:
            response = requests.get(f"{request_domain}/api/courses/{course_id}/details", json={"course_id": course_id}, 
                                    headers={"Content-Type":"text","authorization":f"{wrapper_config['authorization']}"})
            return response.json()
        except Exception as e:
            return f"Error: {e}"
    return get_course_details


def wrap_place_order_service(wrapper_config : Dict[str, Any]):
    @tool
    def place_order(variation_id: str) -> object:
        """
        Place an order for a course.

        Args:
            variation_id (str): The ID of the course variation to order.

        Returns:
            object: The result of the order placement
        """
        try:
            payload = {"variation_id": variation_id, "quantity": 1}
            response = requests.post(f"{request_domain}/api/order/place", json=payload, 
                                    headers={"Content-Type":"application/json","authorization":f"{wrapper_config['authorization']}"})
            return response.json()
        except Exception as e:
            return f"Error: {e}"
    return place_order

@tool
def get_images_by_urls(urlList: list[str]) -> list[str]:
    """
    Get images by URLList.

    Args:
        urlList (list[str]): The list of image URLs.

    Returns:
        list[dict]: List of dicts with url, mime_type, and base64-encoded image data.

    Example return:
        [
            {
                "url": "https://...",
                "mime_type": "image/png",
                "base64": "iVBORw0KGgo..."
            },
            ...
        ]
    """
    import base64
    try:
        images = []
        for url in urlList:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    mime_type = response.headers.get("Content-Type", "application/octet-stream")
                    b64 = base64.b64encode(response.content).decode("utf-8")
                    images.append({
                        "url": url,
                        "mime_type": mime_type,
                        "base64": b64
                    })
                else:
                    images.append({
                        "url": url,
                        "error": f"HTTP {response.status_code}"
                    })
            except Exception as e:
                images.append({
                    "url": url,
                    "error": str(e)
                })
        return images
    except Exception as e:
        return [{"error": str(e)}]