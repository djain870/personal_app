from fastapi import Request


def get_current_user(request: Request):
    user = request.cookies.get("user")
    if not user or user == "None":
        return None
    return user
