import json


class OutputParser:

    @staticmethod
    def parse_json(text: str) -> dict:
        """
        Chuyển response của LLM thành Python dict.
        Nếu LLM trả về markdown ```json ... ``` thì tự động loại bỏ.
        """

        clean_json_str = text.strip()

        # Xóa markdown ```json
        if clean_json_str.startswith("```json"):
            clean_json_str = clean_json_str[7:]

        # Xóa markdown ```
        elif clean_json_str.startswith("```"):
            clean_json_str = clean_json_str[3:]

        # Xóa ``` ở cuối
        if clean_json_str.endswith("```"):
            clean_json_str = clean_json_str[:-3]

        clean_json_str = clean_json_str.strip()

        try:
            return json.loads(clean_json_str)

        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM trả về JSON không hợp lệ:\n\n{clean_json_str}"
            ) from e