from inflection import dasherize, underscore


def get_scoped_construct_id(construct_id: str) -> str:
    """Generate a scoped construct ID by appending 'Name' to the given construct_id.

    Args:
        construct_id (str): The base ID for the construct.

    Returns:
        str: The scoped construct ID.
    """
    return f"{construct_id}Name"


def get_resource_prefix(resource_id: str) -> str:
    """Generate a resource prefix by converting the resource_id to a dasherized and underscored format.

    Args:
        resource_id (str): The base ID for the resource.

    Returns:
        str: The formatted resource prefix.
    """
    return f"{dasherize(underscore(resource_id))}-"
