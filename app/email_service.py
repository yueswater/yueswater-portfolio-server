import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


async def send_quote_confirmation(
    to_email: str,
    client_name: str,
    service_name: str,
    budget_min: float,
    budget_max: float | None,
    expected_completion: str,
    quote_number: str,
):
    budget_str = f"NT$ {budget_min:,.0f}"
    if budget_max:
        budget_str += f" ~ NT$ {budget_max:,.0f}"
    else:
        budget_str += " 起"

    html = f"""\
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; background: #f3f3f3; padding: 40px;">
      <div style="background: #020202; color: #f3f3f3; padding: 32px; margin-bottom: 24px;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">ANTHONY.</h1>
      </div>
      <div style="background: #fff; padding: 32px; border: 1px solid #e5e5e5;">
        <h2 style="margin: 0 0 16px; font-size: 20px; font-weight: 700;">您好，{client_name}！</h2>
        <p style="color: #555; line-height: 1.8; margin: 0 0 8px;">
          感謝您的報價需求，我已收到您的表單。以下是您提交的摘要：
        </p>
        <p style="color: #020202; font-size: 18px; font-weight: 700; margin: 0 0 24px; letter-spacing: 1px;">
          報價編號：{quote_number}
        </p>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
          <tr style="border-bottom: 1px solid #e5e5e5;">
            <td style="padding: 12px 0; font-weight: 600; width: 120px;">選擇服務</td>
            <td style="padding: 12px 0; color: #555;">{service_name}</td>
          </tr>
          <tr style="border-bottom: 1px solid #e5e5e5;">
            <td style="padding: 12px 0; font-weight: 600;">預算範圍</td>
            <td style="padding: 12px 0; color: #555;">{budget_str}</td>
          </tr>
          <tr>
            <td style="padding: 12px 0; font-weight: 600;">期望完成</td>
            <td style="padding: 12px 0; color: #555;">{expected_completion}</td>
          </tr>
        </table>
        <p style="color: #555; line-height: 1.8; margin: 0;">
          我會盡快審閱您的需求並回覆您。如有任何問題，歡迎直接回覆此信件。
        </p>
      </div>
      <p style="text-align: center; color: #999; font-size: 12px; margin-top: 24px;">
        © 2026 Anthony. All rights reserved.
      </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"【Anthony】已收到您的報價需求 {quote_number} — {service_name}"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        start_tls=True,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
    )


async def send_case_created_email(
    to_email: str,
    client_name: str,
    case_number: str,
    quote_number: str | None,
):
    html = f"""\
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; background: #f3f3f3; padding: 40px;">
      <div style="background: #020202; color: #f3f3f3; padding: 32px; margin-bottom: 24px;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">ANTHONY.</h1>
      </div>
      <div style="background: #fff; padding: 32px; border: 1px solid #e5e5e5;">
        <h2 style="margin: 0 0 16px; font-size: 20px; font-weight: 700;">您好，{client_name}！</h2>
        <p style="color: #555; line-height: 1.8; margin: 0 0 8px;">
          您的案件已正式成立，以下是案件資訊：
        </p>
        <p style="color: #020202; font-size: 18px; font-weight: 700; margin: 0 0 24px; letter-spacing: 1px;">
          案件編號：{case_number}
        </p>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
          <tr>
            <td style="padding: 12px 0; font-weight: 600; width: 120px;">報價編號</td>
            <td style="padding: 12px 0; color: #555;">{quote_number or '—'}</td>
          </tr>
        </table>
        <p style="color: #555; line-height: 1.8; margin: 0;">
          我會盡快開始處理您的案件，如有任何問題，歡迎直接回覆此信件或透過聊天室聯繫。
        </p>
      </div>
      <p style="text-align: center; color: #999; font-size: 12px; margin-top: 24px;">
        © 2026 Anthony. All rights reserved.
      </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"【Anthony】案件已成立 {case_number}"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        start_tls=True,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
    )


async def send_chat_notification(
    to_email: str,
    recipient_name: str,
    sender_label: str,
    preview: str,
    quote_number: str,
):
    from html import escape
    html = f"""\
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; background: #f3f3f3; padding: 40px;">
      <div style="background: #020202; color: #f3f3f3; padding: 32px; margin-bottom: 24px;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">ANTHONY.</h1>
      </div>
      <div style="background: #fff; padding: 32px; border: 1px solid #e5e5e5;">
        <h2 style="margin: 0 0 16px; font-size: 20px; font-weight: 700;">您好，{escape(recipient_name)}！</h2>
        <p style="color: #555; line-height: 1.8; margin: 0 0 16px;">
          <strong>{escape(sender_label)}</strong> 在聊天室中發送了新訊息：
        </p>
        <div style="background: #f9f9f9; border-left: 4px solid #020202; padding: 16px; margin: 0 0 24px;">
          <p style="margin: 0; color: #333; font-size: 15px; line-height: 1.6;">{escape(preview)}</p>
        </div>
        <p style="color: #999; font-size: 13px; margin: 0 0 8px;">
          報價編號：{escape(quote_number)}
        </p>
        <a href="https://portfolio.yueswater.com/chat" style="display: inline-block; background: #020202; color: #f3f3f3; padding: 12px 32px; text-decoration: none; font-size: 14px; font-weight: 600; letter-spacing: 1px; margin-top: 16px;">
          前往聊天室
        </a>
      </div>
      <p style="text-align: center; color: #999; font-size: 12px; margin-top: 24px;">
        © 2026 Anthony. All rights reserved.
      </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"【Anthony】{escape(sender_label)} 發送了新訊息 — {escape(quote_number)}"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        start_tls=True,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
    )
