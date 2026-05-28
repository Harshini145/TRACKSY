"""
Email service — uses Gmail SMTP with an App Password (same concept as NodeMailer).
All emails are sent to the address the user registered with.
"""

try:
  import aiosmtplib
  _AIOSMTP_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
  aiosmtplib = None
  _AIOSMTP_AVAILABLE = False
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import settings


def _is_placeholder(value: str, placeholder: str) -> bool:
    return not value or value.strip().lower() == placeholder.lower()


def _smtp_password() -> str:
    # Gmail app passwords are often copied as four groups with spaces.
    # SMTP expects the 16 characters without spaces.
    return settings.SMTP_PASSWORD.replace(" ", "")


def _validate_smtp_settings() -> None:
    missing = []
    if _is_placeholder(settings.SMTP_USER, "your_gmail@gmail.com"):
        missing.append("SMTP_USER")
    if _is_placeholder(settings.SMTP_PASSWORD, "your_16_char_app_password"):
        missing.append("SMTP_PASSWORD")
    if missing:
        raise RuntimeError(
            "SMTP is not configured. Set "
            + ", ".join(missing)
            + " in .env using your Gmail address and Gmail App Password."
        )


# ── HTML email templates ──────────────────────────────────────────────────────

def _base_template(body_html: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#f4f6fb; margin:0; padding:0; }}
        .wrapper {{ max-width:560px; margin:40px auto; background:#fff; border-radius:12px;
                   box-shadow:0 4px 24px rgba(0,0,0,.08); overflow:hidden; }}
        .header {{ background:linear-gradient(135deg,#6366f1,#8b5cf6); padding:32px 32px 24px; }}
        .header h1 {{ color:#fff; margin:0; font-size:22px; letter-spacing:-.5px; }}
        .header p  {{ color:rgba(255,255,255,.8); margin:4px 0 0; font-size:13px; }}
        .body {{ padding:32px; color:#374151; line-height:1.7; }}
        .highlight {{ background:#f3f4f6; border-left:4px solid #6366f1;
                     padding:14px 18px; border-radius:6px; margin:20px 0; }}
        .amount {{ font-size:28px; font-weight:700; color:#6366f1; }}
        .footer {{ background:#f9fafb; padding:20px 32px; text-align:center;
                  font-size:12px; color:#9ca3af; border-top:1px solid #f3f4f6; }}
        .btn {{ display:inline-block; background:#6366f1; color:#fff; padding:12px 28px;
               border-radius:8px; text-decoration:none; font-weight:600; margin-top:16px; }}
        .warning-icon {{ font-size:40px; text-align:center; margin-bottom:12px; }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="header">
          <h1>💰 Tracksy</h1>
          <p>Your smart expense & budget manager</p>
        </div>
        <div class="body">{body_html}</div>
        <div class="footer">You're receiving this because you have budget alerts enabled on Tracksy.</div>
      </div>
    </body>
    </html>
    """


def _warning_email_html(username: str, spent: float, budget: float, month: str, percent: float) -> str:
    remaining = budget - spent
    return _base_template(f"""
        <div class="warning-icon">⚠️</div>
        <h2 style="margin:0 0 8px;color:#1f2937;">Budget Warning</h2>
        <p>Hi <strong>{username}</strong>,</p>
        <p>You're approaching your monthly budget limit for <strong>{month}</strong>.</p>
        <div class="highlight">
          <div class="amount">₹{spent:,.2f} <span style="font-size:16px;color:#6b7280;">/ ₹{budget:,.2f}</span></div>
          <p style="margin:4px 0 0;font-size:13px;color:#6b7280;">
            {percent:.1f}% used &nbsp;·&nbsp; ₹{remaining:,.2f} remaining
          </p>
        </div>
        <p>You've used <strong>{percent:.1f}%</strong> of your budget. 
           Keep an eye on your spending to avoid going over!</p>
        <p style="margin-top:24px;">Track your expenses and stay on top of your finances. 🚀</p>
    """)


def _exceeded_email_html(username: str, spent: float, budget: float, month: str, over_by: float) -> str:
    return _base_template(f"""
        <div class="warning-icon">🚨</div>
        <h2 style="margin:0 0 8px;color:#dc2626;">Budget Exceeded!</h2>
        <p>Hi <strong>{username}</strong>,</p>
        <p>You've gone over your monthly budget for <strong>{month}</strong>.</p>
        <div class="highlight" style="border-left-color:#ef4444;">
          <div class="amount" style="color:#dc2626;">₹{spent:,.2f} <span style="font-size:16px;color:#6b7280;">/ ₹{budget:,.2f}</span></div>
          <p style="margin:4px 0 0;font-size:13px;color:#dc2626;">
            Over by ₹{over_by:,.2f}
          </p>
        </div>
        <p>Don't worry — it happens! Review your recent expenses and adjust your spending 
           for the rest of the month.</p>
        <p style="margin-top:24px;font-size:13px;color:#6b7280;">
          Tip: Try our nearby affordable food spots feature to save on your next meal! 🍽️
        </p>
    """)


def _welcome_email_html(username: str) -> str:
    return _base_template(f"""
        <div class="warning-icon">🎉</div>
        <h2 style="margin:0 0 8px;color:#1f2937;">Welcome to Tracksy!</h2>
        <p>Hi <strong>{username}</strong>,</p>
        <p>Your account is all set up. Here's what you can do with Tracksy:</p>
        <ul style="padding-left:20px;color:#4b5563;">
          <li>📊 Track your daily expenses by category</li>
          <li>🎯 Set monthly & category budgets</li>
          <li>🔔 Get smart budget alerts via email</li>
          <li>📍 Find affordable food spots near you</li>
        </ul>
        <p>Start by setting your monthly budget and adding your first expense!</p>
        <p style="margin-top:24px;">Happy budgeting! 💪</p>
    """)


def _password_reset_email_html(username: str, reset_link: str) -> str:
    return _base_template(f"""
        <div class="warning-icon">🔐</div>
        <h2 style="margin:0 0 8px;color:#1f2937;">Reset Your Password</h2>
        <p>Hi <strong>{username}</strong>,</p>
        <p>We received a request to reset your Tracksy password.</p>
        <p>
          <a class="btn" href="{reset_link}" target="_blank" rel="noopener">Reset Password</a>
        </p>
        <p style="font-size:13px;color:#6b7280;margin-top:24px;">
          This link expires in 30 minutes. If you did not request this, you can ignore this email.
        </p>
    """)


# ── Core send function ────────────────────────────────────────────────────────

async def _send_email(to_email: str, subject: str, html_body: str) -> None:
    _validate_smtp_settings()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{settings.EMAILS_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html"))

    if not _AIOSMTP_AVAILABLE:
      # Fallback: environment missing aiosmtplib — skip sending but log
      print(f"[WARN] Skipping email to {to_email}: aiosmtplib not installed")
      return

    await aiosmtplib.send(
      msg,
      hostname=settings.SMTP_HOST,
      port=settings.SMTP_PORT,
      start_tls=True,
      username=settings.SMTP_USER,
      password=_smtp_password(),
    )


# ── Public API ────────────────────────────────────────────────────────────────

async def send_welcome_email(to_email: str, username: str) -> None:
    await _send_email(
        to_email,
        "Welcome to Tracksy! 🎉",
        _welcome_email_html(username),
    )


async def send_password_reset_email(to_email: str, username: str, reset_link: str) -> None:
    await _send_email(
        to_email,
        "Reset your Tracksy password",
        _password_reset_email_html(username, reset_link),
    )


async def send_budget_warning_email(
    to_email: str, username: str, spent: float, budget: float, month: str, percent: float
) -> None:
    await _send_email(
        to_email,
        f"⚠️ Budget Warning — {percent:.0f}% used for {month}",
        _warning_email_html(username, spent, budget, month, percent),
    )


async def send_budget_exceeded_email(
    to_email: str, username: str, spent: float, budget: float, month: str, over_by: float
) -> None:
    await _send_email(
        to_email,
        f"🚨 Budget Exceeded for {month} — Tracksy Alert",
        _exceeded_email_html(username, spent, budget, month, over_by),
    )
