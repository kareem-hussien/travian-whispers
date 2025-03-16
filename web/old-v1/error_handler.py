# standardize API error responses
def api_response(success, message, data=None, status_code=200):
    """
    Create a standardized API response.
    
    Args:
        success (bool): Whether the request was successful
        message (str): Response message
        data (any, optional): Response data
        status_code (int, optional): HTTP status code
        
    Returns:
        tuple: (response_json, status_code)
    """
    response = {
        'success': success,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code