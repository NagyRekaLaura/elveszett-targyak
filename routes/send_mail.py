from urllib.parse import urlencode

import requests
from flask import current_app as app, url_for


def _build_reset_email_html(reset_url: str) -> str:
	return f"""
	<div style="margin:0;padding:0;background:#f3f6fb;font-family:Segoe UI,Arial,sans-serif;color:#0f172a;">
		<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:32px 16px;">
			<tr>
				<td align="center">
					<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px;background:#ffffff;border:1px solid #e5e7eb;border-radius:20px;overflow:hidden;box-shadow:0 18px 50px rgba(15,23,42,0.08);">
						<tr>
							<td style="padding:0;background:linear-gradient(135deg,#0f766e 0%,#0ea5a4 45%,#14b8a6 100%);">
								<div style="padding:34px 36px 30px;color:#ffffff;">
									<div style="display:inline-block;padding:8px 12px;border-radius:999px;background:rgba(255,255,255,0.16);font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">
										Lost & Found
									</div>
									<h1 style="margin:18px 0 10px;font-size:30px;line-height:1.15;font-weight:800;">Jelszo visszaallitasa</h1>
									<p style="margin:0;font-size:15px;line-height:1.7;max-width:520px;opacity:0.96;">
										Biztonsagi okokbol kaptad ezt az emailt. Ha te kerestel jelszovisszaallitast, az alabbi gombbal uj jelszot allithatsz be.
									</p>
								</div>
							</td>
						</tr>
						<tr>
							<td style="padding:36px;">
								<p style="margin:0 0 16px;font-size:16px;line-height:1.75;color:#1f2937;">
									Ha a jelszavadat szeretned megvaltoztatni, kattints az alabbi gombra. A link egy ideig ervenyes, es csak egyszer hasznalhato.
								</p>

								<table role="presentation" cellspacing="0" cellpadding="0" style="margin:28px 0 26px;">
									<tr>
										<td style="border-radius:14px;background:#0f766e;">
											<a href="{reset_url}" style="display:inline-block;padding:14px 22px;font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;border-radius:14px;">
												Jelszo visszaallitasa
											</a>
										</td>
									</tr>
								</table>

								<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:18px 18px 16px;margin:0 0 22px;">
									<p style="margin:0 0 8px;font-size:13px;font-weight:700;letter-spacing:0.02em;text-transform:uppercase;color:#0f172a;">Mit tegyel, ha nem te kerted?</p>
									<p style="margin:0;font-size:14px;line-height:1.7;color:#475569;">
										Ha ez a kereses nem toled szarmazik, egyszeruen torold ezt az emailt. A jelszavad ekkor sem valtozik.
									</p>
								</div>

								<p style="margin:0 0 10px;font-size:14px;line-height:1.7;color:#64748b;">
									Ha a gomb nem mukodik, masold be ezt a linket a bongeszobe:
								</p>
								<p style="margin:0 0 6px;word-break:break-all;font-size:13px;line-height:1.7;color:#0f766e;">
									<a href="{reset_url}" style="color:#0f766e;text-decoration:underline;">{reset_url}</a>
								</p>
							</td>
						</tr>
						<tr>
							<td style="padding:18px 36px 24px;border-top:1px solid #e5e7eb;background:#fafafa;">
								<p style="margin:0;font-size:12px;line-height:1.7;color:#64748b;">
									Ez egy automatikusan generalt email a Lost & Found rendszerbol. Kerjuk, ne valaszolj ra kozvetlenul.
								</p>
							</td>
						</tr>
					</table>
				</td>
			</tr>
		</table>
	</div>
	"""


def send_password_reset_email(user_email, reset_token):
	reset_path = url_for("auth.reset_password", _external=True)
	reset_url = f"{reset_path}?{urlencode({'token': reset_token})}"

	subject = "Lost & Found - Jelszo visszaallitasa"
	text_body = (
		"Szia!\n\n"
		"Jelszovisszaallitast kertel a Lost & Found rendszerben.\n"
		"Az uj jelszo beallitasahoz nyisd meg az alabbi linket:\n\n"
		f"{reset_url}\n\n"
		"Ha nem te kerted ezt, egyszeruen torold az emailt.\n\n"
		"Udvozlettel,\n"
		"A Lost & Found csapata"
	)
	html_body = _build_reset_email_html(reset_url)

	mailgun_domain = app.config.get("MAILGUN_DOMAIN", "chronarch.eu")
	mailgun_api_key = app.config.get("MAILGUN_API_KEY")
	from_email = app.config.get("MAILGUN_FROM_EMAIL", f"Lost & Found <mail@{mailgun_domain}>")

	if not mailgun_api_key:
		raise ValueError("MAILGUN_API_KEY nincs beallitva.")

	response = requests.post(
		f"https://api.eu.mailgun.net/v3/{mailgun_domain}/messages",
		auth=("api", mailgun_api_key),
		data={
			"from": from_email,
			"to": user_email,
			"subject": subject,
			"text": text_body,
			"html": html_body,
		},
		timeout=20,
	)
	response.raise_for_status()
	return response
    