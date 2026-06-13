"""
calorie_calc.py
food_calories.json を参照し、メニュー（食品名＋グラム）から自動でカロリーを計算する。

使い方:
    from calorie_calc import CalorieDB
    db = CalorieDB("food_calories.json")
    db.calc("鶏むね肉(皮なし)", 200)   # -> 210.0 (kcal)
    db.calc_menu([("白米ごはん", 150), ("納豆", 45), ("卵", 50)])  # 1食まとめて
"""

import json
import unicodedata
from pathlib import Path


class CalorieDB:
    def __init__(self, path: str = "food_calories.json"):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.meta = data["meta"]
        self.foods = data["foods"]
        # 別名(エイリアス)→正式名 の逆引き表を起動時に1回だけ構築（高速化）
        self._alias_map = {}
        for name, info in self.foods.items():
            self._alias_map[self._norm(name)] = name
            for a in info.get("aliases", []):
                self._alias_map[self._norm(a)] = name

    @staticmethod
    def _norm(s: str) -> str:
        # 全角半角・大文字小文字・空白を吸収して表記ゆれに強くする
        return unicodedata.normalize("NFKC", s).strip().lower().replace(" ", "")

    def resolve(self, query: str):
        """入力された食品名を正式名に解決。見つからなければ None。"""
        return self._alias_map.get(self._norm(query))

    def calc(self, food: str, grams: float) -> float:
        """単品のカロリーを返す（kcal、小数1桁）"""
        name = self.resolve(food)
        if name is None:
            raise KeyError(f"未登録の食品: '{food}'（aliasに追加してください）")
        kcal = self.foods[name]["kcal_per_100g"] * grams / 100
        return round(kcal, 1)

    def calc_menu(self, items: list[tuple[str, float]]) -> dict:
        """1食分のメニューをまとめて計算。明細＋合計を返す。"""
        details, total, unknown = [], 0.0, []
        for food, grams in items:
            try:
                kcal = self.calc(food, grams)
                details.append({"食品": self.resolve(food), "g": grams, "kcal": kcal})
                total += kcal
            except KeyError:
                unknown.append(food)
        return {"明細": details, "合計kcal": round(total, 1), "未登録": unknown}


if __name__ == "__main__":
    db = CalorieDB("food_calories.json")

    # 単品
    print(db.calc("鶏むね肉(皮なし)", 200), "kcal")  # 210.0

    # エイリアス（表記ゆれ）も解決される
    print(db.calc("ごはん", 150), "kcal")            # 234.0
    print(db.calc("ヨーグルト", 100), "kcal")        # 56.0

    # 1食まとめて（朝食の例）
    breakfast = [("白米ごはん", 150), ("納豆", 45), ("卵", 50), ("味噌", 18)]
    result = db.calc_menu(breakfast)
    print(json.dumps(result, ensure_ascii=False, indent=2))
