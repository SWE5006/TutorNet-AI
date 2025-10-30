from langchain_core.tools import tool
import requests
from functools import wraps
from typing import Callable, Any, Dict
from src.core.utils.settings import get_settings

# from src.core.utils.token_manager import inject_jwt_token

# request_domain = os.environ['TUTORNET_API_URL']
settings = get_settings()
request_domain = settings.service_api_url

def wrap_get_tutor_list_service(wrapper_config : Dict[str, Any]):
    @tool
    def get_tutor_list(keyword: str) -> list:
        """
        Get the list of tutors based on keyword.

        Args:
            keyword (str): The keyword to search for.

        Returns:
            list: The list of tutors matching the keyword, including id, name.
        """
        try:
            response = requests.get(f"{request_domain}/api/users/search?query={keyword}", 
                                    headers={"Content-Type":"text","authorization":f"{wrapper_config['authorization']}"})
            return response.json()
        except Exception as e:
            return f"Error: {e}"
    return get_tutor_list


def wrap_get_course_list_service(wrapper_config : Dict[str, Any]):
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
            response = requests.get(f"{request_domain}/api/courses/search?query={keyword}", 
                                    headers={"Content-Type":"text","authorization":f"{wrapper_config['authorization']}"})
            return response.json()
        except Exception as e:
            return f"Error: {e}"
    return get_course_list



def wrap_get_course_details_service(wrapper_config : Dict[str, Any]):
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