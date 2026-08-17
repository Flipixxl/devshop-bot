from aiogram.utils.web_app import safe_parse_webapp_init_data


def parse_init_data(token: str, init_data: str):
    if not init_data:
        return None
    try:
        return safe_parse_webapp_init_data(token=token, init_data=init_data)
    except ValueError:
        return None


def get_user_id_from_init_data(token: str, init_data: str) -> int | None:
    data = parse_init_data(token, init_data)
    return data.user.id if data and data.user else None
