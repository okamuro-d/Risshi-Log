from smartcard.System import readers
from smartcard.util import toHexString
import ndef
import config #
import winsound
import time

# config.py からベースURLを取得
BASE_URL = config.STUDENT_URL_BASE

def write_ndef(connection, url):
    """NTAG21x系のカードにURLを書き込む (APDU直接送信)"""
    try:
        # 1. NDEFメッセージ（URL）を作成し、純粋な数字のリストに変換
        record = ndef.UriRecord(url)
        message_bytes = b"".join(ndef.message_encoder([record]))
        message = [int(b) for b in message_bytes] # ここで1バイトずつの整数のリストにする
        
        # 2. TLV形式にラップ (0x03=NDEF, 長さ, ペイロード, 0xFE=終端)
        tlv = [0x03, len(message)] + message + [0xFE]
        
        # 4バイト単位にパディング
        while len(tlv) % 4 != 0:
            tlv.append(0x00)
        
        # 3. データの書き込み (Page 4以降)
        print(f"🔗 書き込み中...")
        for i in range(0, len(tlv), 4):
            page = 4 + (i // 4)
            data = tlv[i:i+4]
            # APDU: [FF, D6, 00, ページ番号, 04, データ(4バイト)]
            cmd = [0xFF, 0xD6, 0x00, page, 0x04] + data
            # 応答を確認 (sw1, sw2)
            _, sw1, sw2 = connection.transmit(cmd)
            if sw1 != 0x90:
                print(f"❌ ページ {page} の書き込みに失敗しました。")
                return False
        return True
    except Exception as e:
        print(f"書き込みエラー詳細: {e}")
        return False

def main():
    print("========================================")
    print("   RisshiLog NFC 自動書き込み (Native PCSC)")
    print("========================================")
    print(f"ベースURL: {BASE_URL}")
    print("カードリーダーを待機中...")

    r = readers() #
    if not r:
        print("❌ エラー: リーダーが見つかりません。")
        return

    connection = r[0].createConnection()
    last_idm = None

    while True:
        try:
            connection.connect()
            # IDmを取得
            data, sw1, sw2 = connection.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
            idm = toHexString(data).replace(" ", "")

            if idm != last_idm:
                print(f"\n💳 カード検知: {idm}")
                target_url = BASE_URL + idm #
                
                if write_ndef(connection, target_url):
                    print(f"✅ 書き込み完了: {target_url}")
                    # 成功音
                    winsound.Beep(2500, 150)
                    winsound.Beep(2500, 150)
                else:
                    winsound.Beep(500, 500) # 失敗音
                
                last_idm = idm
            
            connection.disconnect()
        except Exception:
            last_idm = None
        
        time.sleep(1)

if __name__ == '__main__':
    main()