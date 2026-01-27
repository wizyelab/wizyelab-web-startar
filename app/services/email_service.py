"""
邮件服务模块

提供邮件发送功能:
- 发送验证码邮件
- 验证码生成
"""

import random
import string
from typing import Optional

from app.core.logging import setup_logger
from app.core.config import settings

logger = setup_logger(__name__)


class EmailService:
    """邮件服务类"""

    @staticmethod
    def generate_verify_code(length: int = None) -> str:
        """
        生成数字验证码

        Args:
            length: 验证码长度，默认从配置读取

        Returns:
            验证码字符串
        """
        if length is None:
            length = settings.verify_code.length
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    async def send_verify_code(email: str, code: str) -> bool:
        """
        发送验证码邮件

        Args:
            email: 收件人邮箱
            code: 验证码

        Returns:
            是否发送成功
        """
        smtp_config = settings.smtp

        # 检查SMTP配置
        if not smtp_config.user or not smtp_config.password:
            logger.warning(f"SMTP not configured, mock sending verify code {code} to {email}")
            return True  # 开发模式下假装发送成功

        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # 构建邮件
            message = MIMEMultipart("alternative")
            message["Subject"] = f"{smtp_config.from_name} 验证码: {code}"
            message["From"] = f"{smtp_config.from_name} <{smtp_config.from_email}>"
            message["To"] = email

            # 验证码有效期
            expire_minutes = settings.verify_code.expire_minutes

            # 纯文本内容
            text_content = f"""
您好！

您的验证码是: {code}

验证码有效期为{expire_minutes}分钟，请尽快使用。

如果这不是您本人的操作，请忽略此邮件。

{smtp_config.from_name} Team
            """

            # HTML内容
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">{smtp_config.from_name} 验证码</h2>
        <p>您好！</p>
        <p>您的验证码是:</p>
        <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
            {code}
        </div>
        <p>验证码有效期为{expire_minutes}分钟，请尽快使用。</p>
        <p style="color: #999; font-size: 12px;">如果这不是您本人的操作，请忽略此邮件。</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">{smtp_config.from_name} Team</p>
    </div>
</body>
</html>
            """

            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")

            message.attach(text_part)
            message.attach(html_part)

            # 发送邮件
            await aiosmtplib.send(
                message,
                hostname=smtp_config.host,
                port=smtp_config.port,
                username=smtp_config.user,
                password=smtp_config.password,
                start_tls=smtp_config.use_tls,
            )

            logger.info(f"Verification code sent to {email}")
            return True

        except ImportError:
            logger.warning("aiosmtplib not installed, mock sending email")
            return True

        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return False

    @staticmethod
    async def send_email(
        to: str, subject: str, body: str, html_body: Optional[str] = None
    ) -> bool:
        """
        发送通用邮件

        Args:
            to: 收件人邮箱
            subject: 邮件主题
            body: 纯文本内容
            html_body: HTML内容（可选）

        Returns:
            是否发送成功
        """
        smtp_config = settings.smtp

        if not smtp_config.user or not smtp_config.password:
            logger.warning(f"SMTP not configured, mock sending email to {to}")
            return True

        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{smtp_config.from_name} <{smtp_config.from_email}>"
            message["To"] = to

            text_part = MIMEText(body, "plain", "utf-8")
            message.attach(text_part)

            if html_body:
                html_part = MIMEText(html_body, "html", "utf-8")
                message.attach(html_part)

            await aiosmtplib.send(
                message,
                hostname=smtp_config.host,
                port=smtp_config.port,
                username=smtp_config.user,
                password=smtp_config.password,
                start_tls=smtp_config.use_tls,
            )

            logger.info(f"Email sent to {to}")
            return True

        except ImportError:
            logger.warning("aiosmtplib not installed")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


# 全局服务实例
email_service = EmailService()
