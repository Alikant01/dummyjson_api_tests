"API тесты для DummyJSON"
"Тестирование эндпоинтов авторизации и корзины"

import requests
import pytest

# URL
BASE_URL = "https://dummyjson.com"
AUTH_LOGIN_URL = f"{BASE_URL}/auth/login"
AUTH_ME_URL = f"{BASE_URL}/auth/me"
CARTS_URL = f"{BASE_URL}/carts"

# Тестовые данные
TEST_USER = {
    "username": "emilys",
    "password": "emilyspass"
}


#
@pytest.fixture(scope="module")
def auth_token():
    "Фикстура для получения токена авторизации"
    print("\n[SETUP] Авторизация пользователя...")
    response = requests.post(AUTH_LOGIN_URL, json=TEST_USER)
    assert response.status_code == 200, "Не удалось получить токен"
    token = response.json().get("accessToken")
    print(f"[SETUP] Токен получен: {token[:20]}...")
    return token


@pytest.fixture(scope="module")
def user_id(auth_token):
    "Фикстура для получения ID пользователя."
    print("[SETUP] Получение данных пользователя...")
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(AUTH_ME_URL, headers=headers)
    assert response.status_code == 200, "Не удалось получить данные пользователя"
    user_id = response.json().get("id")
    print(f"[SETUP] ID пользователя: {user_id}")
    return user_id


@pytest.fixture(scope="module")
def user_cart_id(user_id):
    "Фикстура для получения ID первой корзины пользователя."
    print("[SETUP] Получение корзины пользователя...")
    response = requests.get(f"{CARTS_URL}/user/{user_id}")
    assert response.status_code == 200, "Не удалось получить корзину"

    carts = response.json().get("carts", [])
    if not carts:
        pytest.skip("У пользователя нет корзин, тест пропущен")

    cart_id = carts[0]["id"]
    print(f"[SETUP] ID корзины: {cart_id}")
    return cart_id


# Тесты
def test_01_successful_login():
    "Тест 1: Успешная авторизация"
    print("\n[TEST 1] Успешная авторизация")
    response = requests.post(AUTH_LOGIN_URL, json=TEST_USER)

    assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"

    json_response = response.json()
    assert "accessToken" in json_response, "В ответе отсутствует accessToken"
    assert json_response.get("username") == TEST_USER["username"], "Неверный username"

    print(f"[PASS] Токен получен: {json_response['accessToken'][:20]}...")


def test_02_unsuccessful_login():
    "Тест 2: Неуспешная авторизация с неверным паролем"
    print("\n[TEST 2] Неуспешная авторизация (неверный пароль)")
    invalid_data = {"username": "emilys", "password": "wrongpassword"}
    response = requests.post(AUTH_LOGIN_URL, json=invalid_data)

    assert response.status_code == 400, f"Ожидался 400, получен {response.status_code}"

    json_response = response.json()
    assert "message" in json_response or "error" in json_response, \
        "В ответе отсутствует сообщение об ошибке"

    print(f"[PASS] Ошибка получена: {json_response.get('message', json_response.get('error', 'Неизвестная ошибка'))}")


def test_03_get_current_user_with_token(auth_token):
    "Тест 3: Получение данных пользователя с токеном"
    print("\n[TEST 3] Получение данных пользователя с токеном")
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(AUTH_ME_URL, headers=headers)

    assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"

    json_response = response.json()
    assert json_response.get("username") == TEST_USER["username"], "Неверный username"
    assert "id" in json_response, "В ответе отсутствует id"
    assert "email" in json_response, "В ответе отсутствует email"

    print(f"[PASS] Получены данные для пользователя: {json_response['username']} (ID: {json_response['id']})")


def test_04_get_current_user_without_token():
    "Тест 4: Получение данных пользователя без токена (ожидается ошибка)"
    print("\n[TEST 4] Получение данных пользователя без токена (ожидается ошибка)")
    response = requests.get(AUTH_ME_URL)

    assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}"

    json_response = response.json()
    assert "message" in json_response, "В ответе отсутствует сообщение об ошибке"

    print(f"[PASS] Доступ запрещен: {json_response.get('message')}")


def test_05_get_user_carts(user_id):
    "Тест 5: Получение корзин пользователя"
    print(f"\n[TEST 5] Получение корзин пользователя (ID: {user_id})")
    response = requests.get(f"{CARTS_URL}/user/{user_id}")

    assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"

    json_response = response.json()
    assert "carts" in json_response, "В ответе отсутствует поле carts"
    assert isinstance(json_response["carts"], list), "carts должен быть списком"
    assert "total" in json_response, "В ответе отсутствует поле total"

    print(f"[PASS] Получено корзин: {len(json_response['carts'])}")


def test_06_get_cart_by_id(user_cart_id):
    "Тест 6: Получение корзины по ID"
    print(f"\n[TEST 6] Получение корзины по ID: {user_cart_id}")
    response = requests.get(f"{CARTS_URL}/{user_cart_id}")

    assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"

    json_response = response.json()
    assert json_response.get(
        "id") == user_cart_id, f"ID корзины не совпадает. Ожидался {user_cart_id}, получен {json_response.get('id')}"
    assert "products" in json_response, "В ответе отсутствуют продукты"
    assert "total" in json_response, "В ответе отсутствует общая сумма"

    print(f"[PASS] Получена корзина {user_cart_id} с {json_response.get('totalProducts', 0)} продуктами")


def test_07_create_cart(user_id):
    "Тест 7: Создание корзины"
    print(f"\n[TEST 7] Создание корзины для пользователя {user_id}")
    payload = {
        "userId": user_id,
        "products": [
            {"id": 144, "quantity": 2},
            {"id": 98, "quantity": 1}
        ]
    }
    response = requests.post(f"{CARTS_URL}/add", json=payload)

    assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"

    json_response = response.json()
    assert json_response.get("userId") == user_id, "userId не совпадает"
    assert json_response.get("id") is not None, "Не создан ID корзины"
    assert "total" in json_response, "Отсутствует поле total"
    assert json_response.get("totalProducts") == 2, "Неверное количество продуктов"

    print(f"[PASS] Корзина создана с ID: {json_response['id']}, Сумма: {json_response['total']}")


def test_08_update_cart(user_cart_id):
    "Тест 8: Обновление корзины"
    print(f"\n[TEST 8] Обновление корзины {user_cart_id} (добавление продукта)")
    payload = {
        "merge": True,
        "products": [
            {"id": 1, "quantity": 1}
        ]
    }
    response = requests.put(f"{CARTS_URL}/{user_cart_id}", json=payload)

    assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"

    json_response = response.json()
    assert json_response.get("id") == user_cart_id, "ID корзины изменился"
    assert json_response.get("totalQuantity") > 0, "Количество товаров должно быть больше 0"
    assert "products" in json_response, "В ответе отсутствуют продукты"

    print(f"[PASS] Корзина обновлена. Всего товаров: {json_response['totalQuantity']}")


def test_09_delete_cart(user_cart_id):
    "Тест 9: Удаление корзины"
    print(f"\n[TEST 9] Удаление корзины {user_cart_id}")
    response = requests.delete(f"{CARTS_URL}/{user_cart_id}")

    assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"

    json_response = response.json()
    assert json_response.get("isDeleted") is True, "isDeleted должен быть True"
    assert "deletedOn" in json_response, "Отсутствует дата удаления"

    print(f"[PASS] Корзина удалена в {json_response['deletedOn']}")


def test_10_negative_get_nonexistent_cart():
    "Тест 10: Негативный сценарий - запрос несуществующей корзины"
    print("\n[TEST 10] Негативный тест: запрос несуществующей корзины")
    response = requests.get(f"{CARTS_URL}/999999")

    assert response.status_code == 404, f"Ожидался 404, получен {response.status_code}"

    json_response = response.json()
    assert "message" in json_response, "В ответе отсутствует сообщение об ошибке"

    print(f"[PASS] Ошибка 404 получена: {json_response.get('message')}")