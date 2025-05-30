import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.artizon.museum"

def get_artizon_exhibitions():
    url = f"{BASE_URL}/exhibition/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    res = requests.get(url, headers=headers)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    exhibitions = []

    # 「開催中の展覧会」セクションを探す
    current_exhibitions = soup.find("h2", string="開催中の展覧会")
    if current_exhibitions:
        # 次の要素から展覧会情報を取得
        for case in current_exhibitions.find_next_siblings("div", class_="case"):
            exb = {}
            
            # タイトルを取得
            title = case.find("h3", class_="exhibitionBox__title")
            if title:
                exb["title"] = title.get_text(strip=True)
            
            # 会期を取得
            date = case.find("p", class_="exhibitionBox__textDate")
            if date:
                exb["date"] = date.get_text(strip=True)
            
            # 詳細ページのURLを取得
            link = case.find("a", class_="linkBlockHover")
            if link and link.get("href"):
                exb["detail_url"] = BASE_URL + link["href"]
                
                # 詳細ページから料金情報を取得
                try:
                    detail_res = requests.get(exb["detail_url"], headers=headers)
                    detail_res.encoding = detail_res.apparent_encoding
                    detail_soup = BeautifulSoup(detail_res.text, "html.parser")

                    # まずテーブルを探す
                    fee_table = detail_soup.find("table")
                    found_fee = False
                    if fee_table:
                        rows = fee_table.find_all("tr")
                        for row in rows:
                            cells = row.find_all(["th", "td"])
                            if len(cells) >= 2:
                                label = cells[0].get_text(strip=True)
                                value = cells[1].get_text(strip=True)
                                if "一般" in label:
                                    exb["adult_fee"] = value
                                    found_fee = True
                                if "前売" in label and ("一般" in label or "大人" in label):
                                    exb["pre_sale_adult_fee"] = value
                        if found_fee:
                            exhibitions.append(exb)
                            continue
                    # テーブルで見つからなければ、リストや段落も探す
                    fee_texts = detail_soup.find_all(string=re.compile(r"一般|前売"))
                    for text in fee_texts:
                        parent = text.find_parent(["li", "p", "div", "section", "td"])
                        if parent:
                            fee_text = parent.get_text(strip=True)
                            # 一般料金
                            normal_match = re.search(r"一般[^\d]{0,5}([\d,]+)円", fee_text)
                            if normal_match:
                                exb["adult_fee"] = normal_match.group(1) + "円"
                            # 前売り大人料金
                            pre_match = re.search(r"前売[^\d]{0,5}(?:一般|大人)?[^\d]{0,5}([\d,]+)円", fee_text)
                            if pre_match:
                                exb["pre_sale_adult_fee"] = pre_match.group(1) + "円"
                            if "adult_fee" in exb:
                                break
                except Exception as e:
                    exb["adult_fee"] = "取得エラー"
                    exb["error"] = str(e)
            exhibitions.append(exb)

    return exhibitions

if __name__ == "__main__":
    exhibitions = get_artizon_exhibitions()
    if not exhibitions:
        print("\n現在会期中の展覧会はありません。")
    else:
        for idx, exb in enumerate(exhibitions, 1):
            print(f"\n◉ 企画展 {idx}")
            print(f"　タイトル: {exb.get('title')}")
            print(f"　会期: {exb.get('date')}")
            print(f"　大人料金: {exb.get('adult_fee', '情報なし')}")
            print(f"　前売り大人料金: {exb.get('pre_sale_adult_fee', '情報なし')}")
            print(f"　詳細ページ: {exb.get('detail_url')}")
