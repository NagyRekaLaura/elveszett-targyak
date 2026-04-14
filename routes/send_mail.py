from urllib.parse import urlencode

import requests
from flask import current_app as app, url_for


def _build_reset_email_html(reset_url: str) -> str:
	return f"""
	<div style="margin:0;padding:0;background:#f3e8e0;font-family:Segoe UI,Arial,sans-serif;color:#2d1f1e;">
		<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:32px 16px;">
			<tr>
				<td align="center">
					<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px;background:#ffffff;border:1px solid #d4c5ba;border-radius:20px;overflow:hidden;box-shadow:0 18px 50px rgba(148,106,97,0.12);">
						<tr>
							<td style="padding:0;background:linear-gradient(135deg,#9E3F41 0%,#9A5A3B 45%,#946A61 100%);">
								<div style="padding:34px 36px 30px;color:#ffffff;">
									<div style="display:inline-block;padding:8px 12px;border-radius:999px;background:rgba(255,255,255,0.16);font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">
										Lost & Found
									</div>
									<h1 style="margin:18px 0 10px;font-size:30px;line-height:1.15;font-weight:800;">Jelszó visszaállitása</h1>
									<p style="margin:0;font-size:15px;line-height:1.7;max-width:520px;opacity:0.96;">
										Biztonsági okokbol kaptad ezt az emailt. Ha te kértél jelszóvisszaállitást, az alábbi gombbal új jelszót állithatsz be.
									</p>
								</div>
							</td>
						</tr>
						<tr>
							<td style="padding:36px;">
								<p style="margin:0 0 16px;font-size:16px;line-height:1.75;color:#3d2a23;">
									Ha a jelszavadat szeretnéd megváltoztatni, kattints az alábbi gombra. A link csak egy ideig érvényes, és csak egyszer hasznalható.
								</p>

								<table role="presentation" cellspacing="0" cellpadding="0" style="margin:28px 0 26px;">
									<tr>
										<td style="border-radius:14px;background:#9E3F41;">
											<a href="{reset_url}" style="display:inline-block;padding:14px 22px;font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;border-radius:14px;">
												Jelszó visszaállitása
											</a>
										</td>
									</tr>
								</table>

								<div style="background:#f9e8dc;border:1px solid #e5d5c8;border-radius:14px;padding:18px 18px 16px;margin:0 0 22px;">
									<p style="margin:0 0 8px;font-size:13px;font-weight:700;letter-spacing:0.02em;text-transform:uppercase;color:#2d1f1e;">Mit tegyél, ha nem te kérted?</p>
									<p style="margin:0;font-size:14px;line-height:1.7;color:#5a4741;">
										Ha ez a kérés nem tőled származik, egyszerűen töröld ezt az emailt. A jelszavad ekkor nem változik.
									</p>
								</div>

								<p style="margin:0 0 10px;font-size:14px;line-height:1.7;color:#6b5a4f;">
									Ha a gomb nem működik, másold be ezt a linket a böngésződbe:
								</p>
								<p style="margin:0 0 6px;word-break:break-all;font-size:13px;line-height:1.7;color:#9E3F41;">
									<a href="{reset_url}" style="color:#9E3F41;text-decoration:underline;">{reset_url}</a>
								</p>
							</td>
						</tr>
						<tr>
							<td style="padding:18px 36px 24px;border-top:1px solid #d4c5ba;background:#f5ede5;">
								<p style="margin:0;font-size:12px;line-height:1.7;color:#7a6a60;">
									Ez egy automatikusan generált email a Lost & Found rendszerből. Kerjük, ne válaszolj rá közvetlenül.
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
    