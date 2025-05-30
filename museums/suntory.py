import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.suntory.co.jp"

def get_suntory_exhibitions():
    url = f"{BASE_URL}/sma/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    res = requests.get(url, headers=headers)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    exhibitions = []

    # デバッグ情報を出力
    print("=== デバッグ情報 ===")
    print("1. ページの内容確認:")
    print(soup.prettify()[:1000])  # 最初の1000文字を表示

    # 「開催中の展覧会」という<p>タグを探す
    target_p = soup.find("p", string="開催中の展覧会")
    print("\n2. 開催中の展覧会タグの検索結果:")
    print(f"target_p: {target_p}")

    if target_p:
        # 次の div.exhibition_img を探す（兄弟や親から探索）
        exb_img_div = target_p.find_next("div", class_="exhibition_img")
        print("\n3. exhibition_imgの検索結果:")
        print(f"exb_img_div: {exb_img_div}")

        if exb_img_div:
            a_tag = exb_img_div.find("a", href=True)
            print("\n4. リンクの検索結果:")
            print(f"a_tag: {a_tag}")

            if a_tag:
                exb = {}

                # タイトルは img.alt から取得
                img_tag = a_tag.find("img", alt=True)
                if img_tag:
                    exb["title"] = img_tag["alt"]

                # 詳細ページURL
                detail_url = BASE_URL + a_tag["href"]
                exb["detail_url"] = detail_url

                # 詳細ページへアクセスし、会期・料金を取得
                try:
                    detail_res = requests.get(detail_url, headers=headers)
                    detail_res.encoding = detail_res.apparent_encoding
                    detail_soup = BeautifulSoup(detail_res.text, "html.parser")

                    # 会期
                    date_text = detail_soup.find(string=re.compile(r"(会期|開催期間)"))
                    if date_text:
                        parent = date_text.find_parent(["p", "div", "section", "li", "td"])
                        if parent:
                            exb["date"] = parent.get_text(strip=True).replace("会期", "").replace("開催期間", "").strip()

                    # 料金
                    fee_texts = detail_soup.find_all(string=re.compile(r"(観覧料|料金|入場料|前売)"))
                    for text in fee_texts:
                        parent = text.find_parent(["p", "div", "section", "li", "td"])
                        if parent:
                            fee_text = parent.get_text(strip=True)

                            # 大人料金
                            normal_match = re.search(r"(一般|大人)[^\d]{0,5}([\d,]+)円", fee_text)
                            if normal_match:
                                exb["adult_fee"] = normal_match.group(2) + "円"

                            # 前売り大人料金
                            pre_match = re.search(r"(前売[^\d]{0,5})(一般|大人)?[^\d]{0,5}([\d,]+)円", fee_text)
                            if pre_match:
                                exb["pre_sale_adult_fee"] = pre_match.group(3) + "円"

                            if "adult_fee" in exb and "pre_sale_adult_fee" in exb:
                                break
                except Exception as e:
                    exb["adult_fee"] = "取得エラー"
                    exb["error"] = str(e)

                exhibitions.append(exb)

    return exhibitions

if __name__ == "__main__":
    exhibitions = get_suntory_exhibitions()
    if not exhibitions:
        print("\n現在会期中の展覧会はありません。")
    else:
        for idx, exb in enumerate(exhibitions, 1):
            print(f"\n◉ 企画展 {idx}")
            print(f"　タイトル: {exb.get('title')}")
            print(f"　会期: {exb.get('date', '情報なし')}")
            print(f"　大人料金: {exb.get('adult_fee', '情報なし')}")
            print(f"　前売り大人料金: {exb.get('pre_sale_adult_fee', '情報なし')}")
            print(f"　詳細ページ: {exb.get('detail_url')}")
