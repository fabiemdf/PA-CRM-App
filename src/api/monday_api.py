"""
Monday.com API integration.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
import requests

from utils.error_handling import APIError, NetworkError, ErrorCodes, retry

# Get logger
logger = logging.getLogger("monday_uploader.monday_api")

class MondayAPI:
    """
    Monday.com API client.
    Provides methods for interacting with the Monday.com API.
    """
    
    BASE_URL = "https://api.monday.com/v2"
    
    def __init__(self, api_key: str):
        """
        Initialize the API client.
        
        Args:
            api_key: Monday.com API key
        """
        self.api_key = api_key
    
    @retry(max_retries=3, retry_delay=1.0)
    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the Monday.com API.
        
        Args:
            query: GraphQL query
            variables: Variables for the query
            
        Returns:
            Response data
            
        Raises:
            APIError: If the API responds with an error
            NetworkError: If a network-related error occurs
        """
        try:
            headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "query": query
            }
            
            if variables:
                data["variables"] = variables
                
            response = requests.post(
                self.BASE_URL,
                json=data,
                headers=headers
            )
            
            # Raise for HTTP errors
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Check for GraphQL errors
            if "errors" in response_data:
                errors = response_data["errors"]
                first_error = errors[0] if errors else {"message": "Unknown GraphQL error"}
                error_message = first_error.get("message", "Unknown GraphQL error")
                
                # Determine error type
                if "rate limit" in error_message.lower():
                    error_code = ErrorCodes.API_RATE_LIMIT_EXCEEDED
                elif "unauthorized" in error_message.lower() or "authentication" in error_message.lower():
                    error_code = ErrorCodes.API_AUTHENTICATION_ERROR
                elif "not found" in error_message.lower():
                    error_code = ErrorCodes.API_RESOURCE_NOT_FOUND
                elif "permission" in error_message.lower():
                    error_code = ErrorCodes.API_PERMISSION_DENIED
                else:
                    error_code = ErrorCodes.API_REQUEST_INVALID
                    
                raise APIError(
                    message=f"GraphQL Error: {error_message}",
                    error_code=error_code,
                    http_status=response.status_code,
                    response_body=response.text
                )
                
            return response_data
                
        except requests.Timeout as e:
            raise NetworkError(
                message=f"Connection timed out: {str(e)}",
                error_code=ErrorCodes.CONNECTION_TIMEOUT,
                original_exception=e
            )
        except requests.ConnectionError as e:
            raise NetworkError(
                message=f"Connection error: {str(e)}",
                error_code=ErrorCodes.NETWORK_UNAVAILABLE,
                original_exception=e
            )
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                response_text = e.response.text
                
                try:
                    response_data = e.response.json()
                    if "error_code" in response_data:
                        error_message = response_data.get("error_message", "Unknown API error")
                    else:
                        error_message = f"API request failed with status {status_code}"
                except:
                    error_message = f"API request failed with status {status_code}"
                    
                raise APIError(
                    message=error_message,
                    error_code=ErrorCodes.API_SERVER_ERROR,
                    original_exception=e,
                    http_status=status_code,
                    response_body=response_text
                )
            else:
                raise NetworkError(
                    message=f"Network error: {str(e)}",
                    error_code=ErrorCodes.NETWORK_ERROR,
                    original_exception=e
                )
    
    def is_api_key_valid(self) -> bool:
        """
        Check if the API key is valid.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Simple query to check API key validity
            query = """
            query {
                me {
                    id
                    name
                }
            }
            """
            
            result = self.execute_query(query)
            return "data" in result and "me" in result["data"] and result["data"]["me"] is not None
        except Exception as e:
            logger.warning(f"API key validation failed: {str(e)}")
            return False
    
    def get_boards(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all accessible boards.
        
        Args:
            limit: Maximum number of boards to retrieve
            
        Returns:
            List of boards
        """
        query = """
        query ($limit: Int) {
            boards (limit: $limit) {
                id
                name
                description
                state
            }
        }
        """
        
        variables = {
            "limit": limit
        }
        
        result = self.execute_query(query, variables)
        
        if "data" in result and "boards" in result["data"]:
            return result["data"]["boards"]
        
        return []
    
    def get_board(self, board_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific board by ID.
        
        Args:
            board_id: Board ID
            
        Returns:
            Board data if found, None otherwise
        """
        query = """
        query ($board_id: ID!) {
            boards (ids: [$board_id]) {
                id
                name
                description
                state
                columns {
                    id
                    title
                    type
                    settings_str
                }
                groups {
                    id
                    title
                    color
                }
            }
        }
        """
        
        variables = {
            "board_id": board_id
        }
        
        result = self.execute_query(query, variables)
        
        if ("data" in result and 
            "boards" in result["data"] and 
            result["data"]["boards"] and 
            len(result["data"]["boards"]) > 0):
            return result["data"]["boards"][0]
        
        return None
    
    def get_board_items(self, board_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Get all items from a board.
        
        Args:
            board_id: Board ID
            limit: Maximum number of items to retrieve
            
        Returns:
            List of items
        """
        query = """
        query ($board_id: ID!, $limit: Int) {
            boards (ids: [$board_id]) {
                items (limit: $limit) {
                    id
                    name
                    state
                    group {
                        id
                        title
                    }
                    column_values {
                        id
                        title
                        text
                        value
                        type
                    }
                    created_at
                    updated_at
                }
            }
        }
        """
        
        variables = {
            "board_id": board_id,
            "limit": limit
        }
        
        result = self.execute_query(query, variables)
        
        if ("data" in result and 
            "boards" in result["data"] and 
            result["data"]["boards"] and 
            len(result["data"]["boards"]) > 0 and
            "items" in result["data"]["boards"][0]):
            return result["data"]["boards"][0]["items"]
        
        return []
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific item by ID.
        
        Args:
            item_id: Item ID
            
        Returns:
            Item data if found, None otherwise
        """
        query = """
        query ($item_id: ID!) {
            items (ids: [$item_id]) {
                id
                name
                state
                board {
                    id
                    name
                }
                group {
                    id
                    title
                }
                column_values {
                    id
                    title
                    text
                    value
                    type
                }
                created_at
                updated_at
            }
        }
        """
        
        variables = {
            "item_id": item_id
        }
        
        result = self.execute_query(query, variables)
        
        if ("data" in result and 
            "items" in result["data"] and 
            result["data"]["items"] and 
            len(result["data"]["items"]) > 0):
            return result["data"]["items"][0]
        
        return None
    
    def create_item(
        self, 
        board_id: str, 
        item_name: str, 
        column_values: Optional[Dict[str, Any]] = None,
        group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new item on a board.
        
        Args:
            board_id: Board ID
            item_name: Item name
            column_values: Column values for the new item
            group_id: Group ID to place the item in
            
        Returns:
            Created item data
        """
        query = """
        mutation ($board_id: ID!, $item_name: String!, $column_values: JSON, $group_id: String) {
            create_item (
                board_id: $board_id,
                item_name: $item_name,
                column_values: $column_values,
                group_id: $group_id
            ) {
                id
                name
                column_values {
                    id
                    title
                    text
                    value
                }
            }
        }
        """
        
        variables = {
            "board_id": board_id,
            "item_name": item_name
        }
        
        if column_values:
            # Convert dict to JSON string
            variables["column_values"] = json.dumps(column_values)
            
        if group_id:
            variables["group_id"] = group_id
            
        result = self.execute_query(query, variables)
        
        if "data" in result and "create_item" in result["data"]:
            return result["data"]["create_item"]
        
        raise APIError(
            message="Failed to create item",
            error_code=ErrorCodes.API_SERVER_ERROR,
            response_body=json.dumps(result, indent=2)
        )
    
    def update_item(
        self, 
        item_id: str, 
        item_name: Optional[str] = None,
        column_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing item.
        
        Args:
            item_id: Item ID
            item_name: New item name (optional)
            column_values: New column values (optional)
            
        Returns:
            Updated item data
        """
        # Build the mutation based on parameters
        mutation_parts = ["mutation ("]
        variables_dict = {"item_id": item_id}
        
        if item_name is not None:
            mutation_parts.append("$item_id: ID!, $item_name: String!")
            variables_dict["item_name"] = item_name
        else:
            mutation_parts.append("$item_id: ID!")
            
        if column_values is not None:
            if item_name is not None:
                mutation_parts.append(", $column_values: JSON")
            else:
                mutation_parts.append("$item_id: ID!, $column_values: JSON")
            variables_dict["column_values"] = json.dumps(column_values)
            
        mutation_parts.append(") {")
        
        # Build the mutation arguments
        mutation_parts.append("change_item_values (")
        mutation_parts.append("item_id: $item_id")
        
        if item_name is not None:
            mutation_parts.append(", item_name: $item_name")
            
        if column_values is not None:
            mutation_parts.append(", column_values: $column_values")
            
        mutation_parts.append(") {")
        mutation_parts.append("id")
        mutation_parts.append("name")
        mutation_parts.append("column_values {")
        mutation_parts.append("id")
        mutation_parts.append("title")
        mutation_parts.append("text")
        mutation_parts.append("value")
        mutation_parts.append("}")
        mutation_parts.append("}")
        mutation_parts.append("}")
        
        query = "\n".join(mutation_parts)
        
        result = self.execute_query(query, variables_dict)
        
        if "data" in result and "change_item_values" in result["data"]:
            return result["data"]["change_item_values"]
        
        raise APIError(
            message="Failed to update item",
            error_code=ErrorCodes.API_SERVER_ERROR,
            response_body=json.dumps(result, indent=2)
        )
    
    def delete_item(self, item_id: str) -> bool:
        """
        Delete an item.
        
        Args:
            item_id: Item ID
            
        Returns:
            True if successful, False otherwise
        """
        query = """
        mutation ($item_id: ID!) {
            delete_item (item_id: $item_id) {
                id
            }
        }
        """
        
        variables = {
            "item_id": item_id
        }
        
        result = self.execute_query(query, variables)
        
        return "data" in result and "delete_item" in result["data"] 