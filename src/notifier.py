import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

IMPORTANCE_COLOR = {"high": "#dc2626", "medium": "#d97706", "low": "#6b7280"}
IMPORTANCE_LABEL = {"high": "重要", "medium": "通常", "low": "参考"}


def _build_html(articles: list[dict]) -> str:
    importance_order = {"high": 0, "medium": 1, "low": 2}
    sorted_articles = sorted(
        articles,
        key=lambda x: (importance_order.get(x["importance"], 1), x["company_name"]),
    )

    rows = ""
    for a in sorted_articles:
        color = IMPORTANCE_COLOR.get(a["importance"], "#6b7280")
        label = IMPORTANCE_LABEL.get(a["importance"], "通常")
        summary_html = (
            f"<p style='color:#555;margin:4px 0 0;font-size:13px;'>{a['summary']}</p>"
            if a["summary"]
            else ""
        )
        rows += f"""
        <tr>
          <td style='padding:12px 8px;border-bottom:1px solid #eee;vertical-align:top;white-space:nowrap;'>
            <span style='background:{color};color:#fff;border-radius:4px;padding:2px 6px;font-size:11px;font-weight:bold;'>{label}</span>
          </td>
          <td style='padding:12px 8px;border-bottom:1px solid #eee;vertical-align:top;white-space:nowrap;font-size:14px;'>
            {a['company_name']}<br>
            <span style='color:#888;font-size:12px;'>{a['company_code']} | {a['source']}</span>
          </td>
          <td style='padding:12px 8px;border-bottom:1px solid #eee;font-size:14px;'>
            <a href='{a['url']}' style='color:#1d4ed8;text-decoration:none;font-weight:500;'>{a['title']}</a>
            {summary_html}
          </td>
        </tr>"""

    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:'Hiragino Sans','Meiryo',sans-serif;background:#f9fafb;padding:20px;">
  <div style="max-width:900px;margin:0 auto;background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);">
    <div style="background:#1e3a5f;color:#fff;padding:16px 24px;border-radius:8px 8px 0 0;">
      <h1 style="margin:0;font-size:18px;">企業ニュース・開示情報モニタリング</h1>
      <p style="margin:4px 0 0;opacity:.8;font-size:13px;">{now} 時点 | {len(articles)}件の新着情報</p>
    </div>
    <div style="padding:16px 24px;">
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="background:#f1f5f9;">
            <th style="padding:8px;text-align:left;font-size:12px;color:#64748b;">重要度</th>
            <th style="padding:8px;text-align:left;font-size:12px;color:#64748b;">企業</th>
            <th style="padding:8px;text-align:left;font-size:12px;color:#64748b;">タイトル / 要約</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <div style="padding:12px 24px;background:#f8fafc;border-radius:0 0 8px 8px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;">
      Corporate News Monitor による自動送信
    </div>
  </div>
</body></html>"""


def send_email(articles: list[dict]) -> None:
    if not articles:
        return

    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    email_to = os.environ["EMAIL_TO"]

    high_count = sum(1 for a in articles if a.get("importance") == "high")
    prefix = "[重要]" if high_count > 0 else "[通常]"
    subject = (
        f"{prefix} 企業ニュース {len(articles)}件"
        f"（重要{high_count}件） - {datetime.now().strftime('%m/%d %H:%M')}"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = email_to
    msg.attach(MIMEText(_build_html(articles), "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        print(f"メール送信完了 → {email_to} ({len(articles)}件)")
