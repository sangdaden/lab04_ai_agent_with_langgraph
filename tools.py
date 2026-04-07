import logging
from typing import Any

from langchain_core.tools import tool

# MOCK DATA - Dữ liệu gia lập hệ thống du lịch
# Lưu ý: Giá cả có logic (VD: cuối tuần đắt hơn, hạng cao hơn đắt hơn)
# Sinh viên cần đọc hiểu data để debug test cases.
#

FLIGHTS_DB = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1_450_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2_800_000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1_200_000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1_350_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "price": 1_100_000, "class": "economy"},
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "price": 1_600_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "price": 950_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "12:00", "arrival": "14:10", "price": 1_300_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10", "price": 3_200_000, "class": "business"},
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "VietJet Air", "departure": "09:00", "arrival": "10:20", "price": 1_300_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "13:00", "arrival": "14:20", "price": 780_000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00", "price": 1_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "15:00", "arrival": "16:00", "price": 650_000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "stars": 5, "price_per_night": 1_800_000, "area": "Mỹ Khê", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "price_per_night": 1_200_000, "area": "Mỹ Khê", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "price_per_night": 650_000, "area": "Sơn Trà", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "price_per_night": 250_000, "area": "Hải Châu", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350_000, "area": "An Thượng", "rating": 4.7},
    ],
    "Phú Quốc": [
        {"name": "Vinpearl Resort", "stars": 5, "price_per_night": 3_500_000, "area": "Bãi Dài", "rating": 4.4},
        {"name": "Sol by Meliá", "stars": 4, "price_per_night": 1_500_000, "area": "Bãi Trường", "rating": 4.2},
        {"name": "Lahana Resort", "stars": 3, "price_per_night": 800_000, "area": "Dương Đông", "rating": 4.0},
        {"name": "Station Hostel", "stars": 2, "price_per_night": 200_000, "area": "Dương Đông", "rating": 4.5},
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "stars": 5, "price_per_night": 2_800_000, "area": "Quận 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "price_per_night": 1_400_000, "area": "Quận 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "price_per_night": 550_000, "area": "Quận 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "price_per_night": 180_000, "area": "Quận 1", "rating": 4.6},
    ],
}

logger = logging.getLogger(__name__)

Flight = dict[str, Any]
Hotel = dict[str, Any]


def _format_vnd(amount: int) -> str:
    return f"{amount:,}".replace(",", ".") + "đ"


def _prettify_label(label: str) -> str:
    return label.replace("_", " ").strip().capitalize()

@tool
def search_flights(origin: str, destination: str) -> str:
    """
    Tìm kiếm chuyến bay giữa hai thành phố.
    Tham số:
    - origin: Thành phố khởi hành (VD: "Hà Nội", "Hồ Chí Minh")
    - destination: Thành phố đến (VD: "Đà Nẵng", "Phú Quốc")
    Trả về: Danh sách chuyến bay phù hợp với yêu cầu, mỗi chuyến bay bao gồm:
    Nếu không tìm thấy chuyến bay nào, trả về thông báo không có chuyến.
    """
    try:
        origin = origin.strip()
        destination = destination.strip()

        if not origin or not destination:
            return "Vui lòng cung cấp đầy đủ điểm đi và điểm đến."

        flights: list[Flight] | None = FLIGHTS_DB.get((origin, destination))
        reverse_flights: list[Flight] | None = FLIGHTS_DB.get((destination, origin))

        if flights:
            lines = [f"Các chuyến bay từ {origin} đến {destination}:"]
        elif reverse_flights:
            flights = reverse_flights
            lines = [
                f"Không có chuyến bay chiều {origin} → {destination}.",
                f"Hiện có các chuyến chiều ngược lại {destination} → {origin}:"
            ]
        else:
            return f"Không tìm thấy chuyến bay từ {origin} đến {destination}."

        sorted_flights = sorted(flights, key=lambda flight: int(flight["price"]))
        for idx, flight in enumerate(sorted_flights, start=1):
            lines.append(
                f"{idx}. {flight['airline']} | {flight['departure']} - {flight['arrival']} | "
                f"{flight['class']} | {_format_vnd(int(flight['price']))}"
            )

        return "\n".join(lines)
    except Exception:
        logger.exception("search_flights failed for origin=%s destination=%s", origin, destination)
        return "Xin lỗi, hiện có lỗi khi tìm chuyến bay. Bạn vui lòng thử lại sau."

@tool
def search_hotels(city: str, max_price_per_night: int = 99_999_999) -> str:
    """
    Tìm kiếm khách sạn tại một thành phố, có thể lọc theo giá tối đa mỗi đêm.
    Tham số:
    - city: tên thành phố (VD: 'Đà Nẵng', 'Phú Quốc', 'Hồ Chí Minh')
    - max_price_per_night: giá tối đa mỗi đêm (VNĐ) , mặc định không giới hạn
    Trả về danh sách khách sạn phù hợp với tên, số sao, gia, khu vực,
    rating.
    """
    try:
        city = city.strip()
        if not city:
            return "Vui lòng cung cấp tên thành phố để tìm khách sạn."

        hotels: list[Hotel] | None = HOTELS_DB.get(city)
        if not hotels:
            return f"Không tìm thấy dữ liệu khách sạn cho {city}."

        filtered_hotels = [
            hotel for hotel in hotels
            if int(hotel["price_per_night"]) <= max_price_per_night
        ]
        filtered_hotels.sort(
            key=lambda hotel: (-float(hotel["rating"]), int(hotel["price_per_night"]))
        )

        if not filtered_hotels:
            return (
                f"Không tìm thấy khách sạn tại {city} với giá dưới "
                f"{_format_vnd(max_price_per_night)}/đêm. Hãy thử tăng ngân sách."
            )

        lines = [f"Khách sạn phù hợp tại {city}:"]
        for idx, hotel in enumerate(filtered_hotels, start=1):
            lines.append(
                f"{idx}. {hotel['name']} | {hotel['stars']}⭐ | {hotel['area']} | "
                f"rating {hotel['rating']} | {_format_vnd(int(hotel['price_per_night']))}/đêm"
            )

        return "\n".join(lines)
    except Exception:
        logger.exception("search_hotels failed for city=%s max_price_per_night=%s", city, max_price_per_night)
        return "Xin lỗi, hiện có lỗi khi tìm khách sạn. Bạn vui lòng thử lại sau."

@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính toán ngân sách còn lại sau khi trừ các khoản chi phí.
    Tham số:
    - total_budget: tổng ngân sách ban đầu (VNĐ)
    - expenses: chuỗi mô tả các khoản chi, mỗi khoản cách nhau bởi dấu phẩy,
      định dạng 'tên_khoản:số_tiền' (VD:
      'vé_máy_bay:890000, khách_sạn:650000')
    Trả về bảng chi tiết các khoản chi và số tiền còn lại.
    Nếu vượt ngân sách, cảnh báo rõ ràng số tiền thiếu.
    """
    try:
        if total_budget < 0:
            return "Ngân sách ban đầu không hợp lệ. Vui lòng nhập số tiền >= 0."

        parsed_expenses: dict[str, int] = {}
        cleaned_expenses = expenses.strip()

        if cleaned_expenses:
            for raw_item in cleaned_expenses.split(","):
                item = raw_item.strip()
                if not item:
                    continue

                if ":" not in item:
                    return (
                        "Expenses format không hợp lệ. Vui lòng dùng dạng "
                        "'ten_khoan:so_tien,ten_khoan:so_tien'."
                    )

                name, amount_text = item.split(":", 1)
                name = name.strip()
                amount_text = amount_text.strip().replace(".", "").replace("_", "")

                if not name or not amount_text.isdigit():
                    return (
                        "Expenses format không hợp lệ. Vui lòng dùng dạng "
                        "'ten_khoan:so_tien,ten_khoan:so_tien'."
                    )

                parsed_expenses[name] = parsed_expenses.get(name, 0) + int(amount_text)

        total_expense = sum(parsed_expenses.values())
        remaining = total_budget - total_expense

        lines = ["Bảng chi phí:"]
        if parsed_expenses:
            for name, amount in parsed_expenses.items():
                lines.append(f"- {_prettify_label(name)}: {_format_vnd(amount)}")
        else:
            lines.append("- Chưa có khoản chi nào")

        lines.append("---")
        lines.append(f"Tổng chi: {_format_vnd(total_expense)}")
        lines.append(f"Ngân sách: {_format_vnd(total_budget)}")

        if remaining >= 0:
            lines.append(f"Còn lại: {_format_vnd(remaining)}")
        else:
            lines.append(f"Còn lại: -{_format_vnd(abs(remaining))}")
            lines.append(f"Vượt ngân sách {_format_vnd(abs(remaining))}! Cần điều chỉnh.")

        return "\n".join(lines)
    except Exception:
        logger.exception("calculate_budget failed for total_budget=%s expenses=%s", total_budget, expenses)
        return "Xin lỗi, hiện có lỗi khi tính ngân sách. Bạn vui lòng thử lại sau."
